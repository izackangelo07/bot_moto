from database import bot_data, save_to_gist
from utils import send_message, format_date, get_last_km, check_oil_change_alert, send_document, get_last_oil_change
from reports import generate_report, generate_pdf
from config import DELETE_PASSWORD, NOTIFICATION_CHAT_ID
import pytz
from datetime import datetime

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
                "• /pdf — Gera relatório completo em PDF\n"
                "• /statusoleo — Status da troca de óleo\n\n"
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
            # Mostrar status da troca de óleo antes do report
            current_km = get_last_km()
            if current_km > 0:
                alert_msg = check_oil_change_alert(current_km)
                if alert_msg:
                    send_message(chat_id, alert_msg)
            #Envia o report
            send_message(chat_id, generate_report())
        
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
        
        # Comando /statusoleo - Mostra status completo do óleo
        elif text.startswith("/statusoleo"):
            try:
                current_km = get_last_km()
                last_oil_km = get_last_oil_change()
                
                if last_oil_km == 0:
                    send_message(chat_id, "⚠️ *STATUS ÓLEO:* Nenhuma troca de óleo registrada ainda!")
                    return
                
                km_since_last_oil = current_km - last_oil_km
                km_remaining = 1000 - km_since_last_oil
                
                status_msg = f"⚪ *STATUS ÓLEO* ⚪\n\n"
                status_msg += f"📏 *KM Atual:* {current_km} km\n"
                status_msg += f"🛢️ *Última Troca:* {last_oil_km} km\n"
                status_msg += f"🛣️ *KM Rodados:* {km_since_last_oil} km\n"
                status_msg += f"🎯 *KM Restantes:* {km_remaining} km\n\n"
                
                # Adicionar alerta baseado na situação
                if km_since_last_oil >= 1000:
                    status_msg += f"🚨 *SITUAÇÃO:* TROCA URGENTE! Já passou {km_since_last_oil}km"
                elif km_remaining <= 100:
                    status_msg += f"🔴 *SITUAÇÃO:* ALERTA CRÍTICO! Faltam {km_remaining}km"
                elif km_remaining <= 300:
                    status_msg += f"🟡 *SITUAÇÃO:* ALERTA! Faltam {km_remaining}km"
                elif km_remaining <= 500:
                    status_msg += f"🔵 *SITUAÇÃO:* LEMBRETE! Faltam {km_remaining}km"
                else:
                    status_msg += f"✅ *SITUAÇÃO:* Tudo em ordem! Próxima troca em {km_remaining}km"
                
                send_message(chat_id, status_msg)
                
            except Exception as e:
                send_message(chat_id, f"❌ Erro ao verificar status do óleo: {e}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
