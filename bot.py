from telegram import Update
from telegram.ext import ApplicationBuilder,MessageHandler,filters,ContextTypes
from translator import translate
from config import TELEGRAM_TOKEN

async def handle(update:Update,context:ContextTypes.DEFAULT_TYPE):

    text=update.message.text

    result=translate(text)

    await update.message.reply_text(result)

app=ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT,handle))

print("AI Translator Bot running")

app.run_polling()
