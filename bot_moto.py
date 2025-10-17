import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time
from datetime import datetime

print("🚀 BOT MOTOMANUTENÇÃO - GITHUB GIST")

# ========== CONFIGURAÇÃO ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
PORT = int(os.environ.get("PORT", 8080))

# Limpar URL do Gist_ID se necessário
if GIST_ID and "github.com" in GIST_ID:
    GIST_ID = GIST_ID.split("/")[-1]

print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"✅ GitHub Token: {GITHUB_TOKEN[:10]}..." if GITHUB_TOKEN else "❌ GitHub Token")
print(f"✅ Gist ID: {GIST_ID}" if GIST_ID else "❌ Gist ID")

# ========== GITHUB GIST FUNCTIONS ==========
def load_from_gist():
    """Carrega dados do Gist"""
    if not GITHUB_TOKEN or not GIST_ID:
        return {"km": [], "fuel": [], "maintenance": []}
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            gist_data = response.json()
            files = gist_data.get("files", {})
            if "moto_data.json" in files:
                content = files["moto_data.json"]["content"]
                return json.loads(content)
        return {"km": [], "fuel": [], "maintenance": []}
    except:
        return {"km": [], "fuel": [], "maintenance": []}

def save_to_gist(data):
    """Salva dados no Gist"""
    if not GITHUB_TOKEN or not GIST_ID:
        return False
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "files": {
                "moto_data.json": {
                    "content": json.dumps(data, indent=2, ensure_ascii=False)
                }
            }
        }
        
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

# ========== INICIALIZAR DADOS ==========
print("📂 Carregando dados...")
bot_data = load_from_gist()
print(f"📊 Dados: {len(bot_data['km'])} KM, {len(bot_data['fuel'])} abastecimentos")

