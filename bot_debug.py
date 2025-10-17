import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests

# ================= VARIÁVEIS =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
# REMOVER O TOKEN DA APP_URL - deve ser apenas a URL base
APP_URL = "https://botmoto-production.up.railway.app"  # URL FIXA sem o token
PORT = int(os.environ.get("PORT", 8080))

print("=" * 50)
print("🤖 BOT DEBUG - INICIANDO")
print("=" * 50)

# ================= VERIFICAÇÃO DE VARIÁVEIS =================
print("🔍 Verificando variáveis de ambiente...")
print(f"APP_URL: {APP_URL}")
print(f"BOT_TOKEN: {BOT_TOKEN[:10] + '...' if BOT_TOKEN else 'NÃO ENCONTRADO!'}")
print(f"PORT: {PORT}")

if not BOT_TOKEN:
    print("❌ ERRO: BOT_TOKEN não encontrado!")
    exit(1)

# ================= TESTE DE CONEXÃO COM TELEGRAM =================
print("\n📡 Testando conexão com Telegram...")
try:
    test_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    response = requests.get(test_url, timeout=10)
    bot_info = response.json()
    
    if bot_info.get("ok"):
        print(f"✅ Conexão OK! Bot: @{bot_info['result']['username']}")
    else:
        print(f"❌ Erro no Telegram: {bot_info}")
        exit(1)
        
except Exception as e:
    print(f"❌ Falha na conexão: {e}")
    exit(1)

# ================= LIMPAR WEBHOOK ANTIGO =================
print("\n🔄 Limpando webhook antigo...")
try:
    resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    print(f"✅ Webhook antigo removido: {resp.json()}")
except Exception as e:
    print(f"⚠️ Erro ao remover webhook: {e}")

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
    print("\n🚀 Iniciando aplicação...")
    
    # Criar aplicação
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Adicionar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("meuid", meuid))
    application.add_handler(CommandHandler("status", status))
    
    # Configurar webhook - URL CORRETA
    webhook_url = f"{APP_URL.rstrip('/')}/{BOT_TOKEN}"
    print(f"🌐 Configurando webhook: {webhook_url}")
    
    try:
        # Configurar e rodar webhook (approach síncrono para evitar problemas de event loop)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_url,
            key=None,
            cert=None,
            secret_token=None,
            drop_pending_updates=True
        )
        
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        print("🔄 Tentando polling como fallback...")
        try:
            application.run_polling()
        except Exception as poll_error:
            print(f"❌ Erro no polling também: {poll_error}")

# ================= EXECUÇÃO =================
if __name__ == "__main__":
    print("🟢 Iniciando bot...")
    main()
