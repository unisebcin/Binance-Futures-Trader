from telegram import Update  # python-telegram-bot version 20.0
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
# import config
# import pandas as pd

token = "5794773301:AAHXDVijv7DqsTyEvWeiQ9vEugg8MRMunZQ"


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if '@Cointrader200bot' in update.message.text:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{update.message.text} : '
                                                                              f'I can hear you well')


def telegram_listener():
    application = ApplicationBuilder().token(token).build()

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)

    application.add_handler(echo_handler)

    application.run_polling()
