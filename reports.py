import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from database import bot_data
from utils import total_fuel_mes, total_fuel_geral

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
        
        # Seção de Manutenções (todos os registros) - AGORA COM PREÇO
        story.append(Paragraph("<b>✅ Manutenções:</b>", normal_style))
        if bot_data["manu"]:
            for i, item in enumerate(bot_data["manu"], 1):
                price = item.get('price', 0.0)
                story.append(Paragraph(f"{i}. {item['desc']} | R$ {price:.2f} | {item['km']} Km |{item['date']}|", normal_style))
        else:
            story.append(Paragraph("Nenhum registro", normal_style))
        
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

    # Seção de Manutenções (últimas 5) - AGORA COM PREÇO
    msg += "\n🧰 *Manutenções (últimas 5):*\n"
    if bot_data["manu"]:
        last_manu = bot_data["manu"][-5:]
        start_index = len(bot_data["manu"]) - len(last_manu) + 1
        for i, item in enumerate(last_manu, start_index):
            price = item.get('price', 0.0)
            msg += f"{i}. {item['desc']} | R$ {price:.2f} | {item['km']} Km |{item['date']}|\n"
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
