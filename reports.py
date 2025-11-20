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
    Gera PDF no layout solicitado pelo usuário.
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=30)
        styles = getSampleStyleSheet()

        normal = ParagraphStyle(
            'normal',
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            spaceAfter=6
        )

        title = ParagraphStyle(
            'title',
            parent=styles["Normal"],
            fontSize=14,
            leading=18,
            alignment=1,
            spaceAfter=20,
            textColor=colors.black
        )

        header = ParagraphStyle(
            'header',
            parent=styles["Normal"],
            fontSize=12,
            leading=16,
            spaceAfter=10,
            textColor=colors.black
        )

        story = []

        # ===============================
        #   TÍTULO
        # ===============================
        story.append(Paragraph("■■ RELATÓRIO COMPLETO - POPzinha", title))

        data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")
        story.append(Paragraph(f"Gerado em: {data_geracao}", normal))
        story.append(Spacer(1, 12))

        # ===============================
        #   VALORES
        # ===============================
        total_mes = total_fuel_mes()
        total_geral = total_fuel_geral()
        total_manu = sum(item.get("price", 0.0) for item in bot_data["manu"])

        # Mês atual por extenso
        meses_pt = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        nome_mes = meses_pt.get(datetime.now().month, "Mês Atual")

        # TOT. COMBUSTÍVEL
        story.append(Paragraph("■ GASTO TOTAL COMBUSTÍVEL", header))
        story.append(Paragraph(f"Total: R$ {total_geral:.2f}", normal))
        story.append(Spacer(1, 8))

        # TOT. MANUTENÇÃO
        story.append(Paragraph("■ GASTO TOTAL MANUTENÇÃO", header))
        story.append(Paragraph(f"Total: R$ {total_manu:.2f}", normal))
        story.append(Spacer(1, 8))

        # MENSAL COMBUSTÍVEL
        story.append(Paragraph("■ GASTO MENSAL COMBUSTÍVEL", header))
        story.append(Paragraph(f"■Período: ({nome_mes})", normal))
        story.append(Paragraph(f"Total: R$ {total_mes:.2f}", normal))
        story.append(Spacer(1, 12))

        # ===============================
        #   ABASTECIMENTOS
        # ===============================
        story.append(Paragraph("■ Abastecimentos:", header))

        if bot_data["fuel"]:
            for i, item in enumerate(bot_data["fuel"], 1):
                story.append(Paragraph(
                    f"{i}. {item['liters']}L por R${item['price']:.2f} |{item['date']}|",
                    normal
                ))
        else:
            story.append(Paragraph("Nenhum registro", normal))

        story.append(Spacer(1, 12))

        # ===============================
        #   MANUTENÇÕES
        # ===============================
        story.append(Paragraph("■ Manutenções:", header))

        if bot_data["manu"]:
            for i, item in enumerate(bot_data["manu"], 1):
                price = item.get("price", 0.0)
                story.append(Paragraph(
                    f"{i}. {item['desc']} | R$ {price:.2f} | "
                    f"{item['km']} Km |{item['date']}|",
                    normal
                ))
        else:
            story.append(Paragraph("Nenhum registro", normal))

        story.append(Spacer(1, 12))

        # ===============================
        #   KM
        # ===============================
        story.append(Paragraph("■ KM:", header))

        if bot_data["km"]:
            sorted_km = sorted(bot_data["km"], key=lambda x: x["km"])
            for i, item in enumerate(sorted_km, 1):
                story.append(Paragraph(
                    f"{i}. {item['km']} Km |{item['date']}|",
                    normal
                ))
        else:
            story.append(Paragraph("Nenhum registro", normal))

        # ===============================
        #   EXPORT
        # ===============================
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
    total_mes = total_fuel_mes()
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
