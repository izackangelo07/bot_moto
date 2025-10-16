import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
from datetime import datetime

DATA_FILE = "moto_data.json"

# -----------------------------
# Funções de leitura e escrita
# -----------------------------
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"km": [], "fuel": [], "maintenance": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# -----------------------------
# Função auxiliar de data
# -----------------------------
def format_date():
    now = datetime.now()
    return f"| {now.day:02}/{now.month:02}/{str(now.year)[2:]} às {now.hour:02} horas |"

# -----------------------------
# Comandos do bot
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🏍️ Bem-vindo ao Bot da Moto!\n\n"
    msg += "Comandos disponíveis:\n"
    msg += "/start - Mostra esta mensagem\n"
    msg += "/addkm <quilometragem> - Registra o KM atual\n"
    msg += "/fuel <litros> <preço> - Registra abastecimento\n"
    msg += "/maint <descrição> - Registra manutenção\n"
    msg += "/report - Mostra o relatório completo da moto\n"
    msg += "/del <km|fuel|maint> <número> - Remove um registro errado\n"
    await update.message.reply_text(msg)

async def add_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Use: /addkm <quilometragem>")
        return
    
    data = load_data()
    km_value = int(context.args[0])
    data["km"].append({"date": format_date(), "km": km_value})
    save_data(data)
    await update.message.reply_text(f"KM registrado: {km_value}")

async def add_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Use: /fuel <litros> <preço>")
        return
    try:
        liters = float(context.args[0])
        price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Litros e preço devem ser números.")
        return

    data = load_data()

    # Calcular km percorridos desde o último abastecimento
    last_km = None
    if data["km"]:
        last_km = data["km"][-1]["km"]

    km_since_last_fuel = 0
    if data["fuel"] and last_km is not None:
        for km_entry in reversed(data["km"]):
            if km_entry["date"] <= data["fuel"][-1]["date"]:
                last_km = km_entry["km"]
                break
        km_since_last_fuel = 0 if last_km is None else data["km"][-1]["km"] - last_km

    # Registrar o abastecimento
    data["fuel"].append({
        "date": format_date(),
        "liters": liters,
        "price": price,
        "km_since_last": km_since_last_fuel
    })
    save_data(data)

    await update.message.reply_text(f"Abastecimento registrado: {liters}L a R${price} cada")

async def add_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Use: /maint <descrição da manutenção>")
        return
    data = load_data()
    desc = " ".join(context.args)
    data["maintenance"].append({"date": format_date(), "desc": desc})
    save_data(data)
    await update.message.reply_text(f"Manutenção registrada: {desc}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = "🏍️ Relatório da Moto:\n\n"
    msg += "KMs:\n" + "\n".join([f"{i+1}. {d['date']} {d['km']} km" for i, d in enumerate(data["km"])]) + "\n\n"
    msg += "Abastecimentos:\n" + "\n".join([f"{i+1}. {d['date']} {d['liters']}L a R${d['price']}" for i, d in enumerate(data["fuel"])]) + "\n\n"
    msg += "Manutenções:\n" + "\n".join([f"{i+1}. {d['date']} {d['desc']}" for i, d in enumerate(data["maintenance"])])
    await update.message.reply_text(msg)

async def delete_record(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Use: /del <km|fuel|maint> <número do registro>")
        return

    tipo = context.args[0].lower()
    try:
        index = int(context.args[1]) - 1
    except ValueError:
        await update.message.reply_text("O índice deve ser um número.")
        return

    data = load_data()

    if tipo not in data:
        await update.message.reply_text("Tipo inválido. Use: km, fuel ou maint.")
        return

    if index < 0 or index >= len(data[tipo]):
        await update.message.reply_text("Índice inválido.")
        return

    removed = data[tipo].pop(index)
    save_data(data)
    await update.message.reply_text(f"Registro removido com sucesso:\n{removed}")

# -----------------------------
# Inicialização do bot
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Você precisa definir a variável de ambiente BOT_TOKEN")

app = ApplicationBuilder().token(BOT_TOKEN).build()

# Registrando os comandos
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addkm", add_km))
app.add_handler(CommandHandler("fuel", add_fuel))
app.add_handler(CommandHandler("maint", add_maintenance))
app.add_handler(CommandHandler("report", report))
app.add_handler(CommandHandler("del", delete_record))

app.run_polling()
