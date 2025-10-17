import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time
from datetime import datetime

print("🚀 BOT MOTOMANUTENÇÃO - COM GITHUB GIST")

# ========== CONFIGURAÇÃO ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
PORT = int(os.environ.get("PORT", 8080))

print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"✅ GitHub Token: {GITHUB_TOKEN[:10]}..." if GITHUB_TOKEN else "❌ GitHub Token não configurado")
print(f"✅ Gist ID: {GIST_ID}" if GIST_ID else "❌ Gist ID não configurado")

# ========== GITHUB GIST FUNCTIONS ==========
def load_from_gist():
    """Carrega dados do Gist"""
    if not GITHUB_TOKEN or not GIST_ID:
        print("⚠️  Gist não configurado, usando memória")
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
            content = gist_data["files"]["moto_data.json"]["content"]
            loaded_data = json.loads(content)
            print("✅ Dados carregados do Gist")
            return loaded_data
        else:
            print(f"❌ Erro ao carregar Gist: {response.status_code}")
            return {"km": [], "fuel": [], "maintenance": []}
    except Exception as e:
        print(f"❌ Erro ao carregar do Gist: {e}")
        return {"km": [], "fuel": [], "maintenance": []}

def save_to_gist(data):
    """Salva dados no Gist"""
    if not GITHUB_TOKEN or not GIST_ID:
        print("⚠️  Gist não configurado, dados apenas em memória")
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
        if response.status_code == 200:
            print("✅ Dados salvos no Gist")
            return True
        else:
            print(f"❌ Erro ao salvar no Gist: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao salvar no Gist: {e}")
        return False

# ========== INICIALIZAR DADOS ==========
print("📂 Carregando dados do Gist...")
bot_data = load_from_gist()

# ========== FUNÇÕES DO BOT ==========
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass

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
                "✅ *SISTEMA COM BACKUP AUTOMÁTICO*\n\n"
                "📋 Comandos:\n"
                "• `/addkm 15000`\n"
                "• `/fuel 10 5.50`\n"
                "• `/maint Troca de óleo`\n"
                "• `/report`\n"
                "• `/del km 1`\n"
                "• `/meuid`\n"
                "• `/backup` - Forçar backup\n"
                "• `/status` - Status do sistema"
            )
        
        elif text.startswith("/addkm"):
            try:
                km_value = int(text.split()[1])
                bot_data["km"].append({"km": km_value, "date": format_date()})
                if save_to_gist(bot_data):
                    send_message(chat_id, f"✅ KM registrado: {km_value} km")
                else:
                    send_message(chat_id, f"⚠️ KM registrado: {km_value} km (backup falhou)")
            except:
                send_message(chat_id, "❌ Use: `/addkm 15000`")
        
        elif text.startswith("/fuel"):
            try:
                parts = text.split()
                liters = float(parts[1])
                price = float(parts[2])
                bot_data["fuel"].append({"liters": liters, "price": price, "date": format_date()})
                if save_to_gist(bot_data):
                    send_message(chat_id, f"⛽ Abastecimento: {liters}L a R$ {price:.2f}")
                else:
                    send_message(chat_id, f"⚠️ Abastecimento: {liters}L a R$ {price:.2f} (backup falhou)")
            except:
                send_message(chat_id, "❌ Use: `/fuel 10 5.50`")
        
        elif text.startswith("/maint"):
            try:
                desc = " ".join(text.split()[1:])
                if desc:
                    bot_data["maintenance"].append({"desc": desc, "date": format_date()})
                    if save_to_gist(bot_data):
                        send_message(chat_id, f"🧰 Manutenção registrada: {desc}")
                    else:
                        send_message(chat_id, f"⚠️ Manutenção registrada: {desc} (backup falhou)")
                else:
                    send_message(chat_id, "❌ Use: `/maint Troca de óleo`")
            except:
                send_message(chat_id, "❌ Use: `/maint Troca de óleo`")
        
        elif text.startswith("/report"):
            msg = "🏍️ *RELATÓRIO*\n\n"
            
            # KM
            msg += "📏 *KM:*\n"
            if bot_data["km"]:
                for item in bot_data["km"][-10:]:
                    msg += f"• {item['date']} - {item['km']} km\n"
            else:
                msg += "Nenhum registro\n"
            
            # Abastecimentos
            msg += "\n⛽ *Abastecimentos:*\n"
            if bot_data["fuel"]:
                total_litros = sum(item['liters'] for item in bot_data["fuel"])
                total_gasto = sum(item['liters'] * item['price'] for item in bot_data["fuel"])
                for item in bot_data["fuel"][-10:]:
                    msg += f"• {item['date']} - {item['liters']}L a R$ {item['price']:.2f}\n"
                msg += f"\n📊 Total: {total_litros:.1f}L | R$ {total_gasto:.2f}\n"
            else:
                msg += "Nenhum registro\n"
            
            # Manutenções
            msg += "\n🧰 *Manutenções:*\n"
            if bot_data["maintenance"]:
                for item in bot_data["maintenance"][-10:]:
                    msg += f"• {item['date']} - {item['desc']}\n"
            else:
                msg += "Nenhum registro\n"
            
            send_message(chat_id, msg)
        
        elif text.startswith("/meuid"):
            send_message(chat_id, f"🆔 Seu ID: `{chat_id}`")
        
        elif text.startswith("/backup"):
            if save_to_gist(bot_data):
                send_message(chat_id, "💾 Backup realizado com sucesso!")
            else:
                send_message(chat_id, "❌ Falha no backup!")
        
        elif text.startswith("/status"):
            status_msg = "📊 *STATUS DO SISTEMA*\n\n"
            status_msg += f"📏 KM registrados: {len(bot_data['km'])}\n"
            status_msg += f"⛽ Abastecimentos: {len(bot_data['fuel'])}\n"
            status_msg += f"🧰 Manutenções: {len(bot_data['maintenance'])}\n"
            status_msg += f"🔧 Backup: {'✅ Ativo' if GITHUB_TOKEN and GIST_ID else '❌ Inativo'}\n"
            send_message(chat_id, status_msg)
        
        elif text.startswith("/del"):
            try:
                parts = text.split()
                if len(parts) >= 3:
                    tipo = parts[1]
                    index = int(parts[2]) - 1
                    
                    if tipo in ["km", "fuel", "maint"] and 0 <= index < len(bot_data[tipo]):
                        bot_data[tipo].pop(index)
                        if save_to_gist(bot_data):
                            send_message(chat_id, f"🗑️ Registro removido!")
                        else:
                            send_message(chat_id, f"⚠️ Registro removido (backup falhou)")
                    else:
                        send_message(chat_id, "❌ Índice inválido")
                else:
                    send_message(chat_id, "❌ Use: `/del km 1`")
            except:
                send_message(chat_id, "❌ Use: `/del km 1`")
            
    except Exception as e:
        print(f"❌ Erro ao processar comando: {e}")

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
                    print("⚠️  Outra instância detectada. Aguardando...")
                    time.sleep(30)
                else:
                    time.sleep(10)
                
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            print(f"❌ Erro no polling: {e}")
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
