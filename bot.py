import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

TOKEN = os.getenv("TOKEN")

# start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot dịch Trung ↔ Việt\n\n"
        "Gửi tiếng Trung -> bot dịch sang Việt\n"
        "Gửi tiếng Việt -> bot dịch sang Trung"
    )

# detect translate
def translate_text(text):
    try:
        # thử dịch sang việt
        vi = GoogleTranslator(source='zh-CN', target='vi').translate(text)

        # nếu khác text gốc -> nghĩa là tiếng Trung
        if vi != text:
            return f"🇻🇳 {vi}"

        # nếu giống -> dịch sang trung
        zh = GoogleTranslator(source='vi', target='zh-CN').translate(text)
        return f"🇨🇳 {zh}"

    except:
        return "❌ Lỗi dịch"

# message handler
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    result = translate_text(text)
    await update.message.reply_text(result)

# main
def main():

    if not TOKEN:
        print("YOUR_TOKEN")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate))

    print("✅ Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()