# ========== FUNÇÕES DO BOT ==========
def send_message(chat_id, text):
    """Função simplificada - só precisa do chat_id para responder"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass

def format_date():
    now = datetime.now()
    return f"|{now.day:02d}/{now.month:02d}/{str(now.year)[-2:]} às {now.hour:02d}:{now.minute:02d}|"

def process_command(update):
    try:
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not chat_id or not text:
            return
        
        print(f"📨 Comando: {text}")
        
        if text.startswith("/start"):
            send_message(chat_id,
                "🏍️ *BOT MOTOMANUTENÇÃO*\n\n"
                "📊 *REGISTROS:*\n"
                "• /addkm KMsAtuais — Define os KMs Atuais\n"
                "• /fuel Litros Valor — Registra abastecimento\n"
                "• /maint Descrição KM — Registra manutenção\n\n"
                "📋 *CONSULTAS:*\n"
                "• /report — Resumo geral\n\n"
                "⚙️ *GERENCIAMENTO:*\n"
                "• /del km Índice — Deleta KM\n"
                "• /del fuel Índice — Deleta abastecimento\n"
                "• /del maint Índice — Deleta manutenção\n\n"
                "💡 *Dica:* Clique e Segure nos comandos para usar!"
            )
        
        elif text.startswith("/addkm"):
            try:
                km_value = int(text.split()[1])
                bot_data["km"].append({"km": km_value, "date": format_date()})
                save_to_gist(bot_data)
                send_message(chat_id, f"✅ KM registrado: {km_value} km")
            except:
                send_message(chat_id, "❌ Use: `/addkm 15000`")
        
        elif text.startswith("/fuel"):
            try:
                parts = text.split()
                liters = float(parts[1])
                price = float(parts[2])
                bot_data["fuel"].append({"liters": liters, "price": price, "date": format_date()})
                save_to_gist(bot_data)
                send_message(chat_id, f"⛽ Abastecimento: {liters}L a R$ {price:.2f}")
            except:
                send_message(chat_id, "❌ Use: `/fuel 10 5.50`")
        
        elif text.startswith("/maint"):
            try:
                parts = text.split()
                if len(parts) >= 3:
                    # Pega a descrição (tudo menos o último argumento)
                    desc = " ".join(parts[1:-1])
                    km_value = int(parts[-1])  # Último argumento é o KM
                    
                    bot_data["maintenance"].append({
                        "desc": desc, 
                        "date": format_date(),
                        "km": km_value
                    })
                    save_to_gist(bot_data)
                    send_message(chat_id, f"🧰 Manutenção registrada: {desc} | {km_value} Km")
                else:
                    send_message(chat_id, "❌ Use: `/maint Descrição KM`\nEx: `/maint Troca de óleo 15000`")
            except:
                send_message(chat_id, "❌ Use: `/maint Descrição KM`\nEx: `/maint Troca de óleo 15000`")
        
        elif text.startswith("/report"):
            msg = "🏍️ *RELATÓRIO*\n\n"
            
            # KM - Com "|" corrigido
            msg += "📏 *KM:*\n"
            if bot_data["km"]:
                for i, item in enumerate(bot_data["km"][-10:], 1):
                    msg += f"{i}. {item['date']}|{item['km']} Km\n"
            else:
                msg += "Nenhum registro\n"
            
            # Abastecimentos - Sem total
            msg += "\n⛽ *Abastecimentos:*\n"
            if bot_data["fuel"]:
                for i, item in enumerate(bot_data["fuel"][-10:], 1):
                    msg += f"{i}. {item['date']}{item['liters']}L por R${item['price']:.2f}\n"
            else:
                msg += "Nenhum registro\n"
            
            # Manutenções - Com KM específico
            msg += "\n🧰 *Manutenções:*\n"
            if bot_data["maintenance"]:
                for i, item in enumerate(bot_data["maintenance"][-10:], 1):
                    msg += f"{i}. {item['date']}{item['desc']}|{item['km']} Km\n"
            else:
                msg += "Nenhum registro\n"
            
            send_message(chat_id, msg)
        
        elif text.startswith("/del"):
            try:
                parts = text.split()
                if len(parts) >= 3:
                    tipo = parts[1]
                    index = int(parts[2]) - 1
                    
                    if tipo in ["km", "fuel", "maint"] and 0 <= index < len(bot_data[tipo]):
                        bot_data[tipo].pop(index)
                        save_to_gist(bot_data)
                        send_message(chat_id, f"🗑️ Registro removido!")
                    else:
                        send_message(chat_id, "❌ Índice inválido")
                else:
                    # Mensagem de erro específica para cada tipo
                    if len(parts) == 2:
                        tipo = parts[1]
                        if tipo in ["km", "fuel", "maint"]:
                            send_message(chat_id, f"❌ Use: `/del {tipo} 1`")
                        else:
                            send_message(chat_id, "❌ Tipo inválido. Use: km, fuel ou maint")
                    else:
                        send_message(chat_id, "❌ Use: `/del km 1` ou `/del fuel 1` ou `/del maint 1`")
            except Exception as e:
                print(f"❌ Erro no /del: {e}")
                send_message(chat_id, "❌ Use: `/del km 1` ou `/del fuel 1` ou `/del maint 1`")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

# ========== POLLING ==========
def polling_loop():
    print("🔄 Iniciando polling...")
    offset = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 10, "limit": 1}
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data.get("ok"):
                updates = data.get("result", [])
                for update in updates:
                    process_command(update)
                    offset = update["update_id"] + 1
            else:
                if data.get("error_code") == 409:
                    time.sleep(30)
                else:
                    time.sleep(10)
                
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            print(f"❌ Erro: {e}")
            time.sleep(10)

# ========== HTTP SERVER ==========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    def log_message(self, format, *args):
        return

def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    print(f"🌐 HTTP Server rodando na porta {PORT}")
    server.serve_forever()

# ========== INICIALIZAÇÃO ==========
if __name__ == "__main__":
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    polling_loop()
