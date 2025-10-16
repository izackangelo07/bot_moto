from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
from datetime import datetime

DATA_FILE = "moto_data.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"km": [], "fuel": [], "maintenance": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

async def add_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    km_value = int(context.args[0])
    data["km"].append({"date": str(datetime.now()), "km": km_value})
    save_data(data)
    await update.message.reply_text(f"KM registrado: {km_value}")

async def add_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    liters = float(context.args[0])
    price = float(context.args[1])
    data["fuel"].append({"date": str(datetime.now()), "liters": liters, "price": price})
    save_data(data)
    await update.message.reply_text(f"Abastecimento registrado: {liters}L a R${price} cada")

async def add_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    desc = " ".join(context.args)
    data["maintenance"].append({"date": str(datetime.now()), "desc": desc})
    save_data(data)
    await update.message.reply_text(f"Manutenção registrada: {desc}")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    msg = "🏍️ Relatório da Moto:\n\n"
    msg += "KM:\n" + "\n".join([f"{d['date']}: {d['km']} km" for d in data["km"]]) + "\n\n"
    msg += "Abastecimento:\n" + "\n".join([f"{d['date']}: {d['liters']}L a R${d['price']}" for d in data["fuel"]]) + "\n\n"
    msg += "Manutenção:\n" + "\n".join([f"{d['date']}: {d['desc']}" for d in data["maintenance"]])
    await update.message.reply_text(msg)

app = ApplicationBuilder().token("SEU_TOKEN_AQUI").build()

app.add_handler(CommandHandler("addkm", add_km))
app.add_handler(CommandHandler("fuel", add_fuel))
app.add_handler(CommandHandler("maint", add_maintenance))
app.add_handler(CommandHandler("report", report))

app.run_polling()
