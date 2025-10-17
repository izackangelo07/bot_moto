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
print("✅ Google Drive conectado!")

# ========== FUNÇÕES DE ARQUIVO ==========
def get_drive_file_id(filename):
    try:
        results = (
            drive_service.files()
            .list(q=f"name='{filename}'", fields="files(id, name)", spaces="drive")
            .execute()
        )
        files = results.get("files", [])
        return files[0]["id"] if files else None
    except Exception as e:
        print(f"❌ Erro ao buscar arquivo: {e}")
        return None

def download_data():
    try:
        file_id = get_drive_file_id(DRIVE_FILENAME)
        if not file_id:
            print("📁 Arquivo não encontrado, criando novo...")
            return {"km": [], "fuel": [], "maintenance": []}

        # Download do arquivo
        request = drive_service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoBaseUpload(file_content, mimetype='application/json')
        
        # Fazer upload vazio para forçar download? Vamos simplificar:
        # Vamos criar uma nova abordagem mais simples
        from googleapiclient.http import MediaIoBaseDownload
        
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        content = fh.getvalue().decode('utf-8')
        return json.loads(content)
        
    except Exception as e:
        print(f"❌ Erro ao baixar dados: {e}")
        return {"km": [], "fuel": [], "maintenance": []}

def upload_data(data):
    try:
        file_id = get_drive_file_id(DRIVE_FILENAME)
        file_metadata = {"name": DRIVE_FILENAME}
        
        # Converter dados para JSON
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        fh = io.BytesIO(json_data.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimetype='application/json')
        
        if file_id:
            # Atualizar arquivo existente
            drive_service.files().update(
                fileId=file_id, 
                media_body=media
            ).execute()
            print("✅ Arquivo atualizado no Drive")
        else:
            # Criar novo arquivo
            drive_service.files().create(
                body=file_metadata, 
                media_body=media,
                fields='id'
            ).execute()
            print("✅ Novo arquivo criado no Drive")
            
    except Exception as e:
        print(f"❌ Erro ao fazer upload: {e}")

# ========== FUNÇÕES DE FORMATAÇÃO ==========
def format_date():
    now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    return f"| {now.day:02}/{now.month:02}/{str(now.year)[2:]} às {now.hour:02}:{now.minute:02} |"

# ========== COMANDOS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"✅ /start recebido de {chat_id}")
    
    msg = (
        "🏍️ *Bem-vindo ao Controle da Moto!*\n\n"
        "📋 *Comandos disponíveis:*\n"
        "• `/addkm <valor>` — Registrar quilometragem\n"
        "• `/fuel <litros> <preço>` — Registrar abastecimento\n"
        "• `/maint <descrição>` — Registrar manutenção\n"
        "• `/report` — Ver relatório completo\n"
        "• `/del <tipo> <índice>` — Apagar registro\n\n"
        "💡 *Exemplos:*\n"
        "`/addkm 15000`\n"
        "`/fuel 10 5.50`\n"
        "`/maint Troca de óleo`\n"
        "`/del km 1`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def add_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"✅ /addkm recebido de {chat_id}")
    
    try:
        km_value = int(context.args[0])
        if km_value <= 0:
            await update.message.reply_text("❌ Valor de KM deve ser positivo!")
            return
    except:
        await update.message.reply_text("❌ Use: `/addkm <valor>`\nEx: `/addkm 15000`", parse_mode="Markdown")
        return
    
    data = download_data()
    data["km"].append({
        "date": format_date(), 
        "km": km_value,
        "chat_id": chat_id
    })
    upload_data(data)
    await update.message.reply_text(f"✅ *KM registrado:* {km_value} km", parse_mode="Markdown")

async def add_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"✅ /fuel recebido de {chat_id}")
    
    try:
        liters = float(context.args[0])
        price = float(context.args[1])
        if liters <= 0 or price <= 0:
            await update.message.reply_text("❌ Valores devem ser positivos!")
            return
    except:
        await update.message.reply_text("❌ Use: `/fuel <litros> <preço>`\nEx: `/fuel 10 5.50`", parse_mode="Markdown")
        return
    
    data = download_data()
    data["fuel"].append({
        "date": format_date(), 
        "liters": liters, 
        "price": price,
        "total": liters * price,
        "chat_id": chat_id
    })
    upload_data(data)
    await update.message.reply_text(f"⛽ *Abastecimento registrado:*\n{liters}L a R$ {price:.2f}\nTotal: R$ {liters * price:.2f}", parse_mode="Markdown")

