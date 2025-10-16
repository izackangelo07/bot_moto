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
    await update.message.reply_text(msg)

async def add_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Use: /addkm <quilometragem>")
        return
    
    data = load_data()
    km_value = int(context.args[0])
    data["km"].append({"date": str(datetime.now()), "km": km_value})
    save_data(data)
    await update.message.reply_text(f"KM registrado: {km_value}")
    
    # -------------------------
    # ALERTA AUTOMÁTICO TROCA DE ÓLEO
    # -------------------------
    last_oil_km = 0
    for m in reversed(data["maintenance"]):
        if "óleo" in m["desc"].lower():
            # Pega o km correspondente à última manutenção de óleo
            for km_entry in reversed(data["km"]):
                if km_entry["date"] <= m["date"]:
                    last_oil_km = km_entry["km"]
                    break
            break

    km_since_last_oil = km_value - last_oil_km
    if km_since_last_oil >= 900:
        await update.message.reply_text(
            f"⚠️ ALERTA AUTOMÁTICO: Já se passaram {km_since_last_oil} km desde a última troca de óleo. Hora de trocar o óleo!"
        )

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
        "date": str(datetime.now()),
        "liters": liters,
        "price": price,
        "km_since_last": km_since_last_fuel
    })
    save_data(data)
    
    consumo_msg = f"Abastecimento registrado: {liters}L a R${price} cada"
    if km_since_last_fuel > 0 and liters > 0:
        consumo = km_since_last_fuel / liters
        consumo_msg += f"\nConsumo médio desde o último abastecimento: {consumo:.2f} km/l"
    
    await update.message.reply_text(consumo_msg)

async def add_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Use: /maint <descrição da manutenção>")
        return
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

    # Consumo médio total
    total_km = 0
    total_liters = 0
    for f in data["fuel"]:
        if "km_since_last" in f:
            total_km += f["km_since_last"]
            total_liters += f["liters"]

    if total_liters > 0:
        consumo_total = total_km / total_liters
        msg += f"\n\nConsumo médio total: {consumo_total:.2f} km/l"

    await update.message.reply_text(msg)

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

app.run_polling()
