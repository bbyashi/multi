from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working!")

app = ApplicationBuilder().token("8388314171:AAFXrRKZU0d7XMRP5sRNi89ixXXzYGo0_Ws").build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
