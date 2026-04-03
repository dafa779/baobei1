from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from deep_translator import GoogleTranslator

TOKEN = "8708366814:AAEDC1i8gN01IRkbA7C1UcMvwckmlgd_r6E"


def translate_text(text):
    try:
        return GoogleTranslator(source='zh-CN', target='vi').translate(text)
    except:
        try:
            return GoogleTranslator(source='vi', target='zh-CN').translate(text)
        except:
            return "❌ Không dịch được"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot dịch Trung ⇄ Việt\n"
        "Gửi tin nhắn để dịch 🇨🇳🇻🇳"
    )


async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    result = translate_text(text)

    await update.message.reply_text(result)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))

    print("Bot đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()
