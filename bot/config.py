import os
from telegram import Bot, Update
from telegram.ext import Application, ContextTypes, CommandHandler


TOKEN = '7421914146:AAHKaKWoyhIkQPakzIH_7MNp8hDiLFfKbUg'
bot = Bot(TOKEN)
application = Application.builder().token(TOKEN).connect_timeout(60).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome to TicTacToe game Bot!")

application.add_handler(CommandHandler("start", start))


if __name__ == '__main__':
    application.run_polling()