import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from database import bot_data
from utils import total_fuel_por_mes, total_fuel_geral

def generate_pdf():
    """
    Gera PDF completo com layout personalizado:
    - Título centralizado
    - Gastos totais
    - Gastos mensais por TODOS os meses do ano atual
    - Abastecimentos
    - Manutenções
    - KM
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30, leftMargin=30, rightMargin=30)
        styles = getSampleStyleSheet()

        # Estilos
        title_style = ParagraphStyle(
            'Title',
            fontSize=16,
            alignment=1,
            textColor=colors.darkblue,
            spaceAfter=20
        )

        section_style = ParagraphStyle(
            'Section',
            fontSize=12,
            spaceAfter=10,
            textColor=colors.black,
            leading=14
        )

        text_style = ParagraphStyle(
            'Text',
            fontSize=10,
            leading=14,
            spaceAfter=4
        )

        story = []

        # TÍTULO
        story.append(Paragraph("■■ RELATÓRIO COMPLETO - POPzinha", title_style))

        # Data
        data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
        story.append(Paragraph(f"Gerado em: {data_geracao}", text_style))
        story.append(Spacer(1, 12))

        # --------------------------
        # GASTOS TOTAIS
        # --------------------------
        total_geral = total_fuel_geral()
        total_manu = sum(item.get('price', 0.0) for item in bot_data["manu"])

        story.append(Paragraph("■ GASTO TOTAL COMBUSTÍVEL", section_style))
        story.append(Paragraph(f"Total: R$ {total_geral:.2f}", text_style))
        story.append(Spacer(1, 6))

        story.append(Paragraph("■ GASTO TOTAL MANUTENÇÃO", section_style))
        story.append(Paragraph(f"Total: R$ {total_manu:.2f}", text_style))
        story.append(Spacer(1, 10))

        # --------------------------
        # GASTO MENSAL — TODOS OS MESES
        # --------------------------
        meses_pt = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }

        ano_atual = datetime.now().year

        # Cálculo dos gastos mensais
        gastos_mensais = {mes: 0.0 for mes in range(1, 13)}

        for item in bot_data["fuel"]:
            try:
                data_str = item['date'].split(' às ')[0]
                dia, mes, ano = map(int, data_str.split('/'))
                ano_completo = 2000 + ano
                if ano_completo == ano_atual:
                    gastos_mensais[mes] += item['price']
            except:
                pass

        story.append(Paragraph("■ GASTO MENSAL COMBUSTÍVEL", section_style))

        for mes in range(1, 12 + 1):
            nome = meses_pt[mes]
            total_mes = gastos_mensais[mes]
            story.append(Paragraph(f"■ Período: ({nome})", text_style))
            story.append(Paragraph(f"Total: R$ {total_mes:.2f}", text_style))
            story.append(Spacer(1, 4))

        story.append(Spacer(1, 10))

        # --------------------------
        # ABASTECIMENTOS
        # --------------------------
        story.append(Paragraph("■ Abastecimentos:", section_style))

        if bot_data["fuel"]:
            for i, item in enumerate(bot_data["fuel"], 1):
                story.append(Paragraph(
                    f"{i}. {item['liters']}L por R${item['price']:.2f} |{item['date']}|",
                    text_style
                ))
        else:
            story.append(Paragraph("Nenhum registro", text_style))

        story.append(Spacer(1, 10))

        # --------------------------
        # MANUTENÇÕES
        # --------------------------
        story.append(Paragraph("■ Manutenções:", section_style))

        if bot_data["manu"]:
            sorted_manu = sorted(bot_data["manu"], key=lambda x: x["km"])
            for i, item in enumerate(sorted_manu, 1):
                story.append(Paragraph(
                    f"{i}. {item['desc']} | R$ {item['price']:.2f} | {item['km']} Km |{item['date']}|",
                    text_style
                ))
        else:
            story.append(Paragraph("Nenhum registro", text_style))

        story.append(Spacer(1, 10))

        # --------------------------
        # KM
        # --------------------------
        story.append(Paragraph("■ KM:", section_style))

        if bot_data["km"]:
            sorted_km = sorted(bot_data["km"], key=lambda x: x["km"])
            for i, item in enumerate(sorted_km, 1):
                story.append(Paragraph(
                    f"{i}. {item['km']} Km |{item['date']}|",
                    text_style
                ))
        else:
            story.append(Paragraph("Nenhum registro", text_style))

        # --------------------------
        # GERAR PDF
        # --------------------------
        doc.build(story)
        buffer.seek(0)
        return buffer

    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")
        return None

def generate_report():
    """
    Gera relatório resumido para o Telegram
    Mostra apenas os últimos 4 registros de cada categoria
    Inclui gastos mensais e totais
    """
    msg = "🏍️ *RELATÓRIO*\n\n"
    
    # Cálculo de gastos
    total_mes = total_fuel_por_mes()
    total_geral = total_fuel_geral()
    total_manu = sum(item.get('price', 0.0) for item in bot_data["manu"])
    
    now = datetime.now()
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    nome_mes = meses_pt.get(now.month, now.strftime("%B"))
    
    # Seção de KM (últimos 4 registros) - ORDENADO POR KM
    msg += "📏 *KM (últimos 4):*\n"
    if bot_data["km"]:
        # Ordenar por KM e pegar últimos 4
        sorted_km = sorted(bot_data["km"], key=lambda x: x["km"])
        last_km = sorted_km[-4:]
        start_index = len(bot_data["km"]) - len(last_km) + 1
        for i, item in enumerate(last_km, start_index):
            msg += f"{i}. {item['km']} Km |{item['date']}|\n"
    else:
        msg += "Nenhum registro\n"

    # Seção de Manutenções (últimas 4) - ORDENADO POR KM
    msg += "\n🧰 *Manutenções (últimas 4):*\n"
    if bot_data["manu"]:
        # Ordenar por KM e pegar últimas 4
        sorted_manu = sorted(bot_data["manu"], key=lambda x: x["km"])
        last_manu = sorted_manu[-4:]
        start_index = len(bot_data["manu"]) - len(last_manu) + 1
        for i, item in enumerate(last_manu, start_index):
            price = item.get('price', 0.0)
            msg += f"{i}. {item['desc']} | R$ {price:.2f} | {item['km']} Km |{item['date']}|\n"
    else:
        msg += "Nenhum registro\n"
    
    # Seção de Abastecimentos (últimos 4)
    msg += "\n⛽ *Abastecimentos (últimos 4):*\n"
    if bot_data["fuel"]:
        last_fuel = bot_data["fuel"][-4:]
        start_index = len(bot_data["fuel"]) - len(last_fuel) + 1
        for i, item in enumerate(last_fuel, start_index):
            msg += f"{i}. {item['liters']}L por R${item['price']:.2f} |{item['date']}|\n"
    else:
        msg += "Nenhum registro\n"

    # Seção de Gastos
    msg += f"\n💰 *GASTO MENSAL COMBUSTÍVEL* \n"
    msg += f"📅*Período:*({nome_mes})\n"
    msg += f"Total: R$ {total_mes:.2f}\n\n"
    
    msg += f"💰 *GASTO TOTAL COMBUSTÍVEL*\n"
    msg += f"Total: R$ {total_geral:.2f}\n\n"
    
    msg += f"💰 *GASTO TOTAL MANUTENÇÃO*\n"
    msg += f"Total: R$ {total_manu:.2f}"

    return msg
