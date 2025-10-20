from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from config import PORT
from database import load_from_gist
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

if __name__ == "__main__":
    print("🚀 Iniciando Bot de Manutenção - POPzinha")
    
    # Carregar dados iniciais
    load_from_gist()
    
    # Iniciar servidor HTTP em thread separada
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Iniciar agendador de notificações em thread separada
    notification_thread = Thread(target=notification_scheduler, daemon=True)
    notification_thread.start()
    print("🔔 Agendador de notificações iniciado")
    
    # Iniciar loop principal de polling
    print("🔄 Iniciando sistema de polling...")
    polling_loop()
