from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from config import PORT
from database import load_from_gist, get_bot_data, update_bot_data
from notifications import notification_scheduler
from polling import polling_loop

# ========== SERVIDOR WEB PARA HEALTH CHECK ==========

class HealthHandler(BaseHTTPRequestHandler):
    """
    Handler simples para health checks
    Retorna status 200 para verificações de saúde
    """
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')
    
    def log_message(self, format, *args):
        """Suprime logs do servidor HTTP"""
        return

def start_http_server():
    """
    Inicia servidor HTTP simples para health checks
    Necessário para plataformas de hospedagem como Railway
    """
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    print(f"🌐 HTTP Server rodando na porta {PORT}")
    server.serve_forever()

# ========== INICIALIZAÇÃO DO SISTEMA ==========

def start():
    print("🚀 Iniciando Bot de Manutenção - POPzinha")

    print("📂 Iniciando carregamento de dados...")
    load_from_gist()

    bot_data = get_bot_data()
    
    if bot_data and len(bot_data["km"]) > 0:
        print(f"🎉 Dados carregados! KM atual: {bot_data['km'][-1]['km']}")
    else:
        print("⚠️ Nenhum dado carregado ou Gist vazio")
    
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    notification_thread = Thread(target=notification_scheduler, daemon=True)
    notification_thread.start()
    
    print("🔔 Agendador de notificações iniciado")

    print("🔄 Iniciando sistema de polling...")
    polling_loop()