async def add_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"✅ /maint recebido de {chat_id}")
    
    if not context.args:
        await update.message.reply_text("❌ Use: `/maint <descrição>`\nEx: `/maint Troca de óleo do motor`", parse_mode="Markdown")
        return
    
    desc = " ".join(context.args)
    data = download_data()
    data["maintenance"].append({
        "date": format_date(), 
        "desc": desc,
        "chat_id": chat_id
    })
    upload_data(data)
    await update.message.reply_text(f"🧰 *Manutenção registrada:*\n{desc}", parse_mode="Markdown")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"✅ /report recebido de {chat_id}")
    
    data = download_data()
    
    msg = "🏍️ *RELATÓRIO DA MOTO*\n\n"
    
    # Quilometragem
    msg += "📏 *QUILOMETRAGEM:*\n"
    if data["km"]:
        for i, d in enumerate(data["km"][-10:]):  # Últimos 10 registros
            msg += f"`{i+1:2d}.` {d['date']} — {d['km']} km\n"
    else:
        msg += "📭 Nenhum registro de KM\n"
    
    # Abastecimentos
    msg += "\n⛽ *ABASTECIMENTOS:*\n"
    if data["fuel"]:
        total_gasto = 0
        total_litros = 0
        for i, d in enumerate(data["fuel"][-10:]):
            msg += f"`{i+1:2d}.` {d['date']} — {d['liters']}L × R$ {d['price']:.2f} = R$ {d['total']:.2f}\n"
            total_gasto += d['total']
            total_litros += d['liters']
        msg += f"📊 Total: {total_litros:.1f}L | R$ {total_gasto:.2f}\n"
    else:
        msg += "📭 Nenhum abastecimento\n"
    
    # Manutenções
    msg += "\n🧰 *MANUTENÇÕES:*\n"
    if data["maintenance"]:
        for i, d in enumerate(data["maintenance"][-10:]):
            msg += f"`{i+1:2d}.` {d['date']} — {d['desc']}\n"
    else:
        msg += "📭 Nenhuma manutenção\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def delete_record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    print(f"✅ /del recebido de {chat_id}")
    
    if len(context.args) != 2:
        await update.message.reply_text("❌ Use: `/del <km|fuel|maint> <número>`\nEx: `/del km 1`", parse_mode="Markdown")
        return
    
    tipo, index = context.args[0], context.args[1]
    
    if tipo not in ["km", "fuel", "maint"]:
        await update.message.reply_text("❌ Tipo inválido. Use: `km`, `fuel` ou `maint`", parse_mode="Markdown")
        return
    
    try:
        index = int(index) - 1
    except:
        await update.message.reply_text("❌ O índice deve ser um número válido")
        return
    
    data = download_data()
    
    if index < 0 or index >= len(data[tipo]):
        await update.message.reply_text(f"❌ Número inválido. Use de 1 a {len(data[tipo])}")
        return
    
    removido = data[tipo].pop(index)
    upload_data(data)
    
    await update.message.reply_text(f"🗑️ *Registro removido:*\n{removido}", parse_mode="Markdown")

# ========== CONFIGURAÇÃO DO BOT ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN não encontrado!")
    exit(1)

print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print("🔄 Iniciando bot com POLLING...")

# Criar aplicação
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Registrar handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addkm", add_km))
app.add_handler(CommandHandler("fuel", add_fuel))
app.add_handler(CommandHandler("maint", add_maintenance))
app.add_handler(CommandHandler("report", report))
app.add_handler(CommandHandler("del", delete_record))

# Iniciar com POLLING (mais confiável no Railway)
print("🎉 Bot iniciado! Use /start no Telegram")
app.run_polling()
