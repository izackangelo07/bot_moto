import os
from pyrogram import Client, filters
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ========================
# Configurações básicas
# ========================
PORT = int(os.environ.get("PORT", 10000))

api_id = os.environ.get("API_ID")
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")

app = Client(
    "bot_moto",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_token,
)

# ========================
# Conexão com Google Sheets
# ========================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credenciais.json", scope)
client = gspread.authorize(creds)

# Planilhas
km_sheet = client.open("Moto").worksheet("KM")
fuel_sheet = client.open("Moto").worksheet("Combustivel")

# ========================
# Comandos
# ========================

@app.on_message(filters.command("start"))
def start(_, msg):
    msg.reply_text(
        "🏍️ *Bem-vindo ao Bot da Moto!*\n\n"
        "Comandos disponíveis:\n"
        "/km <valor> — registra quilometragem\n"
        "/fuel <litros> <valor> — registra combustível\n"
        "/fuelmes — mostra gasto mensal\n"
        "/oleo — verifica se já está na hora de trocar o óleo",
        quote=True
    )

@app.on_message(filters.command("km"))
def km_register(_, msg):
    try:
        km = msg.text.split()[1]
        km_sheet.append_row([msg.from_user.first_name, km])
        msg.reply_text(f"✅ Quilometragem registrada: {km} km")
    except:
        msg.reply_text("❌ Use: `/km 10234`")

@app.on_message(filters.command("fuel"))
def fuel_register(_, msg):
    try:
        _, litros, valor = msg.text.split()
        fuel_sheet.append_row([msg.from_user.first_name, litros, valor])
        msg.reply_text(f"⛽ Combustível registrado: {litros} L por R$ {valor}")
    except:
        msg.reply_text("❌ Use: `/fuel 5.2 35.00`")

@app.on_message(filters.command("fuelmes"))
def fuel_mes(_, msg):
    registros = fuel_sheet.get_all_values()[1:]
    total = sum(float(r[2]) for r in registros if r[2])
    msg.reply_text(f"💰 Gasto total com combustível no mês: R$ {total:.2f}")

@app.on_message(filters.command("oleo"))
def oleo_alerta(_, msg):
    registros = km_sheet.get_all_values()
    if len(registros) < 2:
        msg.reply_text("⚠️ Poucos registros de KM para calcular.")
        return
    km_atual = int(registros[-1][1])
    km_inicial = int(registros[0][1])
    rodado = km_atual - km_inicial

    if rodado >= 900:
        msg.reply_text("🛢️ Já passou 900km! Hora de trocar o óleo.")
    else:
        falta = 900 - rodado
        msg.reply_text(f"📏 Faltam {falta} km para a troca de óleo.")

# ========================
# Webhook (Render)
# ========================
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="",
        webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/",
    )
