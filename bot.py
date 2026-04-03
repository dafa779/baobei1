import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TOKEN
from translator import translate_vi_to_zh, translate_zh_to_vi, auto_translate

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

keyboard = [
    ["🇻🇳 Việt → Trung", "🇨🇳 Trung → Việt"],
    ["🌐 Auto dịch"]
]

markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    msg = """
🤖 BOT DỊCH TRUNG ⇄ VIỆT

Chức năng:
🇻🇳 Việt → Trung  
🇨🇳 Trung → Việt  
🌐 Auto nhận dạng

Lệnh:
/trung <text>
/viet <text>

Ví dụ:
/trung Xin chào
/viet 你好
"""

    await update.message.reply_text(msg, reply_markup=markup)


async def cmd_trung(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = " ".join(context.args)

    if not text:
        await update.message.reply_text("❌ Ví dụ: /trung Xin chào")
        return

    result = translate_vi_to_zh(text)

    await update.message.reply_text(f"🇨🇳 {result}")


async def cmd_viet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = " ".join(context.args)

    if not text:
        await update.message.reply_text("❌ Ví dụ: /viet 你好")
        return

    result = translate_zh_to_vi(text)

    await update.message.reply_text(f"🇻🇳 {result}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "🇻🇳 Việt → Trung":
        context.user_data["mode"] = "vi_zh"
        await update.message.reply_text("✍️ Gửi tiếng Việt cần dịch")
        return

    if text == "🇨🇳 Trung → Việt":
        context.user_data["mode"] = "zh_vi"
        await update.message.reply_text("✍️ Gửi tiếng Trung cần dịch")
        return

    if text == "🌐 Auto dịch":
        context.user_data["mode"] = "auto"
        await update.message.reply_text("✍️ Gửi nội dung để bot tự nhận dạng")
        return

    mode = context.user_data.get("mode", "auto")

    if mode == "vi_zh":
        result = translate_vi_to_zh(text)
        await update.message.reply_text(f"🇨🇳 {result}")
        return

    if mode == "zh_vi":
        result = translate_zh_to_vi(text)
        await update.message.reply_text(f"🇻🇳 {result}")
        return

    result = auto_translate(text)
    await update.message.reply_text(result)


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trung", cmd_trung))
    app.add_handler(CommandHandler("viet", cmd_viet))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot đang chạy...")

    app.run_polling()


if __name__ == "__main__":
    main()
