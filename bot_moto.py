import os
import json
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import time
from datetime import datetime, time as dt_time
import pytz
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# ========== INICIALIZAÇÃO E CONFIGURAÇÃO ==========
print("🚀 BOT MANUTENÇÃO - MOTO - GITHUB GIST")

# Configurações das variáveis de ambiente
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Token do bot do Telegram
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Token de acesso do GitHub
GIST_ID = os.getenv("GIST_ID")  # ID do Gist para armazenar dados
PORT = int(os.environ.get("PORT", 8080))  # Porta do servidor web
DELETE_PASSWORD = os.getenv("DELETE_PASSWORD", "123456")  # Senha para deletar todos os dados
NOTIFICATION_CHAT_ID = os.getenv("NOTIFICATION_CHAT_ID")  # Chat ID para notificações automáticas

# Limpar URL do Gist se fornecida como URL completa
if GIST_ID and "github.com" in GIST_ID:
    GIST_ID = GIST_ID.split("/")[-1]

# Log das configurações (ocultando informações sensíveis)
print(f"✅ Bot Token: {BOT_TOKEN[:10]}...")
print(f"✅ GitHub Token: {GITHUB_TOKEN[:10]}..." if GITHUB_TOKEN else "❌ GitHub Token")
print(f"✅ Gist ID: {GIST_ID}" if GIST_ID else "❌ Gist ID")
print(f"✅ Delete Password: {DELETE_PASSWORD[:2]}..." if DELETE_PASSWORD else "❌ Delete Password")
print(f"✅ Notification Chat ID: {NOTIFICATION_CHAT_ID}" if NOTIFICATION_CHAT_ID else "❌ Notification Chat ID")

# ========== FUNÇÕES DE GITHUB GIST ==========

def load_from_gist():
    """
    Carrega os dados do Gist do GitHub
    Retorna dicionário com listas vazias se não conseguir carregar
    """
    if not GITHUB_TOKEN or not GIST_ID:
        return {"km": [], "fuel": [], "manu": []}
    
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
        return {"km": [], "fuel": [], "manu": []}
    except:
        return {"km": [], "fuel": [], "manu": []}

def save_to_gist(data):
    """
    Salva os dados no Gist do GitHub
    Retorna True se salvou com sucesso, False se falhou
    """
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

# ========== CARREGAMENTO INICIAL DOS DADOS ==========
print("📂 Carregando dados...")
bot_data = load_from_gist()
print(f"📊 Dados: {len(bot_data['km'])} KM, {len(bot_data['fuel'])} abastecimentos, {len(bot_data['manu'])} manutenções")

# ========== FUNÇÕES PRINCIPAIS DO BOT ==========

