import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Bot, Update
from telegram.ext import Application, ContextTypes, CommandHandler


TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(TOKEN)
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to TicTacToe game Bot!")

application.add_handler(CommandHandler("start", start))


@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        update = Update.de_json(request.json(), bot)
        application.update_queue.put_nowait(update)
    return JsonResponse({'status': 'ok'})


