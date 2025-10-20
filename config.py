import os

print("🚀 BOT MANUTENÇÃO - POPzinha - CONFIGURAÇÃO")

# Configurações das variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
PORT = int(os.environ.get("PORT", 8080))
DELETE_PASSWORD = os.getenv("DELETE_PASSWORD", "123456")
NOTIFICATION_CHAT_ID = os.getenv("NOTIFICATION_CHAT_ID")

# Limpar URL do Gist se fornecida como URL completa
if GIST_ID and "github.com" in GIST_ID:
    GIST_ID = GIST_ID.split("/")[-1]

# Log das configurações (ocultando informações sensíveis)
print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"✅ GitHub Token: {GITHUB_TOKEN[:10]}..." if GITHUB_TOKEN else "❌ GitHub Token")
print(f"✅ Gist ID: {GIST_ID}" if GIST_ID else "❌ Gist ID")
print(f"✅ Delete Password: {DELETE_PASSWORD[:2]}..." if DELETE_PASSWORD else "❌ Delete Password")
print(f"✅ Notification Chat ID: {NOTIFICATION_CHAT_ID}" if NOTIFICATION_CHAT_ID else "❌ Notification Chat ID")
