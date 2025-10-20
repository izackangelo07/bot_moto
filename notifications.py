import time
import pytz
from datetime import datetime
from config import NOTIFICATION_CHAT_ID
from database import bot_data
from utils import get_last_km, check_oil_change_alert, send_message

def send_daily_notification():
    """Envia notificação diária sobre status do óleo"""
    print(f"🔔 Tentando enviar notificação para chat: {NOTIFICATION_CHAT_ID}")
    
    if not NOTIFICATION_CHAT_ID:
        print("❌ NOTIFICATION_CHAT_ID não configurado")
        return
    
    try:
        current_km = get_last_km()
        print(f"🔔 KM atual: {current_km}")
        
        if current_km > 0:
            alert_msg = check_oil_change_alert(current_km)
            print(f"🔔 Mensagem de alerta: {alert_msg}")
            
            if alert_msg:
                notification = f" ```       🔔 MANUTENÇÃO POPzinha 🔔```\n{alert_msg}"
                send_message(NOTIFICATION_CHAT_ID, notification)
                print(f"✅ Notificação enviada para chat {NOTIFICATION_CHAT_ID}")
            else:
                print("ℹ️ Sem alerta ativo para notificação")
        else:
            print("ℹ️ Sem KM registrado para notificação")
    except Exception as e:
        print(f"❌ Erro na notificação: {e}")

def notification_scheduler():
    """
    Agendador de notificações diárias
    Verifica horários específicos (8:00 e 14:00) e envia notificações
    Controla para enviar apenas uma notificação por horário por dia
    """
    print("⏰ Iniciando agendador de notificações...")
    last_notification_hour = None
    
    while True:
        try:
            now = datetime.now(pytz.timezone('America/Sao_Paulo'))
            current_hour = now.hour
            current_minute = now.minute
            
            # Verificar horários configurados (8:00 e 14:00)
            if ((current_hour == 8 and current_minute == 0) or (current_hour == 15 and current_minute == 18)) and last_notification_hour != current_hour:
                print("🕗 Enviando notificação...")
                send_daily_notification()
                last_notification_hour = current_hour
                time.sleep(61)  # Evita múltiplos envios no mesmo minuto
            else:
                time.sleep(30)  # Verifica a cada 30 segundos
                
        except Exception as e:
            print(f"❌ Erro no agendador: {e}")
            time.sleep(60)