def send_message(chat_id, text):
    """
    Envia mensagem para um chat específico do Telegram
    Usa parse_mode Markdown para formatação
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=data, timeout=5)
    except:
        pass

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
    
    # Sistema de alertas progressivos
    if km_since_last_oil >= 1000:
        return f"* PASSOU DA HORA - {km_since_last_oil}KM RODADOS*!\n     🚨TROQUE O ÓLEO AGORA!🚨"
    elif km_remaining <= 100:
        return f"🔴*ALERTA CRÍTICO:* FALTAM APENAS {km_remaining}KM PARA TROCAR O ÓLEO!🔴"
    elif km_remaining <= 300:
        return f"🟡*ALERTA:* FALTAM {km_remaining}KM PARA TROCAR O ÓLEO🟡"
    elif km_remaining <= 500:
        return f"🔵*LEMBRETE:* FALTAM {km_remaining}KM PARA TROCAR O ÓLEO🔵"
    
    return None

def send_daily_notification():
    """
    Envia notificação diária sobre status do óleo
    Só envia se houver um alerta ativo e chat ID configurado
    """
    if not NOTIFICATION_CHAT_ID:
        return
    
    try:
        current_km = get_last_km()
        if current_km > 0:
            alert_msg = check_oil_change_alert(current_km)
            if alert_msg:
                notification = f" ```      🔔 MANUTENÇÃO POPzinha 🔔 ```\n{alert_msg}"
                send_message(NOTIFICATION_CHAT_ID, notification)
                print(f"✅ Notificação enviada para chat {NOTIFICATION_CHAT_ID}")
    except Exception as e:
        print(f"❌ Erro na notificação: {e}")

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

def generate_pdf():
    """
    Gera um PDF completo com todos os registros
    Inclui KM, manutenções, abastecimentos e gastos
    Retorna buffer do PDF ou None em caso de erro
    """
    try:
        # Criar buffer para o PDF
        buffer = io.BytesIO()
        
        # Configurar documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30)
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=6
        )
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Normal'],
            fontSize=14,
            alignment=1,
            spaceAfter=20,
            textColor=colors.darkblue
        )
        
        # Conteúdo do PDF
        story = []
        
        # Título
        story.append(Paragraph("✅ RELATÓRIO DE MANUTENÇÃO - POPzinha", title_style))
        story.append(Spacer(1, 10))
        
        # Data de geração
        data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
        story.append(Paragraph(f"Gerado em: {data_geracao}", normal_style))
        story.append(Spacer(1, 20))
        
        # Gastos
        total_mes = total_fuel_mes()
        total_geral = total_fuel_geral()
        
        now = datetime.now()
        meses_pt = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        nome_mes = meses_pt.get(now.month, now.strftime("%B"))
        
        # Seção de KM (todos os registros)
        story.append(Paragraph("<b>✅ KM:</b>", normal_style))
        if bot_data["km"]:
            for i, item in enumerate(bot_data["km"], 1):
                story.append(Paragraph(f"{i}. {item['km']} Km |{item['date']}|", normal_style))
        else:
            story.append(Paragraph("Nenhum registro", normal_style))
        
        story.append(Spacer(1, 10))
        
        # Seção de Manutenções (todos os registros)
        story.append(Paragraph("<b>✅ Manutenções:</b>", normal_style))
        if bot_data["manu"]:
            for i, item in enumerate(bot_data["manu"], 1):
                story.append(Paragraph(f"{i}. {item['desc']} | {item['km']} Km |{item['date']}|", normal_style))
        else:
            story.append(Paragraph("Nenhum registro", normal_style))
        
        story.append(Spacer(1, 10))
        
        # Seção de Abastecimentos (todos os registros)
        story.append(Paragraph("<b>✅ Abastecimentos:</b>", normal_style))
        if bot_data["fuel"]:
            for i, item in enumerate(bot_data["fuel"], 1):
                story.append(Paragraph(f"{i}. {item['liters']}L por R${item['price']:.2f} |{item['date']}|", normal_style))
        else:
            story.append(Paragraph("Nenhum registro", normal_style))
        
        story.append(Spacer(1, 15))
        
        # Seção de Gastos
        story.append(Paragraph(f"<b>✅ GASTO MENSAL  ✅ Período: ({nome_mes})</b>", normal_style))
        story.append(Paragraph(f"Total: R$ {total_mes:.2f}", normal_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph("<b>✅ GASTO TOTAL</b>", normal_style))
        story.append(Paragraph(f"Total: R$ {total_geral:.2f}", normal_style))
        
        # Gerar PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        return None

def generate_report():
    """
    Gera relatório resumido para o Telegram
    Mostra apenas os últimos 5 registros de cada categoria
    Inclui gastos mensais e totais
    """
    msg = "🏍️ *RELATÓRIO*\n\n"
    
    # Cálculo de gastos
    total_mes = total_fuel_mes()
    total_geral = total_fuel_geral()
    
    now = datetime.now()
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    nome_mes = meses_pt.get(now.month, now.strftime("%B"))
    
    # Seção de KM (últimos 5 registros)
    msg += "📏 *KM (últimos 5):*\n"
    if bot_data["km"]:
        last_km = bot_data["km"][-5:]
        start_index = len(bot_data["km"]) - len(last_km) + 1
        for i, item in enumerate(last_km, start_index):
            msg += f"{i}. {item['km']} Km |{item['date']}|\n"
    else:
        msg += "Nenhum registro\n"

    # Seção de Manutenções (últimas 5)
    msg += "\n🧰 *Manutenções (últimas 5):*\n"
    if bot_data["manu"]:
        last_manu = bot_data["manu"][-5:]
        start_index = len(bot_data["manu"]) - len(last_manu) + 1
        for i, item in enumerate(last_manu, start_index):
            msg += f"{i}. {item['desc']} | {item['km']} Km |{item['date']}|\n"
    else:
        msg += "Nenhum registro\n"
    
    # Seção de Abastecimentos (últimos 5)
    msg += "\n⛽ *Abastecimentos (últimos 5):*\n"
    if bot_data["fuel"]:
        last_fuel = bot_data["fuel"][-5:]
        start_index = len(bot_data["fuel"]) - len(last_fuel) + 1
        for i, item in enumerate(last_fuel, start_index):
            msg += f"{i}. {item['liters']}L por R${item['price']:.2f} |{item['date']}|\n"
    else:
        msg += "Nenhum registro\n"

    # Seção de Gastos
    msg += f"\n💰 *GASTO MENSAL*  📅*Período*:({nome_mes})\nTotal: R$ {total_mes:.2f}\n\n"
    msg += f"💰 *GASTO TOTAL*\nTotal: R$ {total_geral:.2f}\n"

    return msg

def notification_scheduler():
    """
    Agendador de notificações diárias
    Verifica horários específicos (8:00 e 22:30) e envia notificações
    Controla para enviar apenas uma notificação por horário por dia
    """
    print("⏰ Iniciando agendador de notificações...")
    last_notification_hour = None
    
    while True:
        try:
            now = datetime.now(pytz.timezone('America/Sao_Paulo'))
            current_hour = now.hour
            current_minute = now.minute
            
            # Verificar horários configurados (8:00 e 22:30)
            if ((current_hour == 8 and current_minute == 0) or (current_hour == 20 and current_minute == 27)) and last_notification_hour != current_hour:
                print("🕗 Enviando notificação...")
                send_daily_notification()
                last_notification_hour = current_hour
                time.sleep(61)  # Evita múltiplos envios no mesmo minuto
            else:
                time.sleep(30)  # Verifica a cada 30 segundos
                
        except Exception as e:
            print(f"❌ Erro no agendador: {e}")
            time.sleep(60)

# ========== PROCESSAMENTO DE COMANDOS ==========

def process_command(update):
    """
    Processa comandos recebidos do Telegram
    Gerencia todos os comandos disponíveis no bot
    """
    try:
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not chat_id or not text:
            return
        
        print(f"📨 Comando: {text}")
        
        # Comando /start - Menu principal
        if text.startswith("/start"):
            send_message(chat_id,
                "🏍️ *BOT MANUTENÇÃO - POPzinha*\n\n"
                "📊 *REGISTROS:*\n"
                "• /addkm KMsAtuais — Define os KMs Atuais\n"
                "• /fuel Litros Valor — Registra abastecimento\n"
                "• /manu Descrição KM — Registra manutenção\n\n"
                "📋 *CONSULTAS:*\n"
                "• /report — Resumo geral (últimos 5 registros)\n"
                "• /pdf — Gera relatório completo em PDF\n\n"
                "⚙️ *GERENCIAMENTO:*\n"
                "• /del km Índice — Deleta KM\n"
                "• /del fuel Índice — Deleta abastecimento\n"
                "• /del manu Índice — Deleta manutenção\n\n"
                "🔔 *ALERTAS:*\n"
                "• Alertas automáticos para troca de óleo\n"
                "💡 *Dica:* Clique e segure nos comandos para usar!"
            )
        
        # Comando /delete - Apaga todos os dados (com senha)
        elif text.startswith("/delete"):
            try:
                parts = text.split()
                if len(parts) >= 2:
                    password = parts[1]
                    
                    if password == DELETE_PASSWORD:
                        # Confirmar antes de deletar tudo
                        total_km = len(bot_data["km"])
                        total_fuel = len(bot_data["fuel"])
                        total_manu = len(bot_data["manu"])
                        
                        # Limpar todos os dados
                        bot_data["km"] = []
                        bot_data["fuel"] = []
                        bot_data["manu"] = []
                        
                        if save_to_gist(bot_data):
                            send_message(chat_id, f"🗑️🚨 *TODOS OS DADOS FORAM DELETADOS!*\n\n"
                                                f"• {total_km} registros de KM removidos\n"
                                                f"• {total_fuel} abastecimentos removidos\n"
                                                f"• {total_manu} manutenções removidas\n\n"
                                                f"*SISTEMA REINICIADO*")
                        else:
                            send_message(chat_id, "❌ Erro ao salvar dados deletados no Gist")
                    else:
                        send_message(chat_id, "❌ Senha incorreta! Operação cancelada.")
                else:
                    send_message(chat_id, "❌ Use: `/delete SENHA`\n\n⚠️ *ATENÇÃO:* Este comando apaga TODOS os dados permanentemente!")
            except Exception as e:
                print(f"❌ Erro no /delete: {e}")
                send_message(chat_id, "❌ Use: `/delete SENHA`")
        
        # Comando /addkm - Registra novo quilometragem
        elif text.startswith("/addkm"):
            try:
                km_value = int(text.split()[1])
                last_km = get_last_km()
                if km_value == last_km:
                    send_message(chat_id, f"⚠️ KM {km_value} já é o último registrado")
                else:
                    bot_data["km"].append({"km": km_value, "date": format_date()})
                    save_to_gist(bot_data)
                    send_message(chat_id, f"✅ KM registrado: {km_value} km")

                    send_message(chat_id, generate_report())
                    
                    # Verificar alerta de troca de óleo
                    alert_msg = check_oil_change_alert(km_value)
                    if alert_msg:
                        send_message(chat_id, alert_msg)
                    
            except:
                send_message(chat_id, "❌ Use: `/addkm 15000`")
        
        # Comando /fuel - Registra abastecimento
        elif text.startswith("/fuel"):
            try:
                parts = text.split()
                liters = float(parts[1])
                price = float(parts[2])
                bot_data["fuel"].append({"liters": liters, "price": price, "date": format_date()})
                save_to_gist(bot_data)
                send_message(chat_id, f"⛽ Abastecimento: {liters}L a R$ {price:.2f}")
                send_message(chat_id, generate_report())
                
                # Verificar alerta de troca de óleo
                current_km = get_last_km()
                alert_msg = check_oil_change_alert(current_km)
                if alert_msg:
                    send_message(chat_id, alert_msg)
                        
            except:
                send_message(chat_id, "❌ Use: `/fuel 10 5.50`")
        
        # Comando /manu - Registra manutenção
        elif text.startswith("/manu"):
            try:
                parts = text.split()
                if len(parts) >= 3:
                    desc = " ".join(parts[1:-1])
                    km_value = int(parts[-1])
                    
                    last_km = get_last_km()
                    km_added = False
                    # Adiciona KM automaticamente se for diferente do último
                    if km_value != last_km:
                        bot_data["km"].append({"km": km_value, "date": format_date()})
                        km_added = True
                    
                    # Registrar manutenção
                    bot_data["manu"].append({
                        "desc": desc, 
                        "date": format_date(),
                        "km": km_value
                    })
                    
                    save_to_gist(bot_data)
                    
                    # Mensagem de confirmação
                    if km_added:
                        send_message(chat_id, f"🧰 Manutenção registrada: {desc} | {km_value} Km\n✅ KM registrado automaticamente")
                    else:
                        send_message(chat_id, f"🧰 Manutenção registrada: {desc} | {km_value} Km\nℹ️ KM já estava registrado")

                    send_message(chat_id, generate_report())
            
                    # Verificar se é troca de óleo
                    oil_keywords = ['óleo', 'oleo', 'OLEO', 'ÓLEO', 'Óleo']
                    if any(keyword.lower() in desc.lower() for keyword in oil_keywords):
                        send_message(chat_id, "🔧 *TROCA DE ÓLEO REGISTRADA! PRÓXIMO ALERTA EM 1000KM*")
                    else:
                        # Verificar alerta de troca de óleo
                        current_km = get_last_km()
                        alert_msg = check_oil_change_alert(current_km)
                        if alert_msg:
                            send_message(chat_id, alert_msg)
                else:
                    send_message(chat_id, "❌ Use: `/manu Descrição KM`\nEx: `/manu Troca de óleo 15000`")
            except:
                send_message(chat_id, "❌ Use: `/manu Descrição KM`\nEx: `/manu Troca de óleo 15000`")
        
        # Comando /report - Gera relatório resumido
        elif text.startswith("/report"):
            send_message(chat_id, generate_report())
            
            # Mostrar status da troca de óleo no report
            current_km = get_last_km()
            if current_km > 0:
                alert_msg = check_oil_change_alert(current_km)
                if alert_msg:
                    send_message(chat_id, alert_msg)
        
        # Comando /pdf - Gera e envia PDF completo
        elif text.startswith("/pdf"):
            send_message(chat_id, "📄 Gerando relatório completo em PDF...")
            pdf_buffer = generate_pdf()
            if pdf_buffer:
                # Nome do arquivo com data
                data_arquivo = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"relatorio_moto_{data_arquivo}.pdf"
                
                if send_document(chat_id, pdf_buffer, filename):
                    send_message(chat_id, "✅ PDF enviado com sucesso!")
                else:
                    send_message(chat_id, "❌ Erro ao enviar PDF")
            else:
                send_message(chat_id, "❌ Erro ao gerar PDF")
        
        # Comando /del - Deleta registros individuais
        elif text.startswith("/del"):
            try:
                parts = text.split()
                if len(parts) >= 3:
                    tipo = parts[1]
                    index = int(parts[2]) - 1
                    
                    if tipo in bot_data and 0 <= index < len(bot_data[tipo]):
                        bot_data[tipo].pop(index)
                        save_to_gist(bot_data)
                        send_message(chat_id, f"🗑️ Registro removido!")
                        send_message(chat_id, generate_report())
                    else:
                        send_message(chat_id, f"❌ Índice inválido para {tipo}. Use de 1 a {len(bot_data.get(tipo, []))}")
                else:
                    if len(parts) == 2:
                        tipo = parts[1]
                        if tipo in bot_data:
                            send_message(chat_id, f"❌ Use: `/del {tipo} 1`")
                        else:
                            send_message(chat_id, "❌ Tipo inválido. Use: km, fuel ou manu")
                    else:
                        send_message(chat_id, "❌ Use: `/del km 1` ou `/del fuel 1` ou `/del manu 1`")
            except Exception as e:
                print(f"❌ Erro no /del: {e}")
                send_message(chat_id, "❌ Use: `/del km 1` ou `/del fuel 1` ou `/del manu 1`")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

# ========== SISTEMA DE POLLING ==========

def polling_loop():
    """
    Loop principal de polling do Telegram
    Busca atualizações continuamente e processa comandos
    """
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
    # Iniciar servidor HTTP em thread separada
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Iniciar agendador de notificações em thread separada
    notification_thread = Thread(target=notification_scheduler, daemon=True)
    notification_thread.start()
    print("🔔 Agendador de notificações iniciado")
    
    # Iniciar loop principal de polling
    polling_loop()
