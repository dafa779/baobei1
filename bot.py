import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator

TOKEN = os.getenv("TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot dịch đã hoạt động!\nGửi tin nhắn để dịch sang tiếng Việt.")


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        translated = GoogleTranslator(source='auto', target='vi').translate(text)
        await update.message.reply_text(translated)
    except Exception as e:
        await update.message.reply_text("❌ Lỗi dịch: " + str(e))


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))

    print("Bot đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()
