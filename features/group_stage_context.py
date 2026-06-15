#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 小组赛上下文特征模块 (Group Stage Context)
版本: v1.0
功能: 根据当前积分榜计算球队出线状态、战意、轮换风险等特征

使用方式:
    from features.group_stage_context import get_group_stage_context, adjust_for_group_stage_context
    context = get_group_stage_context('Sweden', 'Tunisia', current_standings)
    adjusted_probs = adjust_for_group_stage_context(base_probs, context)
"""

from typing import Dict, Any, Tuple
from enum import Enum


class QualificationStatus(Enum):
    """出线状态枚举"""
    QUALIFIED = "qualified"           # 已出线
    LIKELY = "likely"                 # 基本确定出线
    FIGHTING = "fighting"             # 争夺出线
    MUST_WIN = "must_win"             # 必须赢才能出线
    MUST_NOT_LOSE = "must_not_lose"   # 必须不输才能出线
    ELIMINATED = "eliminated"         # 已出局
    UNKNOWN = "unknown"               # 未知


# ============================================================
# 核心函数
# ============================================================

def get_group_stage_context(home_team: str, away_team: str,
                            current_standings: Dict[str, Dict]) -> Dict[str, Any]:
    """
    根据当前积分榜，返回小组赛上下文特征
    
    Args:
        home_team: 主队名称
        away_team: 客队名称
        current_standings: 当前积分榜，格式:
            {
                "Sweden": {"points": 0, "played": 0, "goal_diff": 0, "goals_for": 0},
                "Tunisia": {"points": 0, "played": 0, "goal_diff": 0, "goals_for": 0},
            }
    
    Returns:
        上下文特征字典
    """
    home_info = current_standings.get(home_team, {})
    away_info = current_standings.get(away_team, {})
    
    # 基础特征
    context = {
        # 积分
        "home_points": home_info.get("points", 0),
        "away_points": away_info.get("points", 0),
        # 已踢场次
        "home_played": home_info.get("played", 0),
        "away_played": away_info.get("played", 0),
        # 净胜球
        "home_goal_diff": home_info.get("goal_diff", 0),
        "away_goal_diff": away_info.get("goal_diff", 0),
        # 进球数
        "home_goals_for": home_info.get("goals_for", 0),
        "away_goals_for": away_info.get("goals_for", 0),
    }
    
    # 计算出线状态
    context["home_status"] = _get_qualification_status(home_info, current_standings)
    context["away_status"] = _get_qualification_status(away_info, current_standings)
    
    # 是否必须赢
    context["home_must_win"] = _is_must_win(home_info, current_standings)
    context["away_must_win"] = _is_must_win(away_info, current_standings)
    
    # 是否必须不输
    context["home_must_not_lose"] = _is_must_not_lose(home_info, current_standings)
    context["away_must_not_lose"] = _is_must_not_lose(away_info, current_standings)
    
    # 强队轮换风险
    context["home_rotation_risk"] = _rotation_risk(home_info, current_standings)
    context["away_rotation_risk"] = _rotation_risk(away_info, current_standings)
    
    # 战意强度 (0-1)
    context["home_motivation"] = _calculate_motivation(home_info, current_standings)
    context["away_motivation"] = _calculate_motivation(away_info, current_standings)
    
    # 是否为小组赛最后一场（关键特征！）
    context["is_last_match"] = _is_last_match(home_info, away_info, current_standings)
    context["home_last_match"] = context["is_last_match"] and home_info.get("played", 0) == 2
    context["away_last_match"] = context["is_last_match"] and away_info.get("played", 0) == 2
    
    # 比赛重要性 (0-1)
    context["match_importance"] = _calculate_match_importance(
        home_info, away_info, current_standings
    )
    
    return context


# ============================================================
# 内部计算函数
# ============================================================

def _get_qualification_status(team_info: Dict, standings: Dict) -> str:
    """
    计算球队出线状态 (v2.0 - 考虑净胜球)
    
    2026世界杯规则：12组→32强，前2名+8个最好第3名出线
    净胜球在很多情况下比积分更重要
    """
    if not team_info:
        return QualificationStatus.UNKNOWN.value
    
    points = team_info.get("points", 0)
    played = team_info.get("played", 0)
    goal_diff = team_info.get("goal_diff", 0)
    
    # 还没踢
    if played == 0:
        return QualificationStatus.UNKNOWN.value
    
    # 已踢3场，比赛结束
    if played >= 3:
        # 按积分+净胜球排序
        sorted_teams = sorted(
            standings.items(),
            key=lambda x: (x[1].get("points", 0), x[1].get("goal_diff", 0)),
            reverse=True
        )
        team_names = [t[0] for t in sorted_teams]
        team_name = None
        for name, info in standings.items():
            if info is team_info:
                team_name = name
                break
        
        if team_name and team_names.index(team_name) < 2:
            return QualificationStatus.QUALIFIED.value
        else:
            # 第3名：净胜球好的更可能出线
            if team_name and team_names.index(team_name) == 2:
                if goal_diff >= 0:
                    return QualificationStatus.LIKELY.value  # 净胜球好，大概率出线
                else:
                    return QualificationStatus.FIGHTING.value  # 净胜球差，看其他组
            return QualificationStatus.ELIMINATED.value
    
    # 已踢2场
    if played == 2:
        if points >= 6:
            return QualificationStatus.QUALIFIED.value  # 6分基本出线
        elif points == 4:
            # 4分：净胜球很关键
            if goal_diff >= 2:
                return QualificationStatus.LIKELY.value     # 4分+好净胜球，大概率出线
            elif goal_diff >= 0:
                return QualificationStatus.LIKELY.value     # 4分+非负净胜球，形势不错
            else:
                return QualificationStatus.FIGHTING.value   # 4分但净胜球为负，不稳
        elif points == 3:
            # 3分：净胜球决定命运
            if goal_diff >= 2:
                return QualificationStatus.FIGHTING.value   # 3分+好净胜球，有机会争第3
            elif goal_diff >= -1:
                return QualificationStatus.FIGHTING.value   # 3分+一般净胜球，需要努力
            else:
                return QualificationStatus.MUST_WIN.value   # 3分+差净胜球，必须赢
        elif points == 1:
            # 1分：基本必须赢
            if goal_diff >= 0:
                return QualificationStatus.MUST_WIN.value   # 1分但净胜球还行
            else:
                return QualificationStatus.MUST_WIN.value   # 1分+负净胜球，必须赢
        else:  # 0分
            # 0分：净胜球好的还有理论机会
            if goal_diff >= 0:
                return QualificationStatus.FIGHTING.value   # 0分但净胜球好，奇迹可能
            elif goal_diff >= -2:
                return QualificationStatus.MUST_WIN.value   # 0分+一般净胜球
            else:
                return QualificationStatus.ELIMINATED.value  # 0分+很差净胜球，基本出局
    
    # 已踢1场
    if played == 1:
        if points == 3:
            if goal_diff >= 2:
                return QualificationStatus.LIKELY.value     # 首战大胜
            else:
                return QualificationStatus.FIGHTING.value   # 首战小胜
        elif points == 1:
            return QualificationStatus.FIGHTING.value       # 平局
        else:  # 0分
            if goal_diff >= -1:
                return QualificationStatus.FIGHTING.value   # 小负
            else:
                return QualificationStatus.MUST_WIN.value   # 大败
    
    return QualificationStatus.UNKNOWN.value


def _is_must_win(team_info: Dict, standings: Dict) -> bool:
    """是否必须赢才能出线"""
    if not team_info:
        return False
    
    points = team_info.get("points", 0)
    played = team_info.get("played", 0)
    
    # 最后一场且必须赢
    if played == 2:
        if points <= 1:
            return True  # 0分或1分，最后一场必须赢
    
    # 已踢1场，0分，第2场必须赢
    if played == 1 and points == 0:
        # 检查其他球队积分
        max_others = max(
            (v.get("points", 0) for k, v in standings.items() if v is not team_info),
            default=0
        )
        if max_others >= 3:
            return True  # 别人已经3分，自己0分，形势危急
    
    return False


def _is_must_not_lose(team_info: Dict, standings: Dict) -> bool:
    """是否必须不输才能出线"""
    if not team_info:
        return False
    
    points = team_info.get("points", 0)
    played = team_info.get("played", 0)
    
    # 4分，最后一场不输就出线
    if played == 2 and points == 4:
        return True
    
    # 3分，最后一场不输大概率出线
    if played == 2 and points == 3:
        return True
    
    return False


def _rotation_risk(team_info: Dict, standings: Dict) -> float:
    """
    强队轮换概率 (0-1)
    已出线或基本出线的强队更可能轮换
    """
    if not team_info:
        return 0.0
    
    points = team_info.get("points", 0)
    played = team_info.get("played", 0)
    
    # 还没踢或只踢1场，不会轮换
    if played < 2:
        return 0.0
    
    # 已踢2场，6分已出线
    if played == 2 and points >= 6:
        return 0.7  # 70%轮换概率
    
    # 已踢2场，4分基本出线
    if played == 2 and points == 4:
        # 检查是否领先第3名很多
        others = [v for k, v in standings.items() if v is not team_info]
        if others:
            max_others = max(v.get("points", 0) for v in others)
            if max_others <= 1:
                return 0.5  # 领先很多，50%轮换
    
    return 0.0


def _calculate_motivation(team_info: Dict, standings: Dict) -> float:
    """
    计算球队战意强度 (0-1)
    """
    if not team_info:
        return 0.5  # 未知时默认中等战意
    
    points = team_info.get("points", 0)
    played = team_info.get("played", 0)
    status = _get_qualification_status(team_info, standings)
    
    # 已出线
    if status == QualificationStatus.QUALIFIED.value:
        return 0.3  # 战意低，可能轮换
    
    # 基本出线
    if status == QualificationStatus.LIKELY.value:
        return 0.5  # 中等战意
    
    # 已出局
    if status == QualificationStatus.ELIMINATED.value:
        return 0.2  # 战意很低
    
    # 必须赢
    if _is_must_win(team_info, standings):
        return 1.0  # 最高战意
    
    # 必须不输
    if _is_must_not_lose(team_info, standings):
        return 0.8  # 高战意，但可能保守
    
    # 争夺中
    if status == QualificationStatus.FIGHTING.value:
        return 0.7  # 较高战意
    
    return 0.5


def _is_last_match(team_info: Dict, opponent_info: Dict, standings: Dict) -> bool:
    """
    判断是否为小组赛最后一场
    条件：两队都已踢2场，且这是本组最后一场比赛（或各自最后一场）
    """
    if not team_info or not opponent_info:
        return False
    
    played = team_info.get("played", 0)
    opp_played = opponent_info.get("played", 0)
    
    # 如果两队都已踢2场，这是第3场比赛（最后一场）
    if played == 2 and opp_played == 2:
        return True
    
    return False


def _calculate_match_importance(home_info: Dict, away_info: Dict, 
                                standings: Dict) -> float:
    """
    计算比赛整体重要性 (0-1)
    基于两队战意和形势
    """
    home_mot = _calculate_motivation(home_info, standings)
    away_mot = _calculate_motivation(away_info, standings)
    
    # 重要性取平均值，但如果一方已出线一方必须赢，重要性更高
    avg_mot = (home_mot + away_mot) / 2
    
    # 特殊情况：一方已出线，一方必须赢
    home_status = _get_qualification_status(home_info, standings)
    away_status = _get_qualification_status(away_info, standings)
    
    if (home_status == QualificationStatus.QUALIFIED.value and 
        _is_must_win(away_info, standings)):
        return 0.9  # 强队vs必须赢的弱队，重要性高
    
    if (away_status == QualificationStatus.QUALIFIED.value and 
        _is_must_win(home_info, standings)):
        return 0.9
    
    return avg_mot


# ============================================================
# 概率调整函数
# ============================================================

def adjust_for_group_stage_context(base_probs: Dict[str, float],
                                   context: Dict[str, Any]) -> Dict[str, float]:
    """
    基于小组赛上下文调整概率
    
    Args:
        base_probs: 基础概率，如 {"home": 0.32, "draw": 0.43, "away": 0.25}
        context: get_group_stage_context()返回的上下文
    
    Returns:
        调整后的概率
    """
    home = base_probs.get("home", 0.33)
    draw = base_probs.get("draw", 0.33)
    away = base_probs.get("away", 0.33)
    
    home_mot = context.get("home_motivation", 0.5)
    away_mot = context.get("away_motivation", 0.5)
    home_rot = context.get("home_rotation_risk", 0.0)
    away_rot = context.get("away_rotation_risk", 0.0)
    match_imp = context.get("match_importance", 0.5)
    
    # 1. 战意调整：高战意球队胜率提升
    mot_diff = home_mot - away_mot  # 正=主队战意更高
    home += mot_diff * 0.05  # 战意差最大影响5%
    away -= mot_diff * 0.05
    
    # 2. 轮换调整：轮换风险高的球队胜率下降
    home -= home_rot * 0.08  # 轮换最多影响8%
    away -= away_rot * 0.08
    
    # 3. 比赛重要性：重要性高的比赛，平局概率下降（更激烈）
    if match_imp > 0.7:
        draw *= 0.95  # 重要性高，平局-5%
        # 分配到胜负
        home += draw * 0.025
        away += draw * 0.025
    
    # 4. 必须赢的球队：进攻更积极，进球概率上升
    if context.get("home_must_win"):
        home += 0.03
        draw -= 0.015
        away -= 0.015
    if context.get("away_must_win"):
        away += 0.03
        draw -= 0.015
        home -= 0.015
    
    # 5. 必须不输的球队：更保守
    if context.get("home_must_not_lose"):
        draw += 0.03
        home -= 0.015
        away -= 0.015
    if context.get("away_must_not_lose"):
        draw += 0.03
        home -= 0.015
        away -= 0.015
    
    # 6. 最后一场调整：重要性极高，平局概率下降，比赛更激烈
    if context.get("is_last_match"):
        draw *= 0.90  # 最后一场平局概率-10%
        # 分配到胜负
        home += draw * 0.05
        away += draw * 0.05
        # 如果一方必须赢，该方胜率额外提升
        if context.get("home_must_win"):
            home += 0.02
            away -= 0.02
        if context.get("away_must_win"):
            away += 0.02
            home -= 0.02
    
    # 归一化
    total = home + draw + away
    if total > 0:
        home = max(0.05, min(0.95, home / total))
        draw = max(0.05, min(0.90, draw / total))
        away = max(0.05, min(0.95, 1 - home - draw))
    
    return {
        "home": round(home, 3),
        "draw": round(draw, 3),
        "away": round(away, 3),
        "adjusted": True,
        "adjustments": {
            "motivation_diff": mot_diff,
            "rotation_home": home_rot,
            "rotation_away": away_rot,
            "match_importance": match_imp
        }
    }


# ============================================================
# 工具函数
# ============================================================

def format_context_for_display(context: Dict[str, Any]) -> str:
    """格式化上下文为可读字符串"""
    lines = [
        f"主队: 积分={context['home_points']}, 场次={context['home_played']}, "
        f"净胜球={context['home_goal_diff']}, 状态={context['home_status']}, "
        f"战意={context['home_motivation']:.1f}",
        f"客队: 积分={context['away_points']}, 场次={context['away_played']}, "
        f"净胜球={context['away_goal_diff']}, 状态={context['away_status']}, "
        f"战意={context['away_motivation']:.1f}",
        f"比赛重要性: {context['match_importance']:.1f}",
    ]
    
    if context.get("home_must_win"):
        lines.append("[!] 主队必须赢才能出线")
    if context.get("away_must_win"):
        lines.append("[!] 客队必须赢才能出线")
    if context.get("home_must_not_lose"):
        lines.append("[!] 主队必须不输才能出线")
    if context.get("away_must_not_lose"):
        lines.append("[!] 客队必须不输才能出线")
    if context.get("is_last_match"):
        lines.append("[!] 这是小组赛最后一场！")
    if context.get("home_rotation_risk", 0) > 0:
        lines.append(f"[!] 主队轮换风险: {context['home_rotation_risk']:.0%}")
    if context.get("away_rotation_risk", 0) > 0:
        lines.append(f"[!] 客队轮换风险: {context['away_rotation_risk']:.0%}")
    
    return "\n".join(lines)


# ============================================================
# 示例用法
# ============================================================

if __name__ == '__main__':
    # 示例：F组第1轮，瑞典vs突尼斯，两队都还没踢
    f_group_standings = {
        "Netherlands": {"points": 0, "played": 0, "goal_diff": 0, "goals_for": 0},
        "Japan": {"points": 0, "played": 0, "goal_diff": 0, "goals_for": 0},
        "Tunisia": {"points": 0, "played": 0, "goal_diff": 0, "goals_for": 0},
        "Sweden": {"points": 0, "played": 0, "goal_diff": 0, "goals_for": 0},
    }
    
    context = get_group_stage_context("Sweden", "Tunisia", f_group_standings)
    print("=" * 60)
    print("F组第1轮 - 瑞典 vs 突尼斯")
    print("=" * 60)
    print(format_context_for_display(context))
    print()
    
    # 调整示例
    base_probs = {"home": 0.32, "draw": 0.43, "away": 0.25}
    adjusted = adjust_for_group_stage_context(base_probs, context)
    print("基础概率:", base_probs)
    print("调整后:", adjusted)
    
    # 示例：已踢2轮后的情况
    print("\n" + "=" * 60)
    print("F组第3轮 - 假设荷兰6分已出线，瑞典3分必须赢")
    print("=" * 60)
    f_group_round3 = {
        "Netherlands": {"points": 6, "played": 2, "goal_diff": 3, "goals_for": 4},
        "Japan": {"points": 4, "played": 2, "goal_diff": 1, "goals_for": 2},
        "Sweden": {"points": 3, "played": 2, "goal_diff": -1, "goals_for": 1},
        "Tunisia": {"points": 1, "played": 2, "goal_diff": -3, "goals_for": 0},
    }
    
    context2 = get_group_stage_context("Sweden", "Netherlands", f_group_round3)
    print(format_context_for_display(context2))
    adjusted2 = adjust_for_group_stage_context({"home": 0.25, "draw": 0.30, "away": 0.45}, context2)
    print("调整后:", adjusted2)
