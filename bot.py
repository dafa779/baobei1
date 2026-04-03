from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from translator import translate

TOKEN = "YOUR_BOT_TOKEN"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        vi = translate(text, "vi")
        zh = translate(text, "zh-CN")

        if text != vi:
            await update.message.reply_text("🇻🇳 " + vi)

        if text != zh:
            await update.message.reply_text("🇨🇳 " + zh)

    except Exception as e:
        print(e)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling(drop_pending_updates=True)
