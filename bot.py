from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator

TOKEN = "YOUR_BOT_TOKEN"


def translate_text(text):
    try:
        return GoogleTranslator(source='zh-CN', target='vi').translate(text)
    except:
        try:
            return GoogleTranslator(source='vi', target='zh-CN').translate(text)
        except:
            return "Không dịch được"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot dịch Trung ⇄ Việt\n\n"
        "Gửi tin nhắn để dịch 🇨🇳🇻🇳"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    result = translate_text(text)

    await update.message.reply_text(result)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()
