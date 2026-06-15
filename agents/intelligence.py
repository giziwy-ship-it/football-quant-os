#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IntelligenceAgent - 情报中心 v1.0
融合顶级博彩机构情报逻辑：多源采集 + 权重分级 + 异常风控触发
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

class SourceTier(Enum):
    OFFICIAL = 1
    AUTHORITATIVE = 2
    PROFESSIONAL = 3
    SOCIAL = 4
    RUMOR = 5

class IntelCategory(Enum):
    INJURY = "injury"
    SUSPENSION = "suspension"
    LINEUP = "lineup"
    TACTICS = "tactics"
    FORM = "form"
    MOTIVATION = "motivation"
    TRANSFER = "transfer"
    WEATHER = "weather"
    REFEREE = "referee"
    MARKET = "market"
    LOCKER_ROOM = "locker_room"
    COACH = "coach"
    BETTING_FLOW = "betting_flow"

@dataclass
class IntelligenceSource:
    name: str
    tier: SourceTier
    category: IntelCategory
    language: str = "en"
    url: str = ""
    reliability_score: float = 0.5
    update_frequency: str = "realtime"

@dataclass
class IntelligenceItem:
    id: str
    source: IntelligenceSource
    match_id: str
    content: str
    raw_text: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    sentiment_score: float = 0.0
    impact_factor: float = 0.0
    confidence: float = 0.5
    verified: bool = False
    keywords: List[str] = field(default_factory=list)
    related_players: List[str] = field(default_factory=list)
    related_teams: List[str] = field(default_factory=list)
    
    def get_weighted_score(self) -> float:
        tier_weights = {SourceTier.OFFICIAL: 1.0, SourceTier.AUTHORITATIVE: 0.8,
                       SourceTier.PROFESSIONAL: 0.7, SourceTier.SOCIAL: 0.4, SourceTier.RUMOR: 0.2}
        tier_weight = tier_weights.get(self.source.tier, 0.5)
        reliability = self.source.reliability_score
        age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600
        time_weight = 1.0 if age_hours <= 24 else 0.8 if age_hours <= 48 else 0.6 if age_hours <= 72 else 0.4
        return tier_weight * reliability * self.confidence * time_weight

