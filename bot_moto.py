import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time

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
                "🏍️ *BOT MOTOMANUTENÇÃO*\\n\\n"
                "📋 Comandos:\\n"
                "• `/addkm 15000`\\n"
                "• `/fuel 10 5.50`\\n"
                "• `/maint Troca de óleo`\\n"
                "• `/report`\\n"
                "• `/del km 1`"
            )
        
        elif text.startswith("/addkm"):
            try:
                km_value = int(text.split()[1])
                bot_data["km"].append({"km": km_value, "date": time.strftime("%d/%m %H:%M")})
                send_message(chat_id, f"✅ KM registrado: {km_value} km")
            except:
                send_message(chat_id, "❌ Use: `/addkm 15000`")
        
        elif text.startswith("/fuel"):
            try:
                parts = text.split()
                liters = float(parts[1])
                price = float(parts[2])
                bot_data["fuel"].append({"liters": liters, "price": price, "date": time.strftime("%d/%m %H:%M")})
                send_message(chat_id, f"⛽ Abastecimento: {liters}L a R$ {price:.2f}")
            except:
                send_message(chat_id, "❌ Use: `/fuel 10 5.50`")
        
        elif text.startswith("/report"):
            msg = "🏍️ *RELATÓRIO*\\n\\n"
            
            msg += "📏 *KM:*\\n"
            for item in bot_data["km"][-5:]:
                msg += f"• {item['date']} - {item['km']} km\\n"
            if not bot_data["km"]:
                msg += "Nenhum registro\\n"
            
            msg += "\\n⛽ *Abastecimentos:*\\n"
            for item in bot_data["fuel"][-5:]:
                msg += f"• {item['date']} - {item['liters']}L a R$ {item['price']:.2f}\\n"
            if not bot_data["fuel"]:
                msg += "Nenhum registro\\n"
            
            send_message(chat_id, msg)
        
        elif text.startswith("/meuid"):
            send_message(chat_id, f"🆔 Seu ID: `{chat_id}`")
            
    except Exception as e:
        print(f"❌ Erro ao processar comando: {e}")

# ========== POLLING MANUAL ==========
def polling_loop():
    print("🔄 Iniciando polling manual...")
    offset = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                updates = data.get("result", [])
                for update in updates:
                    process_command(update)
                    offset = update["update_id"] + 1
            else:
                print(f"❌ Erro na API: {data}")
                
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            print(f"❌ Erro no polling: {e}")
            time.sleep(5)

# ========== HTTP SERVER (para Railway) ==========
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
