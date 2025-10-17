import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")  # https://botmoto-production.up.railway.app

print("✅ Iniciando Bot de Teste...")
print("APP_URL:", APP_URL)
print("BOT_TOKEN:", BOT_TOKEN[:5] + "...")

# Limpar webhook antigo
delete_wh = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
print("❌ Webhook antigo removido:", delete_wh.text)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ Bot ativo!\nSeu chat_id é: {update.effective_chat.id}"
    )
    print("✅ /start recebido de", update.effective_chat.id)

# Application
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))

# Rodar como webhook
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
    url_path=BOT_TOKEN,
    webhook_url=f"{APP_URL}/{BOT_TOKEN}"
)

print(f"✅ Webhook registrado em: {APP_URL}/{BOT_TOKEN}")

# Mantém o container ativo
asyncio.get_event_loop().run_forever()
