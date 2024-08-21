from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from bot.models import Player, Game
from bot.config import bot, application
from bot.utils import get_keyboard, check_winner


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("3ч3", callback_data="size_3")],
        [InlineKeyboardButton("4ч4", callback_data="size_4")],
        [InlineKeyboardButton("5ч5", callback_data="size_5")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the board size:", reply_markup=reply_markup)


async def choose_board_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    board_size = int(query.data.split('_')[1])
    context.user_data['board_size'] = board_size

    keyboard = [
        [InlineKeyboardButton("Play with bot", callback_data="play_with_bot")],
        [InlineKeyboardButton("Play with human", callback_data="play_with_human")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a game mode:", reply_markup=reply_markup)


async def choose_game_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username
    player, _ = Player.objects.get_or_create(user_id=user_id, defaults={'username': username})

    board_size = context.user_data.get('board_size', 3)
    board_default = ' ' * (board_size ** 2)

    if query.data == "play_with_bot":
        game = Game.objects.create(
            player_x=player,
            is_active=True,
            against_bot=True,
            board_size=board_size,
            board=board_default
        )
        game.assign_players(player)
        await query.message.reply_text(
            f"You are playing against a bot on a {board_size}x{board_size} board. Player X turn.",
            reply_markup=get_keyboard(game)
        )
    elif query.data == "play_with_human":
        keyboard = [
            [InlineKeyboardButton("Create a new game", callback_data="create_game"), ],
            [InlineKeyboardButton("Join game", callback_data="join_game")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Do you want to create a new game or join an existing one:",
            reply_markup=reply_markup
        )

async def create_or_join_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    username = query.from_user.username
    player, _ = Player.objects.get_or_create(user_id=user_id, defaults={'username': username})

    board_size = context.user_data.get('board_size', 3)
    board_default = ' ' * (board_size ** 2)

    if query.data == "create_game":
        game = Game.objects.create(player_x=player, is_active=True, board_size=board_size, board=board_default)
        await query.message.reply_text(
            f"The game has been created with a {board_size}x{board_size} board. Share this key with another player to connect: {game.game_key}."
        )
    elif query.data == "join_game":
        await query.message.reply_text("Please enter the game key to join:")
        context.user_data['awaiting_game_key'] = True

async def handle_join_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('awaiting_game_key'):
        user_id = update.effective_user.id
        username = update.effective_user.username
        player, _ = Player.objects.get_or_create(user_id=user_id, defaults={'username': username})

        game_key = update.message.text
        try:
            game = Game.objects.get(game_key=game_key, is_active=True)
            if not game.player_o:
                game.assign_players(game.player_x, player)
                await update.message.reply_text(
                    "You joined the game. Player X turn.",
                    reply_markup=get_keyboard(game)
                )
            else:
                await update.message.reply_text("This game is already has two players.")
        except Game.DoesNotExist:
            await update.message.reply_text("Game with this key does not exist.")
        finally:
            context.user_data['awaiting_game_key'] = False


async def handle_move(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    player = Player.objects.get(user_id=user_id)

    game = (Game.objects.filter(is_active=True, player_x=player).first()
            or Game.objects.filter(is_active=True, player_o=player).first())

    if not game or game.current_turn != player:
        await query.answer("It's not your turn.")
        return

    move = int(query.data)
    if game.board[move] == ' ':
        new_board = list(game.board)
        new_board[move] = 'X' if player == game.player_x else 'O'
        game.board = ''.join(new_board)

    winner = check_winner(game.board, game.board_size)
    if winner:
        game.is_active = False
        game.save()
        await query.message.reply_text(f"Game over! {winner} wins!")
    elif ' ' not in game.board:
        game.is_active = False
        game.save()
        await query.message.reply_text(f"It's a draw!")
    else:
        game.current_turn = game.player_o if game.current_turn == game.player_x else game.player_x
        game.save()
        await query.message.reply_text(text="Next move", reply_markup=get_keyboard(game))



@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        update = Update.de_json(request.json(), bot)
        application.update_queue.put_nowait(update)
    return JsonResponse({'status': 'ok'})


application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(choose_board_size, pattern='^size_'))
application.add_handler(CallbackQueryHandler(choose_game_mode, pattern='^(play_with_bot|play_with_human)$'))
application.add_handler(CallbackQueryHandler(create_or_join_game, pattern='^(create_game|join_game)$'))
application.add_handler(CallbackQueryHandler(handle_move))
application.add_handler(CommandHandler("join_game", handle_join_game))
