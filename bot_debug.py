import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= VARIÁVEIS =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = "https://botmoto-production.up.railway.app"
PORT = int(os.environ.get("PORT", 8080))

print("=" * 50)
print("🤖 BOT DEBUG - INICIANDO")
print("=" * 50)
print(f"APP_URL: {APP_URL}")
print(f"BOT_TOKEN: {BOT_TOKEN[:10] + '...' if BOT_TOKEN else 'NÃO ENCONTRADO!'}")
print(f"PORT: {PORT}")

if not BOT_TOKEN:
    print("❌ ERRO: BOT_TOKEN não encontrado!")
    exit(1)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    await update.message.reply_text(
        f"✅ **Bot Debug - ATIVO!**\n\n"
        f"👤 Seu ID: `{chat_id}`\n"
        f"📛 Nome: {user.first_name}\n"
        f"🔗 User: @{user.username if user.username else 'N/A'}\n\n"
        f"Use /meuid para ver apenas o ID",
        parse_mode='Markdown'
    )
    print(f"✅ /start recebido de {user.first_name} (ID: {chat_id})")

async def meuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🆔 Seu chat_id é: `{chat_id}`", parse_mode='Markdown')
    print(f"✅ /meuid recebido de {chat_id}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 **Status do Bot**\n\n"
        f"✅ Online e funcionando!\n"
        f"🌐 URL: {APP_URL}\n"
        f"🔧 Porta: {PORT}",
        parse_mode='Markdown'
    )

# ================= CONFIGURAÇÃO PRINCIPAL =================
def main():
    print("🚀 Criando aplicação...")
    
    # Criar aplicação
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Adicionar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("meuid", meuid))
    application.add_handler(CommandHandler("status", status))
    
    # Configurar webhook
    webhook_url = f"{APP_URL}/{BOT_TOKEN}"
    print(f"🌐 Webhook URL: {webhook_url}")
    print("🔄 Iniciando webhook...")
    
    try:
        # Iniciar webhook
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_url,
            url_path=BOT_TOKEN,  # Importante para a versão 20.5
            drop_pending_updates=True
        )
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        print("🔄 Tentando polling...")
        application.run_polling()

if __name__ == "__main__":
    main()
