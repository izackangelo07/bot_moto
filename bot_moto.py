import os
from telegram.ext import ApplicationBuilder, CommandHandler

print("🚀 BOT SIMPLES INICIANDO...")

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

async def start(update, context):
    await update.message.reply_text("✅ Bot funcionando via WEBHOOK!")

async def meuid(update, context):
    await update.message.reply_text(f"🆔 {update.effective_chat.id}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("meuid", meuid))

print("🌐 Iniciando webhook...")
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=f"https://botmoto-production.up.railway.app/{BOT_TOKEN}",
    url_path=BOT_TOKEN
)
