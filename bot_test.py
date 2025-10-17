import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# ========== VARIÁVEIS DE AMBIENTE ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")  # ex: https://botmoto-production.up.railway.app

print("✅ Iniciando Bot de Teste...")
print("APP_URL:", APP_URL)
print("BOT_TOKEN:", BOT_TOKEN[:5] + "...")

# ========== LIMPAR WEBHOOK ANTIGO ==========
delete_wh = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
print("❌ Webhook antigo removido:", delete_wh.text)

# ========== HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"✅ Bot ativo!\nSeu chat_id é: {chat_id}"
    )
    print("✅ /start recebido de", chat_id)

async def meu_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"✅ Seu chat_id é: {chat_id}")
    print("✅ /meuid recebido de", chat_id)

# ========== APPLICATION ==========
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("meuid", meu_id))

# ========== RODAR COMO WEBHOOK ==========
app.run_webhook(
    listen="0.0.0.0",
    port=int(os.environ.get("PORT", 8000)),
    url_path=BOT_TOKEN,
    webhook_url=f"{APP_URL}/{BOT_TOKEN}"
)

print(f"✅ Webhook registrado em: {APP_URL}/{BOT_TOKEN}")

# ========== MANTER CONTAINER ATIVO ==========
asyncio.get_event_loop().run_forever()
