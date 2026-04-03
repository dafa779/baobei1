import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from translator import translate

TOKEN = os.getenv("TOKEN")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # dịch Trung -> Việt
    vi = translate(text, "vi")

    # dịch Việt -> Trung
    zh = translate(text, "zh-CN")

    reply = f"""
📥 Gốc:
{text}

🇻🇳 Việt:
{vi}

🇨🇳 中文:
{zh}
"""

    await update.message.reply_text(reply)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot đang chạy...")
    app.run_polling()


if __name__ == "__main__":
    main()
