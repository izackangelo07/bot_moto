import requests
import pytz
from datetime import datetime
from config import BOT_TOKEN
from database import bot_data

# ---------------------------------------------------------
# 🔹 ENVIO DE MENSAGENS
# ---------------------------------------------------------
def send_message(chat_id, text):
    """Envia mensagem simples usando Markdown."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}

    try:
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return False


def send_document(chat_id, document, filename):
    """Envia PDF para o chat."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    files = {'document': (filename, document, 'application/pdf')}
    data = {'chat_id': chat_id}

    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar PDF: {e}")
        return False


# ---------------------------------------------------------
# 🔹 FORMATAÇÃO DE DATA
# ---------------------------------------------------------
def format_date():
    """Retorna data/hora no fuso de São Paulo no formato DD/MM/AA às HH:MM."""
    tz_sp = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz_sp)
    return f"{now.day:02d}/{now.month:02d}/{str(now.year)[-2:]} às {now.hour:02d}:{now.minute:02d}"


# ---------------------------------------------------------
# 🔹 KM E MANUTENÇÃO
# ---------------------------------------------------------
def get_last_km():
    """Retorna último KM registrado ou 0."""
    if bot_data["km"]:
        return bot_data["km"][-1]["km"]
    return 0


def get_last_oil_change():
    """Encontra o último KM onde houve troca de óleo."""
    oil_keywords = ['óleo', 'oleo', 'OLEO', 'ÓLEO', 'Óleo']

    for manu in reversed(bot_data["manu"]):
        desc_lower = manu['desc'].lower()
        if any(keyword.lower() in desc_lower for keyword in oil_keywords):
            return manu['km']
    return 0


def check_oil_change_alert(current_km):
    """Retorna mensagem de alerta sobre troca de óleo."""
    last_oil_km = get_last_oil_change()

    if last_oil_km == 0:
        return "⚠️ *ALERTA:* NENHUMA TROCA DE ÓLEO REGISTRADA AINDA!"

    km_since_last_oil = current_km - last_oil_km
    km_remaining = 1000 - km_since_last_oil

    if km_since_last_oil >= 1000:
        return (
            f"* LASCOU - {km_since_last_oil}KM RODADOS*!\n"
            f"        🚨TROQUE O ÓLEO AGORA!🚨"
        )
    elif km_remaining <= 100:
        return f"🔴*ALERTA CRÍTICO*🔴\n*{km_remaining}KM* PARA TROCAR DE ÓLEO!"
    elif km_remaining <= 300:
        return f"🟡*ALERTA*🟡\n*{km_remaining}KM* PARA TROCAR DE ÓLEO"
    elif km_remaining <= 500:
        return f"🔵*LEMBRETE*🔵\n*{km_remaining}KM* PARA TROCAR DE ÓLEO"
    else:
        return f"⚪*STATUS ÓLEO*⚪\n*{km_since_last_oil}KM* RODADOS | *{km_remaining}KM* RESTANTES"


# ---------------------------------------------------------
# 🔹 COMBUSTÍVEL POR MÊS / TOTAL
# ---------------------------------------------------------
def total_fuel_por_mes():
    """
    Retorna dicionário:
    {'Janeiro': 0, 'Fevereiro': 10.5, ..., 'Dezembro': 0}
    Para o ANO ATUAL.
    """
    ano_atual = datetime.now().year
    
    meses_nomes = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    totais = {mes: 0 for mes in meses_nomes}

    for item in bot_data["fuel"]:
        try:
            data_str = item['date'].split(' às ')[0]  # exemplo: "18/02/25"
            dia, mes, ano = map(int, data_str.split('/'))
            ano_completo = 2000 + ano  # transforma "25" em 2025

            if ano_completo == ano_atual:
                nome_mes = meses_nomes[mes - 1]
                totais[nome_mes] += item['price']
        except:
            continue

    return totais


def total_fuel_geral():
    """Soma tudo de combustível já registrado."""
    return sum(item['price'] for item in bot_data["fuel"])