class IntelligenceAgent:
    DEFAULT_SOURCES = {
        "fifa_official": IntelligenceSource("FIFA Official", SourceTier.OFFICIAL, IntelCategory.LINEUP, "en", "https://www.fifa.com", 0.95, "realtime"),
        "uefa_official": IntelligenceSource("UEFA Official", SourceTier.OFFICIAL, IntelCategory.LINEUP, "en", "https://www.uefa.com", 0.95, "realtime"),
        "club_website": IntelligenceSource("Club Website", SourceTier.OFFICIAL, IntelCategory.INJURY, "en", "", 0.90, "daily"),
        "espn": IntelligenceSource("ESPN", SourceTier.AUTHORITATIVE, IntelCategory.FORM, "en", "https://www.espn.com", 0.85, "hourly"),
        "bbc_sport": IntelligenceSource("BBC Sport", SourceTier.AUTHORITATIVE, IntelCategory.FORM, "en", "https://www.bbc.com/sport", 0.85, "hourly"),
        "lequipe": IntelligenceSource("L'Equipe", SourceTier.AUTHORITATIVE, IntelCategory.TACTICS, "fr", "https://www.lequipe.fr", 0.80, "hourly"),
        "transfermarkt": IntelligenceSource("Transfermarkt", SourceTier.AUTHORITATIVE, IntelCategory.TRANSFER, "en", "https://www.transfermarkt.com", 0.85, "daily"),
        "opta": IntelligenceSource("Opta", SourceTier.PROFESSIONAL, IntelCategory.FORM, "en", "https://www.optasports.com", 0.90, "realtime"),
        "stats_perform": IntelligenceSource("Stats Perform", SourceTier.PROFESSIONAL, IntelCategory.FORM, "en", "https://www.statsperform.com", 0.90, "realtime"),
        "understat": IntelligenceSource("Understat", SourceTier.PROFESSIONAL, IntelCategory.FORM, "en", "https://understat.com", 0.85, "daily"),
        "fbref": IntelligenceSource("FBref", SourceTier.PROFESSIONAL, IntelCategory.FORM, "en", "https://fbref.com", 0.85, "daily"),
        "twitter": IntelligenceSource("Twitter/X", SourceTier.SOCIAL, IntelCategory.LOCKER_ROOM, "en", "https://twitter.com", 0.40, "realtime"),
        "reddit_soccer": IntelligenceSource("Reddit r/soccer", SourceTier.SOCIAL, IntelCategory.MARKET, "en", "https://reddit.com/r/soccer", 0.45, "realtime"),
        "weibo": IntelligenceSource("Weibo", SourceTier.SOCIAL, IntelCategory.MARKET, "zh", "https://weibo.com", 0.35, "realtime"),
        "rumor_mill": IntelligenceSource("Rumor Mill", SourceTier.RUMOR, IntelCategory.TRANSFER, "en", "", 0.20, "daily"),
    }
    
    SENTIMENT_KEYWORDS = {
        "positive": ["excellent", "outstanding", "brilliant", "fantastic", "superb", "confident", "strong", "sharp", "fit", "ready", "top form", "motivated", "focused", "determined", "unstoppable", "状态好", "出色", "信心", "强势", "锐气", "准备好了"],
        "negative": ["injured", "doubt", "suspended", "out", "doubtful", "unfit", "struggling", "poor", "weak", "shaky", "crisis", "chaos", "conflict", "argument", "fight", "unhappy", "disappointed", "受伤", "停赛", "缺席", "状态差", "危机", "冲突", "不满"],
        "neutral": ["training", "practice", "session", "preparation", "schedule", "confirmed", "announced", "official", "statement", "训练", "备战", "确认", "官方", "声明"]
    }
    
    RISK_TRIGGERS = {
        "key_player_injured": 0.08, "multiple_injuries": 0.12, "coach_sacked": 0.10,
        "locker_room_crisis": 0.06, "betting_anomaly": 0.05, "lineup_leak": 0.03,
        "weather_extreme": 0.04, "referee_controversy": 0.02
    }
    
    def __init__(self, custom_sources=None):
        self.sources = custom_sources or self.DEFAULT_SOURCES.copy()
        self.intelligence_db = []
        self.risk_events = []
    
    def add_intelligence(self, match_id, source_key, content, category, raw_text="", sentiment_hint=None, related_players=None, related_teams=None):
        source = self.sources.get(source_key)
        if not source:
            raise ValueError(f"Unknown source: {source_key}")
        
        sentiment = sentiment_hint if sentiment_hint is not None else self._analyze_sentiment(content)
        keywords = self._extract_keywords(content)
        confidence = self._calculate_confidence(content, source, category)
        impact = self._calculate_impact(category, sentiment, confidence, content)
        
        item = IntelligenceItem(
            id=f"{match_id}_{source_key}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            source=source, match_id=match_id, content=content, raw_text=raw_text or content,
            sentiment_score=sentiment, impact_factor=impact, confidence=confidence,
            keywords=keywords, related_players=related_players or [], related_teams=related_teams or []
        )
        
        risk_trigger = self._check_risk_trigger(item)
        if risk_trigger:
            self.risk_events.append(risk_trigger)
            item.verified = True
        
        self.intelligence_db.append(item)
        return item
    
    def _analyze_sentiment(self, text):
        text_lower = text.lower()
        pos_count = sum(1 for w in self.SENTIMENT_KEYWORDS["positive"] if w in text_lower)
        neg_count = sum(1 for w in self.SENTIMENT_KEYWORDS["negative"] if w in text_lower)
        neu_count = sum(1 for w in self.SENTIMENT_KEYWORDS["neutral"] if w in text_lower)
        total = pos_count + neg_count + neu_count
        if total == 0:
            return 0.0
        sentiment = (pos_count - neg_count) / (total + 2)
        return max(-1.0, min(1.0, sentiment))
    
    def _extract_keywords(self, text):
        keywords = []
        players = re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', text)
        keywords.extend(players)
        injury_terms = ['injured', 'injury', 'doubt', 'out', 'suspended', 'knock', 'strain', 'tear']
        for term in injury_terms:
            if term in text.lower():
                keywords.append(term)
        tactic_terms = ['formation', 'tactic', 'lineup', 'squad', 'starting XI']
        for term in tactic_terms:
            if term in text.lower():
                keywords.append(term)
        return list(set(keywords))[:10]
    
    def _calculate_confidence(self, content, source, category):
        base = source.reliability_score
        specificity = 0.0
        if re.search(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', content): specificity += 0.1
        if re.search(r'\d+\s*(day|week|month|hour)', content): specificity += 0.1
        if re.search(r'\d+\s*%', content): specificity += 0.1
        if re.search(r'\d+\s*(min|minute|goal|assist)', content): specificity += 0.05
        verifiable = 0.0
        if "http" in content or "source" in content.lower(): verifiable += 0.1
        if "official" in content.lower() or "confirmed" in content.lower(): verifiable += 0.15
        confidence = base + specificity + verifiable
        return min(1.0, confidence)
    
    def _calculate_impact(self, category, sentiment, confidence, content):
        category_impact = {
            IntelCategory.INJURY: -0.05, IntelCategory.SUSPENSION: -0.04, IntelCategory.LINEUP: 0.02,
            IntelCategory.TACTICS: 0.01, IntelCategory.FORM: 0.03, IntelCategory.MOTIVATION: 0.03,
            IntelCategory.TRANSFER: -0.02, IntelCategory.WEATHER: 0.01, IntelCategory.REFEREE: 0.01,
            IntelCategory.MARKET: 0.02, IntelCategory.LOCKER_ROOM: -0.03, IntelCategory.COACH: 0.02,
            IntelCategory.BETTING_FLOW: 0.02
        }
        base_impact = category_impact.get(category, 0.0)
        sentiment_adjustment = sentiment * 0.03
        confidence_multiplier = confidence
        content_lower = content.lower()
        multiplier = 1.0
        if any(w in content_lower for w in ['captain', 'star', 'key', 'main', '核心', '队长', '主力']): multiplier *= 1.5
        if any(w in content_lower for w in ['multiple', 'several', 'three', 'four', '多人', '多名']): multiplier *= 1.3
        if any(w in content_lower for w in ['serious', 'severe', 'surgery', ' ACL', '重伤', '手术']): multiplier *= 1.4
        total_impact = (base_impact + sentiment_adjustment) * confidence_multiplier * multiplier
        return max(-0.1, min(0.1, total_impact))
    
    def _check_risk_trigger(self, item):
        content = item.content.lower()
        category = item.source.category
        for trigger_name, threshold in self.RISK_TRIGGERS.items():
            triggered = False
            severity = "low"
            if trigger_name == "key_player_injured":
                if category == IntelCategory.INJURY and any(w in content for w in ['captain', 'star', 'key', 'main', '核心', '队长']) and item.confidence > 0.7:
                    triggered = True; severity = "high"
            elif trigger_name == "multiple_injuries":
                if category == IntelCategory.INJURY and any(w in content for w in ['multiple', 'several', 'three', 'four', '五人', '多名']) and item.confidence > 0.6:
                    triggered = True; severity = "critical"
            elif trigger_name == "coach_sacked":
                if category == IntelCategory.COACH and any(w in content for w in ['sack', 'fired', 'dismissed', 'replaced', '下课', '解雇']) and item.confidence > 0.8:
                    triggered = True; severity = "critical"
            elif trigger_name == "locker_room_crisis":
                if category == IntelCategory.LOCKER_ROOM and any(w in content for w in ['crisis', 'conflict', 'fight', 'argument', '危机', '冲突']) and item.confidence > 0.6:
                    triggered = True; severity = "high"
            elif trigger_name == "betting_anomaly":
                if category == IntelCategory.BETTING_FLOW and any(w in content for w in ['surge', 'unusual', 'sharp', 'spike', '异常', '激增']) and item.confidence > 0.5:
                    triggered = True; severity = "medium"
            elif trigger_name == "lineup_leak":
                if category == IntelCategory.LINEUP and any(w in content for w in ['leak', 'revealed', 'confirmed', '泄露', '确认']) and item.confidence > 0.7:
                    triggered = True; severity = "medium"
            elif trigger_name == "weather_extreme":
                if category == IntelCategory.WEATHER and any(w in content for w in ['storm', 'heavy rain', 'snow', 'extreme', '暴雨', '大雪']) and item.confidence > 0.6:
                    triggered = True; severity = "medium"
            if triggered:
                return {
                    'trigger': trigger_name, 'severity': severity, 'match_id': item.match_id,
                    'intelligence_id': item.id, 'impact': item.impact_factor,
                    'recommended_action': self._get_risk_action(trigger_name, severity),
                    'timestamp': datetime.now().isoformat()
                }
        return None
    
    def _get_risk_action(self, trigger, severity):
        actions = {
            "key_player_injured": {"high": "SUSPEND_BETTING_15MIN + REVIEW_PROBABILITY", "medium": "REDUCE_STAKE_50% + MONITOR"},
            "multiple_injuries": {"critical": "SUSPEND_BETTING + NOTIFY_ADMIN", "high": "REDUCE_EXPOSURE_70% + HEDGE"},
            "coach_sacked": {"critical": "SUSPEND_ALL_MATCHES + MANUAL_REVIEW", "high": "SUSPEND_BETTING_30MIN + ADJUST_PROBABILITY"},
            "locker_room_crisis": {"high": "REDUCE_STAKE_30% + MONITOR_SOCIAL", "medium": "FLAG_FOR_REVIEW"},
            "betting_anomaly": {"medium": "INVESTIGATE_FRAUD + ALERT_COMPLIANCE", "low": "LOG_ANOMALY + CONTINUE_MONITORING"},
            "lineup_leak": {"medium": "ADJUST_ODDS_5% + VERIFY_SOURCE", "low": "LOG_EVENT"},
            "weather_extreme": {"medium": "CHECK_POSTPONEMENT_RISK + ADJUST_TOTAL_GOALS", "low": "LOG_EVENT"}
        }
        trigger_actions = actions.get(trigger, {})
        return trigger_actions.get(severity, "LOG_EVENT + CONTINUE_MONITORING")
    
    def get_match_intelligence(self, match_id):
        items = [i for i in self.intelligence_db if i.match_id == match_id]
        if not items:
            return {'match_id': match_id, 'status': 'no_data'}
        by_category = {}
        for item in items:
            cat = item.source.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(item)
        total_weighted_impact = 0.0
        total_weight = 0.0
        for item in items:
            weight = item.get_weighted_score()
            total_weighted_impact += item.impact_factor * weight
            total_weight += weight
        net_impact = total_weighted_impact / total_weight if total_weight > 0 else 0.0
        match_risks = [r for r in self.risk_events if r['match_id'] == match_id]
        avg_confidence = sum(i.confidence for i in items) / len(items)
        data_freshness = min((datetime.now() - i.timestamp).total_seconds() / 3600 for i in items)
        return {
            'match_id': match_id, 'total_intelligence': len(items), 'by_category': {k: len(v) for k, v in by_category.items()},
            'net_impact': round(net_impact, 4), 'impact_description': self._describe_impact(net_impact),
            'risk_events': match_risks, 'risk_level': self._calculate_risk_level(match_risks),
            'avg_confidence': round(avg_confidence, 2), 'data_freshness_hours': round(data_freshness, 1),
            'recommendation': self._generate_recommendation(net_impact, match_risks),
            'top_intelligence': self._get_top_intelligence(items, n=5)
        }
    
    def _describe_impact(self, impact):
        if impact > 0.05: return "strongly_positive"
        elif impact > 0.02: return "moderately_positive"
        elif impact > -0.02: return "neutral"
        elif impact > -0.05: return "moderately_negative"
        else: return "strongly_negative"
    
    def _calculate_risk_level(self, risks):
        if not risks: return "low"
        severities = [r['severity'] for r in risks]
        if "critical" in severities: return "critical"
        elif "high" in severities: return "high"
        elif "medium" in severities: return "medium"
        return "low"
    
    def _generate_recommendation(self, impact, risks):
        if any(r['severity'] == 'critical' for r in risks): return "SUSPEND_TRADING + MANUAL_REVIEW_REQUIRED"
        elif any(r['severity'] == 'high' for r in risks): return "REDUCE_EXPOSURE + ENHANCED_MONITORING"
        elif impact < -0.05: return "REDUCE_HOME_STAKE + CONSIDER_HEDGE"
        elif impact > 0.05: return "CONFIDENT_HOME_POSITION + STANDARD_MONITORING"
        else: return "PROCEED_WITH_CAUTION"
    
    def _get_top_intelligence(self, items, n=5):
        sorted_items = sorted(items, key=lambda x: x.get_weighted_score(), reverse=True)
        return [
            {
                'id': item.id, 'source': item.source.name, 'tier': item.source.tier.name,
                'category': item.source.category.value,
                'content': item.content[:100] + "..." if len(item.content) > 100 else item.content,
                'impact': item.impact_factor, 'confidence': item.confidence,
                'weighted_score': round(item.get_weighted_score(), 3),
                'timestamp': item.timestamp.isoformat()
            }
            for item in sorted_items[:n]
        ]
    
    def generate_pre_match_briefing(self, match_id):
        intel = self.get_match_intelligence(match_id)
        lines = [
            "=" * 60, f"     IntelligenceAgent 赛前情报简报", f"     比赛: {match_id}", "=" * 60, "",
            f"【情报概况】", f"  总情报数: {intel['total_intelligence']}",
            f"  平均置信度: {intel['avg_confidence']*100:.0f}%", f"  最新数据: {intel['data_freshness_hours']:.1f}小时前", "",
            f"【影响评估】", f"  净影响: {intel['net_impact']:+.1%} ({intel['impact_description']})", f"  风险等级: {intel['risk_level'].upper()}", "",
            f"【风险事件】",
        ]
        if intel['risk_events']:
            for risk in intel['risk_events']:
                lines.append(f"  !! {risk['trigger']} [{risk['severity'].upper()}]")
                lines.append(f"     建议: {risk['recommended_action']}")
        else:
            lines.append("  无异常风险事件")
        lines.extend(["", f"【分类统计】"])
        for cat, count in intel['by_category'].items():
            lines.append(f"  {cat}: {count}条")
        lines.extend(["", f"【核心建议】", f"  {intel['recommendation']}", "", f"【Top 5 情报】"])
        for i, item in enumerate(intel['top_intelligence'], 1):
            lines.append(f"  {i}. [{item['tier']}] {item['source']}")
            lines.append(f"     {item['content']}")
            lines.append(f"     影响: {item['impact']:+.1%} | 置信度: {item['confidence']*100:.0f}% | 加权分: {item['weighted_score']}")
            lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

if __name__ == "__main__":
    agent = IntelligenceAgent()
    print("=" * 60)
    print("           IntelligenceAgent 情报中心")
    print("=" * 60)
    match_id = "USA_PAR_20260613"
    agent.add_intelligence(match_id, "club_website", "Captain Christian Pulisic is fit and ready for the World Cup opener. Confirmed in starting XI.", IntelCategory.INJURY, related_players=["Christian Pulisic"])
    agent.add_intelligence(match_id, "espn", "USA team showing excellent form in training sessions. High motivation for home opener.", IntelCategory.FORM)
    agent.add_intelligence(match_id, "twitter", "Rumor: Multiple players in USA squad have locker room conflict after last friendly loss.", IntelCategory.LOCKER_ROOM)
    agent.add_intelligence(match_id, "opta", "USA xG in last 5 matches: 1.8, 2.1, 1.5, 2.3, 1.9. Average: 1.92", IntelCategory.FORM)
    agent.add_intelligence(match_id, "transfermarkt", "Paraguay key defender suspended for accumulation of yellow cards.", IntelCategory.SUSPENSION, related_players=["Gustavo Gomez"])
    agent.add_intelligence(match_id, "weibo", "Weather forecast: Heavy rain expected in LA during match time. 80% precipitation.", IntelCategory.WEATHER)
    print(agent.generate_pre_match_briefing(match_id))
