import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from translator import translate

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text

    try:
        result = translate(text)
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text("Lỗi dịch 😢")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle)
    )

    print("AI Translator Bot running 🚀")

    app.run_polling()

if __name__ == "__main__":
    main()
