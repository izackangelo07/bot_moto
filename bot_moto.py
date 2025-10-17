import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import io
import requests
import asyncio

# Nome do arquivo usado no Drive
DRIVE_FILENAME = "moto_data.json"

# ========== GOOGLE DRIVE AUTH ==========
def get_drive_service():
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("❌ GOOGLE_CREDENTIALS não encontrada!")
    creds_dict = json.loads(creds_json)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

drive_service = get_drive_service()

# ========== FUNÇÕES DE ARQUIVO ==========
def get_drive_file_id(filename):
    results = (
        drive_service.files()
        .list(q=f"name='{filename}'", fields="files(id, name)", spaces="drive")
        .execute()
    )
    files = results.get("files", [])
    return files[0]["id"] if files else None

def download_data():
    file_id = get_drive_file_id(DRIVE_FILENAME)
    if not file_id:
        return {"km": [], "fuel": [], "maintenance": []}

    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return json.load(fh)

def upload_data(data):
    file_id = get_drive_file_id(DRIVE_FILENAME)
    file_metadata = {"name": DRIVE_FILENAME}
    fh = io.BytesIO(json.dumps(data, indent=2).encode("utf-8"))
    media = MediaIoBaseUpload(fh, mimetype="application/json", resumable=True)

    if file_id:
        drive_service.files().update(fileId=file_id, media_body=media).execute()
    else:
        drive_service.files().create(body=file_metadata, media_body=media).execute()

# ========== FUNÇÕES DE FORMATAÇÃO ==========
def format_date():
    now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    return f"| {now.day:02}/{now.month:02}/{str(now.year)[2:]} às {now.hour} horas |"

# ========== COMANDOS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /start recebido")
    msg = (
        "🏍️ *Bem-vindo ao Controle da Moto!*\n\n"
        "Comandos disponíveis:\n"
        "• `/addkm <valor>` — Registrar quilometragem\n"
        "• `/fuel <litros> <preço>` — Registrar abastecimento\n"
        "• `/maint <descrição>` — Registrar manutenção\n"
        "• `/report` — Ver relatório completo\n"
        "• `/del <tipo> <índice>` — Apagar um registro (km, fuel ou maint)\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def add_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /addkm recebido")
    try:
        km_value = int(context.args[0])
    except:
        await update.message.reply_text("Use: /addkm <valor>")
        return
    data = download_data()
    data["km"].append({"date": format_date(), "km": km_value})
    upload_data(data)
    await update.message.reply_text(f"✅ KM registrado: {km_value} km")

async def add_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /fuel recebido")
    try:
        liters = float(context.args[0])
        price = float(context.args[1])
    except:
        await update.message.reply_text("Use: /fuel <litros> <preço>")
        return
    data = download_data()
    data["fuel"].append({"date": format_date(), "liters": liters, "price": price})
    upload_data(data)
    await update.message.reply_text(f"⛽ Abastecimento: {liters}L a R${price}")

async def add_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /maint recebido")
    if not context.args:
        await update.message.reply_text("Use: /maint <descrição>")
        return
    desc = " ".join(context.args)
    data = download_data()
    data["maintenance"].append({"date": format_date(), "desc": desc})
    upload_data(data)
    await update.message.reply_text(f"🧰 Manutenção registrada: {desc}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /report recebido")
    data = download_data()
    msg = "🏍️ *Relatório da Moto:*\n\n"
    msg += "📏 *KM:*\n" + (
        "\n".join([f"{i+1}. {d['date']} — {d['km']} km" for i, d in enumerate(data["km"])])
        if data["km"] else "Nenhum registro."
    ) + "\n\n"
    msg += "⛽ *Abastecimentos:*\n" + (
        "\n".join([f"{i+1}. {d['date']} — {d['liters']}L a R${d['price']}" for i, d in enumerate(data["fuel"])])
        if data["fuel"] else "Nenhum registro."
    ) + "\n\n"
    msg += "🧰 *Manutenções:*\n" + (
        "\n".join([f"{i+1}. {d['date']} — {d['desc']}" for i, d in enumerate(data["maintenance"])])
        if data["maintenance"] else "Nenhum registro."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def delete_record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ /del recebido")
    if len(context.args) != 2:
        await update.message.reply_text("Use: /del <km|fuel|maint> <número>")
        return
    tipo, index = context.args[0], context.args[1]
    if tipo not in ["km", "fuel", "maint"]:
        await update.message.reply_text("Tipo inválido. Use: km, fuel ou maint.")
        return
    try:
        index = int(index) - 1
    except:
        await update.message.reply_text("O índice deve ser um número.")
        return
    data = download_data()
    if index < 0 or index >= len(data[tipo]):
        await update.message.reply_text("Número inválido.")
        return
    removido = data[tipo].pop(index)
    upload_data(data)
    await update.message.reply_text(f"🗑️ Registro removido: {removido}")

# ========== MAIN / WEBHOOK ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")  # https://botmoto-production.up.railway.app

print("✅ Iniciando Bot...")
print("APP_URL:", APP_URL)
print("BOT_TOKEN:", BOT_TOKEN[:5] + "...")

# Limpar webhook antigo
delete_wh = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
print("❌ Webhook antigo removido:", delete_wh.text)

app = ApplicationBuilder().token(BOT_TOKEN).build()

# Registrando handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addkm", add_km))
app.add_handler(CommandHandler("fuel", add_fuel))
app.add_handler(CommandHandler("maint", add_maintenance))
app.add_handler(CommandHandler("report", report))
app.add_handler(CommandHandler("del", delete_record))

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
