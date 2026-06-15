"""
Football Quant OS - Kelly仓位集成模块
连接预测模型与TreasuryAgent的资金管理
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class BettingOpportunity:
    """投注机会"""
    match: str
    market: str
    selection: str
    odds: float
    model_probability: float
    model_confidence: float
    edge: float


def parse_prediction_to_opportunities(prediction: Dict[str, Any]) -> List[BettingOpportunity]:
    """
    将预测结果解析为投注机会列表
    
    Args:
        prediction: predict.py 的输出结果
    
    Returns:
        List[BettingOpportunity]: 可投注的机会列表
    """
    opportunities = []
    match = prediction['match']
    
    # 1X2 市场
    if '1x2' in prediction.get('markets', {}):
        m1x2 = prediction['markets']['1x2']
        implied = m1x2['implied']
        model = m1x2['model']
        edge = m1x2['edge']
        
        for selection in ['home', 'draw', 'away']:
            if edge[selection] > 0.02:  # Edge > 2%
                opp = BettingOpportunity(
                    match=match,
                    market='1x2',
                    selection=selection,
                    odds=1 / implied[selection],  # 从概率反推赔率
                    model_probability=model[selection],
                    model_confidence=prediction.get('confidence', 0.5),
                    edge=edge[selection]
                )
                opportunities.append(opp)
    
    # 大小球市场
    if 'over_under' in prediction.get('markets', {}):
        ou = prediction['markets']['over_under']
        if ou.get('recommendation') and ou['recommendation'] != 'No Edge':
            line = ou.get('line', 2.5)
            selection = ou['recommendation'].lower()  # 'over' or 'under'
            
            opp = BettingOpportunity(
                match=match,
                market=f'over_under_{line}',
                selection=selection,
                odds=2.0,  # 简化，实际应从市场获取
                model_probability=ou['over_prob'] if selection == 'over' else ou['under_prob'],
                model_confidence=prediction.get('confidence', 0.5),
                edge=ou.get('edge', 0.0)
            )
            opportunities.append(opp)
    
    return opportunities


def calculate_kelly_stake(opportunity: BettingOpportunity, 
                          bankroll: float = 100000.0,
                          kelly_fraction: float = 0.25) -> Dict[str, Any]:
    """
    计算Kelly注码
    
    Args:
        opportunity: 投注机会
        bankroll: 总资金
        kelly_fraction: Kelly分数 (保守0.25, 标准0.5, 激进1.0)
    
    Returns:
        {
            'action': 'bet' or 'skip',
            'stake': float,
            'kelly_pct': float,
            'fraction': float,
            'expected_value': float
        }
    """
    p = opportunity.model_probability
    odds = opportunity.odds
    
    if odds <= 1.0 or p <= 0 or p >= 1:
        return {'action': 'skip', 'reason': 'invalid_parameters'}
    
    b = odds - 1  # 净赔率
    q = 1 - p
    
    # Kelly公式: f = (bp - q) / b
    kelly = (b * p - q) / b
    
    if kelly <= 0:
        return {
            'action': 'skip',
            'reason': 'negative_kelly',
            'kelly_pct': round(kelly, 4)
        }
    
    # 应用Kelly分数和置信度
    fraction = kelly * kelly_fraction * opportunity.model_confidence
    
    # 限制最大注码
    max_stake = bankroll * 0.05  # 单次不超过5%
    stake = min(bankroll * fraction, max_stake)
    
    # 计算期望价值 (EV)
    ev = (p * odds - 1) * 100  # 百分比
    
    return {
        'action': 'bet',
        'stake': round(stake, 2),
        'kelly_pct': round(kelly * 100, 2),
        'fraction': round(fraction, 4),
        'expected_value': round(ev, 2),
        'confidence': opportunity.model_confidence,
        'edge': round(opportunity.edge, 3)
    }


def format_kelly_report(stake_info: Dict[str, Any], opportunity: BettingOpportunity) -> str:
    """格式化Kelly报告"""
    if stake_info['action'] == 'skip':
        return f"❌ {opportunity.match} - {opportunity.selection}: {stake_info.get('reason', 'skipped')}"
    
    return (
        f"✅ {opportunity.match} - {opportunity.selection}\n"
        f"   注码: ${stake_info['stake']:.2f} (Kelly: {stake_info['kelly_pct']}%)\n"
        f"   Edge: {stake_info['edge']:.1%} | EV: {stake_info['expected_value']:.1f}%\n"
        f"   置信度: {stake_info['confidence']:.1%}"
    )


# ============================================================
# 集成到 predict.py 的快捷函数
# ============================================================

def get_kelly_recommendations(prediction: Dict[str, Any], 
                              bankroll: float = 100000.0,
                              kelly_fraction: float = 0.25) -> List[Dict[str, Any]]:
    """
    从预测结果直接获取Kelly推荐
    
    使用示例:
        prediction = run_prediction('A', 'B', 2.0, 3.2, 3.8)
        kelly_recs = get_kelly_recommendations(prediction)
    """
    opportunities = parse_prediction_to_opportunities(prediction)
    recommendations = []
    
    for opp in opportunities:
        stake_info = calculate_kelly_stake(opp, bankroll, kelly_fraction)
        recommendations.append({
            'opportunity': opp,
            'stake': stake_info
        })
    
    return recommendations
