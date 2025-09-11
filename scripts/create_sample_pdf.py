#!/usr/bin/env python3
"""
Script para criar um PDF de extrato bancário de exemplo para testes.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import os
from datetime import datetime, timedelta


def create_sample_statement():
    """Cria um extrato bancário de exemplo em PDF."""

    # Criar diretório se não existir
    os.makedirs("data/samples", exist_ok=True)

    # Nome do arquivo
    filename = "data/samples/extrato_exemplo.pdf"

    # Criar documento
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#003366'),
        alignment=TA_CENTER
    )

    # Cabeçalho
    story.append(Paragraph("BANCO EXEMPLO S.A.", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Extrato de Conta Corrente", styles['Heading2']))
    story.append(Spacer(1, 12))

    # Informações da conta
    info_data = [
        ["Agência:", "1234", "Conta:", "56789-0"],
        ["Cliente:", "João da Silva", "CPF:", "123.456.789-00"],
        ["Período:", "01/08/2025 a 31/08/2025", "", ""]
    ]

    info_table = Table(info_data, colWidths=[60, 120, 60, 120])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 20))

    # Saldo anterior
    story.append(Paragraph("Saldo Anterior (31/07/2025): € 2.500,00", styles['Normal']))
    story.append(Spacer(1, 12))

    # Transações
    transactions = [
        ["Data", "Descrição", "Valor", "Saldo"],
        ["01/08", "SALARIO EMPRESA XYZ", "€ 5.000,00 C", "€ 7.500,00"],
        ["02/08", "PIX ENVIADO MARIA SILVA", "€ 150,00 D", "€ 7.350,00"],
        ["03/08", "SUPERMERCADO EXTRA", "€ 287,45 D", "€ 7.062,55"],
        ["05/08", "FARMACIA POPULAR", "€ 89,90 D", "€ 6.972,65"],
        ["07/08", "UBER TRIP", "€ 23,50 D", "€ 6.949,15"],
        ["08/08", "RESTAURANTE SABOR", "€ 156,00 D", "€ 6.793,15"],
        ["10/08", "CONTA LUZ", "€ 234,78 D", "€ 6.558,37"],
        ["12/08", "NETFLIX.COM", "€ 39,90 D", "€ 6.518,47"],
        ["15/08", "TRANSFERENCIA RECEBIDA", "€ 500,00 C", "€ 7.018,47"],
        ["18/08", "POSTO SHELL", "€ 200,00 D", "€ 6.818,47"],
        ["20/08", "ACADEMIA FITNESS", "€ 120,00 D", "€ 6.698,47"],
        ["22/08", "PIX RECEBIDO PEDRO", "€ 80,00 C", "€ 6.778,47"],
        ["25/08", "SHOPPING CENTER", "€ 450,00 D", "€ 6.328,47"],
        ["28/08", "IFOOD", "€ 67,80 D", "€ 6.260,67"],
        ["30/08", "RENDIMENTO POUPANCA", "€ 15,43 C", "€ 6.276,10"],
    ]

    # Helper to safely get a color: prefer named attribute if present, otherwise fall back to HexColor
    def _safe_color(name, fallback_hex):
        attr = getattr(colors, name, None)
        if attr:
            return attr
        # Some reportlab fakes provide HexColor; others provide constants. Try HexColor when available.
        hexfunc = getattr(colors, 'HexColor', None)
        if callable(hexfunc):
            return hexfunc(fallback_hex)
        return fallback_hex

    # Criar tabela de transações
    trans_table = Table(transactions, colWidths=[50, 200, 80, 80])
    trans_table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), _safe_color('grey', '#808080')),
        ('TEXTCOLOR', (0, 0), (-1, 0), _safe_color('whitesmoke', '#F5F5F5')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Corpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),

        # Linhas alternadas
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [_safe_color('white', '#FFFFFF'), _safe_color('lightgrey', '#D3D3D3')]),

        # Bordas
        ('GRID', (0, 0), (-1, -1), 0.5, _safe_color('black', '#000000')),
    ]))

    story.append(trans_table)
    story.append(Spacer(1, 20))

    # Resumo
    story.append(Paragraph("RESUMO DO PERÍODO", styles['Heading3']))
    story.append(Spacer(1, 12))

    summary_data = [
        ["Total de Créditos:", "€ 5.595,43"],
        ["Total de Débitos:", "€ 1.819,33"],
        ["Saldo Final:", "€ 6.276,10"]
    ]

    summary_table = Table(summary_data, colWidths=[150, 100])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))

    story.append(summary_table)

    # Gerar PDF
    doc.build(story)
    print(f"✅ PDF de exemplo criado: {filename}")
    return filename


if __name__ == "__main__":
    create_sample_statement()
