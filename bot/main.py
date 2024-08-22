import os, sys
import telebot
import logging
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TicTacToeBot.settings')
django.setup()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.models import Player, Game
from bot.utils import get_keyboard, check_winner, deactivate_other_games

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

TOKEN = '7421914146:AAHKaKWoyhIkQPakzIH_7MNp8hDiLFfKbUg'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("3x3", callback_data="size_3"),
        telebot.types.InlineKeyboardButton("4x4", callback_data="size_4"),
        telebot.types.InlineKeyboardButton("5x5", callback_data="size_5")
    )
    bot.send_message(message.chat.id, "Choose the board size:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('size_'))
def choose_board_size(call):
    board_size = int(call.data.split('_')[1])
    bot.answer_callback_query(call.id)

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("Play with bot", callback_data=f"play_with_bot_{board_size}"),
        telebot.types.InlineKeyboardButton("Play with human", callback_data=f"play_with_human_{board_size}"),
    )
    bot.send_message(call.message.chat.id, "Choose a game mode:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('play_with_'))
def progress_game_mode(call):
    mode, board_size = call.data.split('_')[2], int(call.data.split('_')[3])
    user_id = call.from_user.id
    username = call.from_user.username

    if mode == "bot":
        create_game(call.message, board_size, against_bot=True, user_id=user_id, username=username)
    elif mode == "human":
        choose_create_or_join(call.message, board_size)


def choose_create_or_join(message, board_size):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(
        telebot.types.InlineKeyboardButton("Create game", callback_data=f"create_game_{board_size}"),
        telebot.types.InlineKeyboardButton("Join game", callback_data=f"join_game_{board_size}"),
    )
    bot.send_message(message.chat.id, "Choose an option:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('create_game_'))
def create_game_handler(call):
    board_size = int(call.data.split('_')[2])
    user_id = call.from_user.id
    username = call.from_user.username
    create_game(call.message, board_size, against_bot=False, user_id=user_id, username=username)


def create_game(message, board_size, against_bot, user_id, username):
    player, _ = Player.objects.get_or_create(user_id=user_id, defaults={'username': username})

    deactivate_other_games(player)

    board_default = ' ' * (board_size ** 2)
    game = Game.objects.create(
        player_x=player,
        is_active=True,
        against_bot=against_bot,
        board_size=board_size,
        board=board_default
    )

    if against_bot:
        game.assign_players(player)
        bot.send_message(message.chat.id,
                         f"You are playing against a bot on a {board_size}x{board_size} board. Player X turn.")
    else:
        bot.send_message(message.chat.id,
                         f"The game has been created with a {board_size}x{board_size} board. Share this key with another player to connect: \n{game.game_key}")
        bot.register_next_step_handler(message, process_game_key)


@bot.callback_query_handler(func=lambda call: call.data.startswith('join_game_'))
def join_game_handler(call):
    bot.send_message(call.message.chat.id, "Please enter the game key to join:")
    bot.register_next_step_handler(call.message, process_game_key)


def process_game_key(message):
    game_key = message.text.strip()
    try:
        game = Game.objects.get(game_key=game_key, is_active=True)
        if not game.player_o:
            user_id = message.from_user.id
            username = message.from_user.username

            player, _ = Player.objects.get_or_create(user_id=user_id, defaults={'username': username})

            deactivate_other_games(player)

            game.assign_players(game.player_x, player)

            bot.send_message(game.player_x.user_id, "You are playing as X. Your move.", reply_markup=get_keyboard(game))
            bot.send_message(game.player_o.user_id, "You are playing as O. Waiting for X to move.")
        else:
            bot.send_message(message.chat.id, "This game already has two players.")
    except Game.DoesNotExist:
        bot.send_message(message.chat.id, "Game with this key does not exist.")



@bot.callback_query_handler(func=lambda call: call.data.isdigit())
def handle_move(call):
    user_id = call.from_user.id
    player = Player.objects.get(user_id=user_id)

    game = (Game.objects.filter(is_active=True, player_x=player).first()
            or Game.objects.filter(is_active=True, player_o=player).first())

    if not game or game.current_turn != player:
        bot.answer_callback_query(call.id, "It's not your turn.")
        return

    move = int(call.data)
    if game.board[move] == ' ':
        new_board = list(game.board)
        new_board[move] = 'X' if player == game.player_x else 'O'
        game.board = ''.join(new_board)

    winner = check_winner(game.board, game.board_size)
    if winner:
        game.is_active = False
        game.save()
        bot.send_message(game.player_x.user_id, f"Game over! {winner} wins!")
        bot.send_message(game.player_o.user_id, f"Game over! {winner} wins!")
    elif ' ' not in game.board:
        game.is_active = False
        game.save()
        bot.send_message(call.message.chat.id, f"It's a draw!")
    else:
        if game.current_turn == game.player_x:
            game.current_turn = game.player_o
        else:
            game.current_turn = game.player_x
        game.save()
        bot.edit_message_text(text="Next move", chat_id=call.message.chat.id, message_id=call.message.message_id,
                              reply_markup=get_keyboard(game))
        bot.send_message(game.current_turn.user_id, f"Your move.", reply_markup=get_keyboard(game))
        bot.send_message(game.player_x.user_id if game.current_turn == game.player_o else game.player_o.user_id,
                         "Waiting for opponent's move.")


if __name__ == '__main__':
    while True:
        try:
            logging.info("Polling started")
            bot.polling()
        except Exception as e:
            logger.error(f"Polling error: {e}")