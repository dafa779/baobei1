import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from deep_translator import GoogleTranslator

TOKEN = os.getenv("TOKEN")

keyboard = [
    ["🇻🇳 Việt → Trung", "🇨🇳 Trung → Việt"]
]

markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🤖 BOT DỊCH TRUNG - VIỆT

Gửi tin nhắn để dịch tự động

Lệnh:
/trung <text>  → Việt sang Trung
/viet <text>   → Trung sang Việt

Ví dụ:
/trung Xin chào
/viet 你好
"""

    await update.message.reply_text(text, reply_markup=markup)


# Việt → Trung
async def viet_trung(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = " ".join(context.args)

    if not text:
        await update.message.reply_text("❌ Ví dụ: /trung Xin chào")
        return

    try:
        result = GoogleTranslator(source="vi", target="zh-CN").translate(text)
        await update.message.reply_text(f"🇨🇳 {result}")
    except:
        await update.message.reply_text("❌ Lỗi dịch")


# Trung → Việt
async def trung_viet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = " ".join(context.args)

    if not text:
        await update.message.reply_text("❌ Ví dụ: /viet 你好")
        return

    try:
        result = GoogleTranslator(source="zh-CN", target="vi").translate(text)
        await update.message.reply_text(f"🇻🇳 {result}")
    except:
        await update.message.reply_text("❌ Lỗi dịch")


# Auto dịch
async def auto_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    try:

        if text == "🇻🇳 Việt → Trung":
            context.user_data["mode"] = "vi_zh"
            await update.message.reply_text("✍️ Gửi tiếng Việt để dịch sang Trung")
            return

        if text == "🇨🇳 Trung → Việt":
            context.user_data["mode"] = "zh_vi"
            await update.message.reply_text("✍️ Gửi tiếng Trung để dịch sang Việt")
            return

        mode = context.user_data.get("mode")

        if mode == "vi_zh":
            result = GoogleTranslator(source="vi", target="zh-CN").translate(text)
            await update.message.reply_text(f"🇨🇳 {result}")
            return

        if mode == "zh_vi":
            result = GoogleTranslator(source="zh-CN", target="vi").translate(text)
            await update.message.reply_text(f"🇻🇳 {result}")
            return

        # auto detect
        vi = GoogleTranslator(source="auto", target="vi").translate(text)

        if vi.lower() == text.lower():
            zh = GoogleTranslator(source="auto", target="zh-CN").translate(text)
            await update.message.reply_text(f"🇨🇳 {zh}")
        else:
            await update.message.reply_text(f"🇻🇳 {vi}")

    except:
        await update.message.reply_text("❌ Không dịch được")


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trung", viet_trung))
    app.add_handler(CommandHandler("viet", trung_viet))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_translate))

    print("BOT ĐANG CHẠY...")

    app.run_polling()


if __name__ == "__main__":
    main()
