from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from translator import translate

TOKEN = "YOUR_BOT_TOKEN"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    # phát hiện tiếng
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        result = translate(text, "vi")
    else:
        result = translate(text, "zh-CN")

    await update.message.reply_text(result)


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Bot đang chạy...")

    app.run_polling()


if __name__ == "__main__":
    main()
