#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - Goldman Style PDF Report Generator
Integrated into reports/ directory
Generates professional Chinese PDF reports from prediction results
"""

import sys, os, math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Chinese fonts (Windows system fonts)
_FONTS = {
    'YaHei': r"C:\Windows\Fonts\msyh.ttc",
    'YaHei-Bold': r"C:\Windows\Fonts\msyhbd.ttc",
    'YaHei-Light': r"C:\Windows\Fonts\msyhl.ttc",
}
for name, path in _FONTS.items():
    try:
        pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
    except Exception as e:
        from core.logger import get_logger
        logger = get_logger("naga_quant.fixer")
        logger.error(f"Silent error suppressed: {e}", exc_info=True)

# Goldman color palette
_BLUE = HexColor('#003366')
_GRAY = HexColor('#666666')
_LIGHT_GRAY = HexColor('#999999')
_DARK_GRAY = HexColor('#333333')
_ACCENT_RED = HexColor('#CC0000')
_GREEN = HexColor('#006600')
_TABLE_HEADER = HexColor('#E8EEF4')
_WARNING_BG = HexColor('#FFF3CD')
_VALUE_BG = HexColor('#E8F5E9')


def _create_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('RTitle', fontName='YaHei-Bold', fontSize=24, leading=30, textColor=_BLUE, alignment=TA_CENTER, spaceAfter=6*mm))
    s.add(ParagraphStyle('RSub', fontName='YaHei', fontSize=14, leading=20, textColor=_GRAY, alignment=TA_CENTER, spaceAfter=4*mm))
    s.add(ParagraphStyle('RMeta', fontName='YaHei-Light', fontSize=10, leading=14, textColor=_LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=20*mm))
    s.add(ParagraphStyle('RWarning', fontName='YaHei-Bold', fontSize=12, leading=18, textColor=_ACCENT_RED, alignment=TA_CENTER, spaceBefore=4*mm, spaceAfter=10*mm, backColor=_WARNING_BG))
    s.add(ParagraphStyle('RH2', fontName='YaHei-Bold', fontSize=14, leading=20, textColor=_BLUE, spaceBefore=8*mm, spaceAfter=4*mm))
    s.add(ParagraphStyle('RH3', fontName='YaHei-Bold', fontSize=12, leading=18, textColor=_DARK_GRAY, spaceBefore=6*mm, spaceAfter=3*mm))
    s.add(ParagraphStyle('RH4', fontName='YaHei-Bold', fontSize=11, leading=16, textColor=_ACCENT_RED, spaceBefore=4*mm, spaceAfter=2*mm))
    s.add(ParagraphStyle('RBody', fontName='YaHei', fontSize=10.5, leading=16, textColor=_DARK_GRAY, alignment=TA_JUSTIFY, spaceAfter=3*mm))
    s.add(ParagraphStyle('RSmall', fontName='YaHei', fontSize=9, leading=14, textColor=_GRAY, alignment=TA_JUSTIFY, spaceAfter=2*mm))
    s.add(ParagraphStyle('RDisclaimer', fontName='YaHei-Light', fontSize=8, leading=12, textColor=_LIGHT_GRAY, alignment=TA_JUSTIFY, spaceAfter=2*mm))
    return s


def _table_style_base():
    return [
        ('FONTNAME', (0, 0), (-1, -1), 'YaHei'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), _DARK_GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, _LIGHT_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]


def _table_header():
    base = _table_style_base()
    base += [
        ('BACKGROUND', (0, 0), (-1, 0), _TABLE_HEADER),
        ('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, 0), _BLUE),
    ]
    return base


class _GoldmanHeader:
    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(_BLUE)
        canvas.rect(0, doc.height + doc.topMargin - 15, doc.width + doc.leftMargin + doc.rightMargin, 15, fill=1, stroke=0)
        canvas.setFont('YaHei-Light', 8)
        canvas.setFillColor(_LIGHT_GRAY)
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 20, f"Naga Quantitative Investment System | Confidential | {datetime.now().strftime('%Y-%m-%d')}")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin - 20, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()


def generate_pdf_report(result: dict, output_path: str = None) -> str:
    """
    Generate a Goldman-style PDF report from a FootballQuant prediction result.
    
    Args:
        result: dict from FootballQuantBridge.predict() or run_match_task()
        output_path: optional path; defaults to Desktop
    
    Returns:
        Path to generated PDF file
    """
    if output_path is None:
        desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
        output_path = os.path.join(desktop, f"Naga_Report_{result.get('home_team','Home')}_vs_{result.get('away_team','Away')}.pdf")
    
    styles = _create_styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=25*mm, bottomMargin=20*mm)
    story = []
    
    # Title
    home = result.get('home_team', 'Home')
    away = result.get('away_team', 'Away')
    league = result.get('league', 'Unknown')
    story.append(Paragraph("NAGA 量化投资决策报告", styles['RTitle']))
    story.append(Paragraph(f"{home} vs {away} | {league}", styles['RSub']))
    story.append(Paragraph(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} | 数据来源：Football Quant OS v4.2", styles['RMeta']))
    story.append(HRFlowable(width="100%", thickness=1, color=_BLUE, spaceBefore=2*mm, spaceAfter=5*mm))
    
    # Executive Summary
    story.append(Paragraph("执行摘要", styles['RH2']))
    
    # Prediction result
    probs = result.get('matrix_108', {}).get('probabilities', {})
    home_win = probs.get('home_win', 0)
    draw = probs.get('draw', 0)
    away_win = probs.get('away_win', 0)
    
    # Determine prediction
    max_prob = max(home_win, draw, away_win)
    if max_prob == home_win:
        prediction = f"{home} 主胜（{home_win:.1f}%）"
    elif max_prob == draw:
        prediction = f"平局（{draw:.1f}%）"
    else:
        prediction = f"{away} 客胜（{away_win:.1f}%）"
    
    story.append(Paragraph(
        f"<b>预测结果：</b>{prediction}。<br/>"
        f"<b>概率分布：</b>主胜 {home_win:.1f}% | 平局 {draw:.1f}% | 客胜 {away_win:.1f}%。<br/>"
        f"<b>说明：</b>以上为最可能 outcome 的概率评估。价值投注（赔率被低估的方向）请参见各市场分析。",
        styles['RBody']))
    
    # Key Findings Table
    story.append(Paragraph("关键指标", styles['RH2']))
    key_data = [
        ['指标', '数值'],
        ['系统版本', 'Football Quant OS v4.2'],
        ['预测模型', '108矩阵 + 9 Agent流水线'],
        ['主胜概率', f'{home_win:.1f}%'],
        ['平局概率', f'{draw:.1f}%'],
        ['客胜概率', f'{away_win:.1f}%'],
        ['预测结果', prediction],
    ]
    key_table = Table(key_data, colWidths=[50*mm, 100*mm])
    key_table.setStyle(TableStyle(_table_header()))
    story.append(key_table)
    story.append(Spacer(1, 5*mm))
    
    # Decision / Strategy
    story.append(Paragraph("投注策略", styles['RH2']))
    dec = result.get('decision', {})
    rec = dec.get('recommended_outcome', 'N/A')
    conf = dec.get('confidence', 0) * 100
    stake = result.get('stake', {})
    
    story.append(Paragraph(
        f"<b>推荐方向：</b>{rec}<br/>"
        f"<b>信心度：</b>{conf:.0f}%<br/>"
        f"<b>Kelly比例：</b>{stake.get('safe_fraction', 0)*100:.2f}%<br/>"
        f"<b>建议投注：</b>{stake.get('stake', 0):.0f} 单位<br/>"
        f"<b>风险等级：</b>{stake.get('risk_level', 'Unknown')}",
        styles['RBody']))
    
    # Risk Warnings
    story.append(Paragraph("风险提示", styles['RH2']))
    warnings = result.get('risk_warnings', [])
    if not warnings:
        warnings = [
            "所有预测基于概率模型，不代表必然结果",
            "过往表现不代表未来收益",
            "请根据自身财务状况理性决策",
        ]
    for w in warnings:
        story.append(Paragraph(f"• {w}", styles['RSmall']))
    
    story.append(Spacer(1, 8*mm))
    
    # Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=_LIGHT_GRAY, spaceBefore=5*mm, spaceAfter=5*mm))
    story.append(Paragraph("免责声明", styles['RH2']))
    story.append(Paragraph(
        "本报告仅供研究参考，不构成任何投资建议或财务建议。博彩涉及高风险，可能导致资金损失。"
        "过往表现不代表未来收益。请根据自身财务状况理性决策，切勿投入超出承受能力的资金。",
        styles['RDisclaimer']))
    
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        "Naga Quantitative Investment System v5.0 | Football Quant OS v4.2 | Generated by Naga Core",
        styles['RDisclaimer']))
    
    doc.build(story, onFirstPage=_GoldmanHeader(), onLaterPages=_GoldmanHeader())
    return output_path


if __name__ == '__main__':
    # Demo usage with a mock result
    demo = {
        'home_team': 'Qatar',
        'away_team': 'Switzerland',
        'league': 'World Cup',
        'matrix_108': {'probabilities': {'home_win': 23.8, 'draw': 13.9, 'away_win': 62.4}},
        'decision': {'recommended_outcome': 'Switzerland Win', 'confidence': 0.62},
        'stake': {'safe_fraction': 0.015, 'stake': 150, 'risk_level': 'Medium'},
    }
    out = generate_pdf_report(demo)
    print(f"Demo PDF: {out}")
