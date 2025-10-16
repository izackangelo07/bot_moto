import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ----------------- Google Sheets -----------------
scope = ["https://spreadsheets.google.com/feeds",
         'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client = gspread.authorize(creds)
sheet_km = client.open("Moto").worksheet("KM")
sheet_fuel = client.open("Moto").worksheet("Combustível")
sheet_maint = client.open("Moto").worksheet("Manutenção")

# ----------------- Comandos -----------------
# Registrar KM
def add_km(update: Update, context: CallbackContext):
    try:
        km = float(context.args[0])
        sheet_km.append_row([datetime.now().strftime("%d/%m/%Y"), km])
        # Verifica total acumulado
        total_km = sum([float(row[1]) for row in sheet_km.get_all_values()[1:]])
        if total_km % 900 < 50:
            update.message.reply_text(f"⚠️ Está na hora de trocar o óleo! Total: {total_km} km")
        else:
            update.message.reply_text(f"✅ KM registrado! Total rodado: {total_km} km")
    except:
        update.message.reply_text("Erro! Use: /km QUANTIDADE")

# Registrar combustível
def add_fuel(update: Update, context: CallbackContext):
    try:
        valor = float(context.args[0].replace(",", "."))
        sheet_fuel.append_row([datetime.now().strftime("%d/%m/%Y"), valor])
        update.message.reply_text("✅ Combustível registrado!")
    except:
        update.message.reply_text("Erro! Use: /fuel VALOR")

# Registrar manutenção
def add_maintenance(update: Update, context: CallbackContext):
    try:
        km = float(context.args[0])
        service = " ".join(context.args[1:])
        sheet_maint.append_row([datetime.now().strftime("%d/%m/%Y"), km, service])
        update.message.reply_text("✅ Manutenção registrada!")
    except:
        update.message.reply_text("Erro! Use: /maintenance KM SERVIÇO")

# Resumo combustível mensal
def fuel_summary(update: Update, context: CallbackContext):
    data = sheet_fuel.get_all_records()
    total = sum(float(d["Valor (R$)"]) for d in data if datetime.strptime(d["Data"], "%d/%m/%Y").month == datetime.now().month)
    update.message.reply_text(f"💰 Gasto total com combustível este mês: R${total:.2f}")

# ----------------- Bot -----------------
TOKEN = os.environ.get("BOT_TOKEN")  # colocar token no Render como variável de ambiente
updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("km", add_km))
dp.add_handler(CommandHandler("fuel", add_fuel))
dp.add_handler(CommandHandler("maintenance", add_maintenance))
dp.add_handler(CommandHandler("fuelmes", fuel_summary))

# ----------------- Iniciar bot -----------------
if __name__ == "__main__":
    print("Bot iniciado com polling...")
    updater.start_polling()  # para Render Free funciona bem
    updater.idle()
