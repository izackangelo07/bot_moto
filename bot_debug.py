import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# ================= VARIÁVEIS =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")  # ex: https://botmoto-production.up.railway.app
PORT = int(os.environ.get("PORT", 8080))

print("✅ Iniciando Bot de Debug...")
print("APP_URL:", APP_URL)
print("BOT_TOKEN:", BOT_TOKEN[:5] + "...")
print("PORT:", PORT)

# ================= LIMPAR WEBHOOK ANTIGO =================
try:
    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    print("❌ Webhook antigo removido:", resp.text)
except Exception as e:
    print("⚠️ Erro ao remover webhook antigo:", e)

# ================= HANDLERS =================
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

# ================= APPLICATION =================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("meuid", meu_id))

# ================= REGISTRAR WEBHOOK =================
try:
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{APP_URL}/{BOT_TOKEN}"
    )
    print(f"✅ Webhook registrado em: {APP_URL}/{BOT_TOKEN}")
except Exception as e:
    print("❌ Erro ao registrar webhook:", e)

# ================= TESTE DE ACESSO =================
try:
    test = requests.get(f"{APP_URL}/{BOT_TOKEN}")
    print("🌐 Teste de acesso ao webhook:", test.status_code, test.reason)
except Exception as e:
    print("⚠️ Erro ao testar acesso:", e)

# ================= MANTER CONTAINER ATIVO =================
asyncio.get_event_loop().run_forever()
