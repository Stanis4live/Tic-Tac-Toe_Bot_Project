from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.models import Player, Game
from bot.config import bot, application
from bot.utils import get_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if query.data == "play_with_bot":
        game = Game.objects.create(is_active=True, against_bot=True)
        game.assign_players(player)
        await query.message.reply_text(
            f"You are playing against a bot. Player X turn.",
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

    if query.data == "create_game":
        game = Game.objects.create(is_active=True)
        await query.message.reply_text(
            f"The game has been created. Player share this key with another player to connect: {game.game_key}."
        )
    elif query.data == "join_game":
        await query.message.reply_text("Please enter the game key to join:")
        context.user_data['awaiting_game_key'] = True



@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        update = Update.de_json(request.json(), bot)
        application.update_queue.put_nowait(update)
    return JsonResponse({'status': 'ok'})


