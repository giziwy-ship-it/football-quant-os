#!/usr/bin/env python3
import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from reports.generate_pdf_report import generate_pdf_report

# 构建完整的预测结果
result = {
    'home_team': '巴西',
    'away_team': '摩洛哥',
    'league': '2026世界杯小组赛',
    'matrix_108': {
        'probabilities': {
            'home_win': 52.0,
            'draw': 28.0,
            'away_win': 20.0,
        }
    },
    'decision': {
        'recommended_outcome': '摩洛哥+1球（让球盘）/ 小球',
        'confidence': 0.65,
    },
    'stake': {
        'safe_fraction': 0.079,
        'stake': 793,
        'risk_level': 'Medium',
    },
    'risk_warnings': [
        '市场隐含巴西胜率60.6%，但模型仅52.0%，存在8.6%定价偏差',
        '摩洛哥近10场不败+场均失0.3球，防守数据极强',
        '投注热度83%流向巴西，但赔率不降反升，大热信号',
        'CoachFactor: 雷格拉吉CRI 7.4 vs 多里瓦尔6.0，大赛经验碾压',
        'UpsetDetector: 冷门评分17/100，非强冷门但存在市场定价错误',
        '过往表现不代表未来收益，请理性决策',
    ],
}

output_path = 'D:\\openclaw-workspace\\Naga_Report_Brazil_vs_Morocco.pdf'
pdf_path = generate_pdf_report(result, output_path)
print(f'PDF已生成: {pdf_path}')
