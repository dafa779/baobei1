from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from translator import translate_to_vi, translate_to_zh

TOKEN = "YOUR_BOT_TOKEN"


def is_chinese(text):
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    try:

        # Nếu là tiếng Trung → dịch sang Việt
        if is_chinese(text):

            translated = translate_to_vi(text)

            if translated != text:
                await update.message.reply_text(f"🇻🇳 {translated}")

        # Nếu là tiếng Việt → dịch sang Trung
        else:

            translated = translate_to_zh(text)

            if translated != text:
                await update.message.reply_text(f"🇨🇳 {translated}")

    except Exception as e:
        print("Translation error:", e)


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Bot Translator Running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
