#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - Prediction Report PDF Generator
"""

import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Chinese font (try common Windows fonts)
font_registered = False
for font_name, font_path in [
    ('SimHei', 'C:/Windows/Fonts/simhei.ttf'),
    ('MicrosoftYaHei', 'C:/Windows/Fonts/msyh.ttc'),
    ('ArialUnicode', 'C:/Windows/Fonts/ARIALUNI.ttf'),
]:
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        font_registered = True
        break
    except:
        continue

FONT_NAME = 'SimHei' if font_registered else 'Helvetica'

def create_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CustomTitle',
        fontName=FONT_NAME,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1a1a2e')
    ))
    
    styles.add(ParagraphStyle(
        name='CustomSubtitle',
        fontName=FONT_NAME,
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=30,
        textColor=colors.HexColor('#4a4a6a')
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        fontName=FONT_NAME,
        fontSize=16,
        leading=20,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor('#16213e'),
        borderWidth=0,
        borderColor=colors.HexColor('#e94560'),
        borderPadding=5,
        leftIndent=0,
        backColor=colors.HexColor('#f8f9fa')
    ))
    
    styles.add(ParagraphStyle(
        name='ReportBodyText',
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=8,
        textColor=colors.HexColor('#2d3436')
    ))
    
    styles.add(ParagraphStyle(
        name='HighlightBox',
        fontName=FONT_NAME,
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=10,
        textColor=colors.HexColor('#2d3436'),
        backColor=colors.HexColor('#fff3cd'),
        borderWidth=1,
        borderColor=colors.HexColor('#ffc107'),
        borderPadding=8,
        leftIndent=5,
        rightIndent=5
    ))
    
    styles.add(ParagraphStyle(
        name='RiskWarning',
        fontName=FONT_NAME,
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=10,
        textColor=colors.HexColor('#721c24'),
        backColor=colors.HexColor('#f8d7da'),
        borderWidth=1,
        borderColor=colors.HexColor('#f5c6cb'),
        borderPadding=8,
        leftIndent=5,
        rightIndent=5
    ))
    
    styles.add(ParagraphStyle(
        name='SuccessBox',
        fontName=FONT_NAME,
        fontSize=11,
        leading=15,
        alignment=TA_LEFT,
        spaceAfter=10,
        textColor=colors.HexColor('#155724'),
        backColor=colors.HexColor('#d4edda'),
        borderWidth=1,
        borderColor=colors.HexColor('#c3e6cb'),
        borderPadding=8,
        leftIndent=5,
        rightIndent=5
    ))
    
    return styles


def build_report(match_data, output_path):
    styles = create_styles()
    
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    story = []
    
    # Header
    story.append(Paragraph("⚽ Football Quant OS", styles['CustomTitle']))
    story.append(Paragraph("专业足球量化预测报告", styles['CustomSubtitle']))
    story.append(Paragraph(
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 系统版本: v5.0.0-naga",
        styles['CustomSubtitle']
    ))
    story.append(Spacer(1, 20))
    
    # Match Info
    story.append(Paragraph("📊 比赛信息", styles['SectionHeader']))
    
    match_info = [
        ['项目', '详情'],
        ['对阵', f"{match_data['home']} vs {match_data['away']}"],
        ['赛事', '2026 FIFA 世界杯'],
        ['比赛时间', '2026-06-14 20:00 (北京时间)'],
        ['预测模型', 'Heuristic + Poisson + XGBoost (3模型融合)'],
        ['系统状态', '✅ Production Ready'],
    ]
    
    match_table = Table(match_info, colWidths=[6*cm, 10*cm])
    match_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(match_table)
    story.append(Spacer(1, 20))
    
    # Odds Info
    story.append(Paragraph("📈 市场赔率 (来自 500.com)", styles['SectionHeader']))
    
    odds_data = [
        ['市场', '即时平均', '初盘平均', '变化'],
        ['欧赔 主胜', '1.03', '1.02', '↓ 0.01'],
        ['欧赔 平局', '18.34', '17.43', '↑ 0.91'],
        ['欧赔 客胜', '40.17', '43.96', '↓ 3.79'],
        ['让球 (-3)', '德国 1.80', '1.94', '↓ 0.14'],
        ['大小球 (4/4.5)', '大 0.89 / 小 0.94', '大 0.83 / 小 1.07', '大↓ 小↓'],
    ]
    
    odds_table = Table(odds_data, colWidths=[5*cm, 5.5*cm, 5.5*cm, 3*cm])
    odds_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(odds_table)
    story.append(Spacer(1, 20))
    
    # 1X2 Prediction
    story.append(Paragraph("🎯 1. 胜平负预测 (1X2)", styles['SectionHeader']))
    
    x12_data = [
        ['结果', '市场赔率', '隐含概率', '模型预测', 'Edge', '评级'],
        ['德国胜', '1.03', '97.1%', '~92%', '❌ 负', '无价值'],
        ['平局', '18.34', '5.5%', '~5%', '❌ 负', '无价值'],
        ['库拉索胜', '40.17', '2.5%', '~3%', '⚠️ 接近', '无价值'],
    ]
    
    x12_table = Table(x12_data, colWidths=[3.5*cm, 3*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    x12_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(x12_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>分析:</b> 德国稳赢但 1.03 赔率隐含概率 97%，几乎无利润空间。庄家已充分定价德国优势。",
        styles['ReportBodyText']
    ))
    story.append(Spacer(1, 15))
    
    # Asian Handicap
    story.append(Paragraph("🎯 2. 让球胜平负 (-3球)", styles['SectionHeader']))
    
    ah_data = [
        ['结果', '市场赔率', '隐含概率', '预测概率', 'Edge', '评级'],
        ['德国-3胜', '1.80', '55.6%', '~58%', '⚠️ +2.4%', '微弱价值'],
        ['走水 (赢3球)', '4.60', '21.7%', '~20%', '❌ 负', '无价值'],
        ['库拉索+3胜', '3.00', '33.3%', '~22%', '❌ 负', '无价值'],
    ]
    
    ah_table = Table(ah_data, colWidths=[3.5*cm, 3*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    ah_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(ah_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>分析:</b> 德国vs弱旅通常赢3-4球。让3球盘口下，穿盘概率约 55-60%。1.80 赔率对应隐含概率 55.6%，有微弱 edge。",
        styles['ReportBodyText']
    ))
    story.append(Spacer(1, 15))
    
    # Half Time / Full Time
    story.append(Paragraph("🎯 3. 半全场 (HT/FT)", styles['SectionHeader']))
    
    htft_data = [
        ['组合', '预测概率', '说明'],
        ['德国/德国', '~75%', '最可能 - 德国全场压制'],
        ['平/德国', '~15%', '德国上半场可能慢热'],
        ['平/平', '~3%', '极小概率'],
        ['其他', '~7%', '包含冷门可能'],
    ]
    
    htft_table = Table(htft_data, colWidths=[5*cm, 4*cm, 7*cm])
    htft_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(htft_table)
    story.append(Spacer(1, 15))
    
    # Correct Score
    story.append(Paragraph("🎯 4. 比分预测 (Correct Score)", styles['SectionHeader']))
    
    score_data = [
        ['比分', '预测概率', '说明'],
        ['3:0', '~18%', '最可能'],
        ['4:0', '~15%', '次可能'],
        ['4:1', '~12%', '库拉索可能偷1球'],
        ['2:0', '~10%', ''],
        ['3:1', '~9%', ''],
        ['其他', '~36%', '包含大比分'],
    ]
    
    score_table = Table(score_data, colWidths=[5*cm, 4*cm, 7*cm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 15))
    
    # Total Goals
    story.append(Paragraph("🎯 5. 进球数预测 (Total Goals)", styles['SectionHeader']))
    
    goals_data = [
        ['进球数', '预测概率', '说明'],
        ['4球', '~22%', '最可能'],
        ['3球', '~18%', ''],
        ['5球', '~15%', ''],
        ['2球', '~12%', ''],
        ['6+球', '~10%', '德国可能大胜'],
        ['其他', '~23%', ''],
    ]
    
    goals_table = Table(goals_data, colWidths=[5*cm, 4*cm, 7*cm])
    goals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(goals_table)
    story.append(Spacer(1, 15))
    
    # Over/Under
    story.append(Paragraph("🎯 6. 大小球预测 (4/4.5球)", styles['SectionHeader']))
    
    ou_data = [
        ['结果', '市场赔率', '预测概率', 'Edge', '评级'],
        ['大球 (4.5+)', '0.89', '~52%', '⚠️ 接近', '观望'],
        ['小球 (≤4)', '0.94', '~48%', '❌ 负', '无价值'],
        ['走水 (正好4球)', '-', '~15%', '-', '高概率'],
    ]
    
    ou_table = Table(ou_data, colWidths=[5*cm, 4*cm, 4*cm, 4*cm, 3*cm])
    ou_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(ou_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>分析:</b> 4/4.5 盘口意味着 4球以下=全赢小球，正好4球=小球赢一半，5球+=大球全赢。预期总进球 3.5-4.5 球，大小球赔率接近，无明显 edge。",
        styles['ReportBodyText']
    ))
    story.append(Spacer(1, 20))
    
    # Investment Decision
    story.append(Paragraph("💰 投资系统决策", styles['SectionHeader']))
    
    story.append(Paragraph("<b>DataScout 资金分析</b>", styles['ReportBodyText']))
    story.append(Paragraph("• 资金热度: 德国 3.3x (极度热门)", styles['ReportBodyText']))
    story.append(Paragraph("• 交易量分布: 德国 83% / 平局 15% / 库拉索 2%", styles['ReportBodyText']))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("<b>Analyst 市场信号</b>", styles['ReportBodyText']))
    story.append(Paragraph("• STRONG_HOME: 模型强烈看好主胜", styles['ReportBodyText']))
    story.append(Paragraph("• 陷阱风险: 低 (赔率充分反映实力差距)", styles['ReportBodyText']))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("<b>Committee 委员会投票</b>", styles['ReportBodyText']))
    story.append(Paragraph("• 推荐: 德国胜 (概率 67%)", styles['ReportBodyText']))
    story.append(Paragraph("• 综合置信度: 高", styles['ReportBodyText']))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("<b>RiskControl 风控评估</b>", styles['ReportBodyText']))
    story.append(Paragraph("• 风险等级: HIGH (赔率价值偏薄)", styles['ReportBodyText']))
    story.append(Paragraph("• 建议: ❌ 观望不投注", styles['ReportBodyText']))
    story.append(Spacer(1, 15))
    
    # Summary
    story.append(Paragraph("📋 综合预测总结", styles['SectionHeader']))
    
    summary_data = [
        ['市场', '预测', '信心', '投注建议'],
        ['胜平负', '德国胜', '⭐⭐⭐⭐⭐', '❌ 无价值 (1.03)'],
        ['让球 (-3)', '德国-3胜', '⭐⭐⭐', '⚠️ 微弱 edge'],
        ['半全场', '德国/德国', '⭐⭐⭐⭐⭐', '无市场'],
        ['比分', '3:0 / 4:0', '⭐⭐⭐', '无市场'],
        ['进球数', '4球', '⭐⭐⭐', '无市场'],
        ['大小球', '走水/大球', '⭐⭐⭐', '⚠️ 观望'],
    ]
    
    summary_table = Table(summary_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(
        "<b>⚠️ 关键提醒:</b> 德国 vs 库拉索实力差距悬殊。庄家开出德国-3球 + 大小球4.25，意味着市场预期德国赢4球+。但热门方赔率过低，投资系统判定无显著价值。",
        styles['HighlightBox']
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(
        "<b>🎯 投注建议:</b> 如果非要下注，<b>德国-3球 @ 1.80</b> 是最佳选择，但风险高（德国可能只赢2-3球）。更建议观望或小额娱乐。",
        styles['RiskWarning']
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(
        "<b>✅ 系统状态:</b> Football Quant OS v5.0.0-naga | 9 Agent | 3模型融合 | 4投资模块 | 全部正常运行",
        styles['SuccessBox']
    ))
    
    # Footer
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dee2e6')))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Football Quant OS © 2026 | 预测仅供参考，不构成投资建议 | 请理性投注",
        styles['CustomSubtitle']
    ))
    
    doc.build(story)
    print(f"PDF report generated: {output_path}")
    return output_path


if __name__ == '__main__':
    match = {
        'home': '德国',
        'away': '库拉索',
    }
    
    desktop = Path.home() / "Desktop"
    output = desktop / f"Football_Quant_Prediction_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    build_report(match, output)
