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

# ========== GOOGLE DRIVE ==========
def get_drive_service():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("❌ GOOGLE_CREDENTIALS não encontrada!")
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive.file"]
    )
    return build("drive", "v3", credentials=creds)

try:
    drive_service = get_drive_service()
    print("✅ Google Drive conectado!")
except Exception as e:
    print(f"❌ Erro no Google Drive: {e}")
    drive_service = None

# ========== FUNÇÕES DRIVE ==========
def get_drive_file_id(filename):
    try:
        results = drive_service.files().list(
            q=f"name='{filename}'", 
            fields="files(id, name)", 
            spaces="drive"
        ).execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None
    except Exception as e:
        print(f"❌ Erro ao buscar arquivo: {e}")
        return None

def download_data():
    try:
        file_id = get_drive_file_id(DRIVE_FILENAME)
        if not file_id:
            return {"km": [], "fuel": [], "maintenance": []}

        request = drive_service.files().get_media(fileId=file_id)
        file_content = request.execute()
        return json.loads(file_content.decode('utf-8'))
    except Exception as e:
        print(f"❌ Erro ao baixar dados: {e}")
        return {"km": [], "fuel": [], "maintenance": []}

def upload_data(data):
    try:
        file_id = get_drive_file_id(DRIVE_FILENAME)
        file_metadata = {"name": DRIVE_FILENAME}
        
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        fh = io.BytesIO(json_data.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='application/json')
        
        if file_id:
            drive_service.files().update(fileId=file_id, media_body=media).execute()
        else:
            drive_service.files().create(body=file_metadata, media_body=media).execute()
        print("✅ Dados salvos no Drive")
    except Exception as e:
        print(f"❌ Erro ao salvar no Drive: {e}")

# ========== HANDLERS ==========
def format_date():
    now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    return f"{now.day:02}/{now.month:02} {now.hour:02}:{now.minute:02}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await update.message.reply_text(f"✅ KM: {km_value}")
    except:
        await update.message.reply_text("❌ Use: `/addkm 15000`", parse_mode="Markdown")

async def add_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        liters, price = float(context.args[0]), float(context.args[1])
        data = download_data()
        data["fuel"].append({"date": format_date(), "liters": liters, "price": price})
        upload_data(data)
        await update.message.reply_text(f"⛽ {liters}L a R$ {price:.2f}")
    except:
        await update.message.reply_text("❌ Use: `/fuel 10 5.50`", parse_mode="Markdown")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = download_data()
    msg = "🏍️ *RELATÓRIO*\n\n"
    
    msg += "📏 KM:\n" + ("\n".join([f"• {d['date']} - {d['km']} km" for d in data["km"][-5:]]) or "Nenhum registro") + "\n\n"
    msg += "⛽ Abastecimentos:\n" + ("\n".join([f"• {d['date']} - {d['liters']}L a R$ {d['price']:.2f}" for d in data["fuel"][-5:]]) or "Nenhum registro")
    
    await update.message.reply_text(msg, parse_mode="Markdown")

# ========== INICIALIZAÇÃO ==========
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addkm", add_km))
app.add_handler(CommandHandler("fuel", add_fuel))
app.add_handler(CommandHandler("report", report))

print("🎉 Bot configurado!")

# ========== WEBHOOK NO RAILWAY ==========
print("🌐 Iniciando WEBHOOK...")
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=f"{APP_URL}/{BOT_TOKEN}",
    url_path=BOT_TOKEN,
    drop_pending_updates=True
)
