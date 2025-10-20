import requests
import pytz
from datetime import datetime
from config import BOT_TOKEN
from database import bot_data

def send_message(chat_id, text):
    """
    Envia mensagem para um chat específico do Telegram
    Usa parse_mode Markdown para formatação
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return False

def send_document(chat_id, document, filename):
    """
    Envia documento PDF para o chat do Telegram
    Retorna True se enviou com sucesso
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    files = {'document': (filename, document, 'application/pdf')}
    data = {'chat_id': chat_id}
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro ao enviar PDF: {e}")
        return False

def format_date():
    """
    Retorna data e hora atual formatada no fuso de São Paulo
    Formato: DD/MM/AA às HH:MM
    """
    tz_sp = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz_sp)
    return f"{now.day:02d}/{now.month:02d}/{str(now.year)[-2:]} às {now.hour:02d}:{now.minute:02d}"

def get_last_km():
    """
    Retorna o último KM registrado
    Retorna 0 se não houver registros
    """
    if bot_data["km"]:
        return bot_data["km"][-1]["km"]
    return 0

def get_last_oil_change():
    """
    Encontra a última troca de óleo registrada
    Procura por palavras-chave nas descrições de manutenção
    Retorna o KM da última troca ou 0 se não encontrou
    """
    oil_keywords = ['óleo', 'oleo', 'OLEO', 'ÓLEO', 'Óleo']
    
    for manu in reversed(bot_data["manu"]):
        desc_lower = manu['desc'].lower()
        if any(keyword.lower() in desc_lower for keyword in oil_keywords):
            return manu['km']
    return 0

def check_oil_change_alert(current_km):
    """
    Verifica se está próximo da troca de óleo (a cada 1000km)
    Retorna mensagem de alerta apropriada ou None se não há alerta
    """
    last_oil_km = get_last_oil_change()
    
    if last_oil_km == 0:
        return "⚠️ *ALERTA:* NENHUMA TROCA DE ÓLEO REGISTRADA AINDA!"
    
    km_since_last_oil = current_km - last_oil_km
    km_remaining = 1000 - km_since_last_oil
    
    # Sistema de alertas progressivos - SEMPRE retorna uma mensagem
    if km_since_last_oil >= 1000:
        return f"* LASCOU - {km_since_last_oil}KM RODADOS*!\n        🚨TROQUE O ÓLEO AGORA!🚨"
    elif km_remaining <= 100:
        return f"🔴*ALERTA CRÍTICO*🔴\n*{km_remaining}KM* PARA TROCAR DE ÓLEO!"
    elif km_remaining <= 300:
        return f"🟡*ALERTA*🟡\n*{km_remaining}KM* PARA TROCAR DE ÓLEO"
    elif km_remaining <= 500:
        return f"🔵*LEMBRETE*🔵\n*{km_remaining}KM* PARA TROCAR DE ÓLEO"
    else:
        # SEMPRE retorna uma mensagem, mesmo que seja apenas informativa
        return f"⚪*STATUS ÓLEO*⚪\n*{km_since_last_oil}KM* RODADOS | *{km_remaining}KM* RESTANTES"

def total_fuel_mes():
    """
    Calcula o total gasto em abastecimentos no mês atual
    Considera apenas registros do mês e ano corrente
    """
    now = datetime.now()
    mes_atual = now.month
    ano_atual = now.year
    
    total = 0
    for item in bot_data["fuel"]:
        try:
            data_str = item['date'].split(' às ')[0]
            dia, mes, ano = map(int, data_str.split('/'))
            ano_completo = 2000 + ano
            
            if mes == mes_atual and ano_completo == ano_atual:
                total += item['price']
        except:
            continue
    
    return total

def total_fuel_geral():
    """
    Calcula o total gasto em todos os abastecimentos registrados
    """
    total = 0
    for item in bot_data["fuel"]:
        total += item['price']
    return total
