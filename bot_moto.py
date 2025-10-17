import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time
from datetime import datetime

print("🚀 BOT MOTOMANUTENÇÃO - HTTP MODE")

# ========== CONFIGURAÇÃO ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"🔧 Porta: {PORT}")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN não encontrado!")
    exit(1)

# ========== ARMAZENAMENTO EM MEMÓRIA ==========
bot_data = {"km": [], "fuel": [], "maintenance": []}

# ========== FUNÇÕES DO BOT ==========
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=data)
        return response.json()
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return None

def format_date():
    now = datetime.now()
    return f"{now.day:02d}/{now.month:02d} {now.hour:02d}:{now.minute:02d}"

def process_command(update):
    try:
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not chat_id or not text:
            return
        
        print(f"📨 Mensagem de {chat_id}: {text}")
        
        if text.startswith("/start"):
            send_message(chat_id, 
                "🏍️ *BOT MOTOMANUTENÇÃO*\n\n"
                "📋 Comandos:\n"
                "• `/addkm 15000`\n"
                "• `/fuel 10 5.50`\n"
                "• `/maint Troca de óleo`\n"
                "• `/report`\n"
                "• `/del km 1`\n"
                "• `/meuid`"
            )
        
        elif text.startswith("/addkm"):
            try:
                km_value = int(text.split()[1])
                bot_data["km"].append({"km": km_value, "date": format_date()})
                send_message(chat_id, f"✅ KM registrado: {km_value} km")
            except:
                send_message(chat_id, "❌ Use: `/addkm 15000`")
        
        elif text.startswith("/fuel"):
            try:
                parts = text.split()
                liters = float(parts[1])
                price = float(parts[2])
                bot_data["fuel"].append({"liters": liters, "price": price, "date": format_date()})
                send_message(chat_id, f"⛽ Abastecimento: {liters}L a R$ {price:.2f}")
            except:
                send_message(chat_id, "❌ Use: `/fuel 10 5.50`")
        
        elif text.startswith("/maint"):
            try:
                desc = " ".join(text.split()[1:])
                if desc:
                    bot_data["maintenance"].append({"desc": desc, "date": format_date()})
                    send_message(chat_id, f"🧰 Manutenção registrada: {desc}")
                else:
                    send_message(chat_id, "❌ Use: `/maint Troca de óleo`")
            except:
                send_message(chat_id, "❌ Use: `/maint Troca de óleo`")
        
        elif text.startswith("/report"):
            msg = "🏍️ *RELATÓRIO*\n\n"
            
            # KM
            msg += "📏 *KM:*\n"
            if bot_data["km"]:
                for item in bot_data["km"][-5:]:
                    msg += f"• {item['date']} - {item['km']} km\n"
            else:
                msg += "Nenhum registro\n"
            
            # Abastecimentos
            msg += "\n⛽ *Abastecimentos:*\n"
            if bot_data["fuel"]:
                for item in bot_data["fuel"][-5:]:
                    msg += f"• {item['date']} - {item['liters']}L a R$ {item['price']:.2f}\n"
            else:
                msg += "Nenhum registro\n"
            
            # Manutenções
            msg += "\n🧰 *Manutenções:*\n"
            if bot_data["maintenance"]:
                for item in bot_data["maintenance"][-5:]:
                    msg += f"• {item['date']} - {item['desc']}\n"
            else:
                msg += "Nenhum registro\n"
            
            send_message(chat_id, msg)
        
        elif text.startswith("/meuid"):
            send_message(chat_id, f"🆔 Seu ID: `{chat_id}`")
        
        elif text.startswith("/del"):
            try:
                parts = text.split()
                if len(parts) >= 3:
                    tipo = parts[1]
                    index = int(parts[2]) - 1
                    
                    if tipo in ["km", "fuel", "maint"] and 0 <= index < len(bot_data[tipo]):
                        removido = bot_data[tipo].pop(index)
                        send_message(chat_id, f"🗑️ Registro removido!")
                    else:
                        send_message(chat_id, "❌ Índice inválido")
                else:
                    send_message(chat_id, "❌ Use: `/del km 1`")
            except:
                send_message(chat_id, "❌ Use: `/del km 1`")
            
    except Exception as e:
        print(f"❌ Erro ao processar comando: {e}")

# ========== POLLING COM PROTEÇÃO CONTRA CONFLITOS ==========
def polling_loop():
    print("🔄 Iniciando polling manual...")
    offset = 0
    consecutive_errors = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 10, "limit": 1}  # Limite menor para evitar conflitos
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data.get("ok"):
                consecutive_errors = 0  # Reset error counter
                updates = data.get("result", [])
                for update in updates:
                    process_command(update)
                    offset = update["update_id"] + 1
            else:
                error_code = data.get("error_code")
                if error_code == 409:  # Conflict - outra instância rodando
                    print("⚠️  Outra instância detectada. Aguardando...")
                    time.sleep(30)  # Espera mais tempo
                    consecutive_errors += 1
                else:
                    print(f"❌ Erro na API: {data}")
                    consecutive_errors += 1
                
                # Se muitos erros consecutivos, espera mais tempo
                if consecutive_errors >= 3:
                    print("💤 Muitos erros, aguardando 60 segundos...")
                    time.sleep(60)
                    consecutive_errors = 0
                
        except requests.exceptions.Timeout:
            continue  # Timeout é normal, continua
        except Exception as e:
            print(f"❌ Erro no polling: {e}")
            consecutive_errors += 1
            time.sleep(10)

# ========== HTTP SERVER ==========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        return  # Silencia os logs

def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    print(f"🌐 HTTP Server rodando na porta {PORT}")
    server.serve_forever()

# ========== INICIALIZAÇÃO ==========
if __name__ == "__main__":
    # Iniciar HTTP Server em thread separada
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Iniciar polling
    polling_loop()
