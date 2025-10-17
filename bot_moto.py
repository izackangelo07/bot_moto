import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import requests

print("🚀 BOT MOTOMANUTENÇÃO INICIANDO...")

# ========== CONFIGURAÇÃO ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = "https://botmoto-production.up.railway.app"
PORT = int(os.environ.get("PORT", 8080))
DRIVE_FILENAME = "moto_data.json"

print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"🌐 URL: {APP_URL}")
print(f"🔧 Porta: {PORT}")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN não encontrado!")
    exit(1)

# ========== ARQUIVO LOCAL (SOLUÇÃO TEMPORÁRIA) ==========
DATA_FILE = "/tmp/moto_data.json"

def download_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"km": [], "fuel": [], "maintenance": []}

def upload_data(data):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("✅ Dados salvos localmente")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")

# ========== HANDLERS ==========
def format_date():
    now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    return f"{now.day:02}/{now.month:02} {now.hour:02}:{now.minute:02}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"✅ /start de {chat_id}")
    await update.message.reply_text(
        "🏍️ *BOT MOTOMANUTENÇÃO*\n\n"
        "📋 Comandos:\n"
        "• `/addkm 15000`\n"
        "• `/fuel 10 5.50`\n" 
        "• `/maint Troca de óleo`\n"
        "• `/report`\n"
        "• `/del km 1`",
        parse_mode="Markdown"
    )

async def add_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        km_value = int(context.args[0])
        data = download_data()
        data["km"].append({"date": format_date(), "km": km_value})
        upload_data(data)
        await update.message.reply_text(f"✅ KM registrado: {km_value} km")
    except:
        await update.message.reply_text("❌ Use: `/addkm 15000`", parse_mode="Markdown")

async def add_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        liters = float(context.args[0])
        price = float(context.args[1])
        data = download_data()
        data["fuel"].append({"date": format_date(), "liters": liters, "price": price})
        upload_data(data)
        await update.message.reply_text(f"⛽ Abastecimento: {liters}L a R$ {price:.2f}")
    except:
        await update.message.reply_text("❌ Use: `/fuel 10 5.50`", parse_mode="Markdown")

async def add_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        desc = " ".join(context.args)
        data = download_data()
        data["maintenance"].append({"date": format_date(), "desc": desc})
        upload_data(data)
        await update.message.reply_text(f"🧰 Manutenção: {desc}")
    except:
        await update.message.reply_text("❌ Use: `/maint Troca de óleo`", parse_mode="Markdown")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = download_data()
    msg = "🏍️ *RELATÓRIO DA MOTO*\n\n"
    
    # KM
    msg += "📏 *QUILOMETRAGEM:*\n"
    if data["km"]:
        for i, d in enumerate(data["km"][-10:]):
            msg += f"`{i+1:2d}.` {d['date']} — {d['km']} km\n"
    else:
        msg += "📭 Nenhum registro\n"
    
    # Combustível
    msg += "\n⛽ *ABASTECIMENTOS:*\n"
    if data["fuel"]:
        for i, d in enumerate(data["fuel"][-10:]):
            msg += f"`{i+1:2d}.` {d['date']} — {d['liters']}L × R$ {d['price']:.2f}\n"
    else:
        msg += "📭 Nenhum registro\n"
    
    # Manutenção
    msg += "\n🧰 *MANUTENÇÕES:*\n"
    if data["maintenance"]:
        for i, d in enumerate(data["maintenance"][-10:]):
            msg += f"`{i+1:2d}.` {d['date']} — {d['desc']}\n"
    else:
        msg += "📭 Nenhum registro\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def delete_record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tipo = context.args[0]
        index = int(context.args[1]) - 1
        
        if tipo not in ["km", "fuel", "maint"]:
            await update.message.reply_text("❌ Tipo deve ser: km, fuel ou maint")
            return
            
        data = download_data()
        if index < 0 or index >= len(data[tipo]):
            await update.message.reply_text("❌ Índice inválido")
            return
            
        removido = data[tipo].pop(index)
        upload_data(data)
        await update.message.reply_text(f"🗑️ Registro removido!")
        
    except:
        await update.message.reply_text("❌ Use: `/del km 1`", parse_mode="Markdown")

# ========== CONFIGURAÇÃO DO BOT ==========
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Registrar handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addkm", add_km))
app.add_handler(CommandHandler("fuel", add_fuel))
app.add_handler(CommandHandler("maint", add_maintenance))
app.add_handler(CommandHandler("report", report))
app.add_handler(CommandHandler("del", delete_record))

print("🎉 Bot configurado!")

# ========== WEBHOOK NO RAILWAY ==========
print("🌐 Configurando Webhook no Railway...")

# Limpar webhook antigo primeiro
try:
    response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
    print(f"✅ Webhook antigo removido: {response.json()}")
except Exception as e:
    print(f"⚠️ Erro ao remover webhook: {e}")

# Configurar webhook
webhook_url = f"{APP_URL}/{BOT_TOKEN}"
print(f"🌐 Webhook URL: {webhook_url}")

try:
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=webhook_url,
        url_path=BOT_TOKEN,
        drop_pending_updates=True
    )
except Exception as e:
    print(f"❌ Erro no webhook: {e}")
    print("🔄 Tentando polling como fallback...")
    try:
        app.run_polling()
    except Exception as poll_error:
        print(f"❌ Erro no polling também: {poll_error}")
