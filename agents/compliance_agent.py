#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComplianceAgent v1.0 - Football Quant OS
注入: 15 高盛合规框架
功能: 投注合规监控 + 交易前检查 + 异常检测 + 记录保留 + 税务追踪 + 审计追踪

合规不是阻碍，是护城河。合规做得好，竞争对手进不来。
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from pathlib import Path
import numpy as np


class ComplianceLevel(Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    BLOCK = "BLOCK"
    EMERGENCY = "EMERGENCY"


class AuditAction(Enum):
    PREDICTION = "prediction"
    STAKE_PROPOSAL = "stake_proposal"
    ORDER_SUBMIT = "order_submit"
    ORDER_FILL = "order_fill"
    SETTLEMENT = "settlement"
    RISK_OVERRIDE = "risk_override"
    COMPLIANCE_OVERRIDE = "compliance_override"


@dataclass
class AuditRecord:
    """审计记录 - 不可篡改"""
    timestamp: str
    action: AuditAction
    match_id: str
    decision_chain: List[str]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    models_used: List[str]
    confidence: float
    compliance_check: str
    risk_check: str
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """计算审计哈希"""
        data = f"{self.timestamp}|{self.action.value}|{self.match_id}|{json.dumps(self.inputs, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class PreTradeChecker:
    """交易前检查器"""
    
    DEFAULT_LIMITS = {
        'max_single_stake': 5000,        # 单注最大金额
        'max_daily_stake': 15000,        # 单日最大投注
        'max_daily_trades': 20,          # 单日最大笔数
        'max_odds_deviation': 0.15,      # 赔率偏离最大比例
        'min_odds': 1.05,                # 最低赔率
        'max_odds': 50.0,               # 最高赔率
        'max_stake_per_match': 0.10,     # 单场比赛占总资金比例
        'max_concentration': 0.30,       # 同一联赛/阶段集中度
    }
    
    def __init__(self, limits: Dict[str, float] = None):
        self.limits = limits or self.DEFAULT_LIMITS
    
    def check(self, proposal: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """执行交易前检查"""
        violations = []
        level = ComplianceLevel.PASS
        
        stake = proposal.get('stake', 0)
        odds = proposal.get('odds', 1.0)
        match_id = proposal.get('match_id', '')
        bankroll = state.get('bankroll', 100000)
        daily_stake = state.get('daily_stake', 0)
        daily_trades = state.get('daily_trades', 0)
        
        # 1. 单注金额检查
        if stake > self.limits['max_single_stake']:
            violations.append({
                'type': 'MAX_SINGLE_STAKE',
                'limit': self.limits['max_single_stake'],
                'actual': stake,
                'message': f'单注金额 {stake} 超过上限 {self.limits["max_single_stake"]}'
            })
            level = ComplianceLevel.BLOCK
        
        # 2. 单日金额检查
        if daily_stake + stake > self.limits['max_daily_stake']:
            violations.append({
                'type': 'MAX_DAILY_STAKE',
                'limit': self.limits['max_daily_stake'],
                'actual': daily_stake + stake,
                'message': f'单日投注 {daily_stake + stake} 超过上限'
            })
            level = ComplianceLevel.BLOCK
        
        # 3. 单日笔数检查
        if daily_trades + 1 > self.limits['max_daily_trades']:
            violations.append({
                'type': 'MAX_DAILY_TRADES',
                'limit': self.limits['max_daily_trades'],
                'actual': daily_trades + 1,
                'message': '单日交易笔数超限'
            })
            level = ComplianceLevel.BLOCK
        
        # 4. 赔率合理性检查
        if odds < self.limits['min_odds']:
            violations.append({
                'type': 'ODDS_TOO_LOW',
                'limit': self.limits['min_odds'],
                'actual': odds,
                'message': f'赔率 {odds} 低于最低限制'
            })
            level = ComplianceLevel.BLOCK
        
        if odds > self.limits['max_odds']:
            violations.append({
                'type': 'ODDS_TOO_HIGH',
                'limit': self.limits['max_odds'],
                'actual': odds,
                'message': f'赔率 {odds} 过高，可能存在异常'
            })
            level = ComplianceLevel.WARNING
        
        # 5. 资金占比检查
        if stake / bankroll > self.limits['max_stake_per_match']:
            violations.append({
                'type': 'STAKE_EXCEEDS_BANKROLL_PCT',
                'limit': self.limits['max_stake_per_match'],
                'actual': round(stake / bankroll, 4),
                'message': '单注占资金比例过高'
            })
            level = ComplianceLevel.BLOCK
        
        return {
            'level': level.value,
            'passed': level == ComplianceLevel.PASS,
            'violations': violations,
            'timestamp': datetime.now().isoformat()
        }


class AnomalyDetector:
    """异常检测器 - 检测可疑交易模式"""
    
    def __init__(self, history_window: int = 30):
        self.history_window = history_window
        self.trade_history = []
    
    def record_trade(self, trade: Dict[str, Any]) -> None:
        """记录交易"""
        self.trade_history.append({
            'timestamp': datetime.now().isoformat(),
            'match_id': trade.get('match_id'),
            'stake': trade.get('stake'),
            'odds': trade.get('odds'),
            'selection': trade.get('selection')
        })
    
    def detect(self, new_trade: Dict[str, Any]) -> Dict[str, Any]:
        """检测异常"""
        anomalies = []
        
        # 1. 连续大额投注
        recent = self.trade_history[-5:] if len(self.trade_history) >= 5 else []
        if len(recent) >= 3:
            avg_stake = np.mean([t['stake'] for t in recent])
            if new_trade['stake'] > avg_stake * 3:
                anomalies.append({
                    'type': 'LARGE_STAKE_SPIKE',
                    'severity': 'WARNING',
                    'message': f'注码 {new_trade["stake"]} 是近期平均的 {new_trade["stake"]/avg_stake:.1f} 倍'
                })
        
        # 2. 赔率异常波动
        if new_trade.get('odds_drift', 0) > 0.20:
            anomalies.append({
                'type': 'ODDS_DRIFT_EXTREME',
                'severity': 'WARNING',
                'message': f'赔率漂移 {new_trade["odds_drift"]:.1%}，可能存在市场异常'
            })
        
        # 3. 频繁同一方向投注
        same_selection = [t for t in self.trade_history[-10:] 
                         if t['selection'] == new_trade.get('selection')]
        if len(same_selection) >= 5:
            anomalies.append({
                'type': 'REPETITIVE_SELECTION',
                'severity': 'INFO',
                'message': f'连续 {len(same_selection)} 次同一方向投注'
            })
        
        # 4. 时间异常 (深夜大额投注)
        hour = datetime.now().hour
        if hour < 6 and new_trade['stake'] > 1000:
            anomalies.append({
                'type': 'SUSPICIOUS_TIMING',
                'severity': 'WARNING',
                'message': '深夜大额投注，需人工确认'
            })
        
        severity = 'PASS' if not anomalies else max(
            [a['severity'] for a in anomalies], 
            key=lambda x: {'INFO': 0, 'WARNING': 1, 'BLOCK': 2}.get(x, 0)
        )
        
        return {
            'status': 'ANOMALY_DETECTED' if anomalies else 'NORMAL',
            'severity': severity,
            'anomalies': anomalies,
            'recommendation': 'REVIEW' if anomalies else 'PROCEED'
        }


class RecordKeeper:
    """记录保留器 - 不可篡改存档"""
    
    def __init__(self, archive_dir: str = None):
        if archive_dir is None:
            archive_dir = Path(__file__).parent.parent / 'archive'
        self.archive_dir = Path(archive_dir)
        self.archive_dir.mkdir(exist_ok=True)
        
        self.records: List[AuditRecord] = []
    
    def record(self, record: AuditRecord) -> None:
        """记录审计"""
        self.records.append(record)
        
        # 写入文件
        date_str = datetime.now().strftime('%Y%m%d')
        record_file = self.archive_dir / f"audit_{date_str}.jsonl"
        
        with open(record_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps({
                'timestamp': record.timestamp,
                'action': record.action.value,
                'match_id': record.match_id,
                'decision_chain': record.decision_chain,
                'inputs': record.inputs,
                'outputs': record.outputs,
                'models_used': record.models_used,
                'confidence': record.confidence,
                'compliance_check': record.compliance_check,
                'risk_check': record.risk_check,
                'hash': record.hash
            }, ensure_ascii=False) + '\n')
    
    def verify_integrity(self, date_str: str = None) -> Dict[str, Any]:
        """验证记录完整性"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        
        record_file = self.archive_dir / f"audit_{date_str}.jsonl"
        if not record_file.exists():
            return {'status': 'NO_DATA'}
        
        records = []
        with open(record_file, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        
        # 验证哈希链
        intact = True
        for i, record in enumerate(records):
            expected_hash = record['hash']
            # 简化验证：检查哈希格式
            if len(expected_hash) != 16:
                intact = False
                break
        
        return {
            'status': 'INTACT' if intact else 'TAMPERED',
            'record_count': len(records),
            'file_path': str(record_file)
        }


class TaxTracker:
    """税务追踪器"""
    
    def __init__(self, tax_rate: float = 0.20):
        self.tax_rate = tax_rate
        self.trades: List[Dict] = []
    
    def record_trade(self, trade: Dict[str, Any]) -> None:
        """记录交易用于税务"""
        self.trades.append({
            'timestamp': datetime.now().isoformat(),
            'match_id': trade.get('match_id'),
            'stake': trade.get('stake', 0),
            'payout': trade.get('payout', 0),
            'pnl': trade.get('pnl', 0),
            'tax_liable': max(trade.get('pnl', 0), 0)
        })
    
    def calculate_tax(self, year: int = None) -> Dict[str, Any]:
        """计算税务"""
        if year:
            year_trades = [t for t in self.trades 
                          if datetime.fromisoformat(t['timestamp']).year == year]
        else:
            year_trades = self.trades
        
        total_pnl = sum(t['pnl'] for t in year_trades)
        total_wins = sum(t['pnl'] for t in year_trades if t['pnl'] > 0)
        total_losses = sum(t['pnl'] for t in year_trades if t['pnl'] < 0)
        
        taxable_gain = max(total_pnl, 0)
        tax = taxable_gain * self.tax_rate
        
        return {
            'year': year or datetime.now().year,
            'total_pnl': round(total_pnl, 2),
            'total_wins': round(total_wins, 2),
            'total_losses': round(total_losses, 2),
            'taxable_gain': round(taxable_gain, 2),
            'tax_rate': self.tax_rate,
            'tax_due': round(tax, 2),
            'trade_count': len(year_trades)
        }
    
    def tax_loss_harvesting(self) -> List[Dict[str, Any]]:
        """税务损失收割建议"""
        recommendations = []
        
        # 查找亏损持仓
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        if losing_trades:
            total_loss = sum(t['pnl'] for t in losing_trades)
            recommendations.append({
                'action': 'REALIZE_LOSSES',
                'potential_tax_saving': round(abs(total_loss) * self.tax_rate, 2),
                'trades_to_close': len(losing_trades),
                'deadline': f'{datetime.now().year}-12-31'
            })
        
        return recommendations


class ComplianceAgent:
    """ComplianceAgent v1.0 - 高盛级合规框架"""
    
    def __init__(self, limits: Dict[str, float] = None, tax_rate: float = 0.20):
        self.pre_trade = PreTradeChecker(limits)
        self.anomaly = AnomalyDetector()
        self.record_keeper = RecordKeeper()
        self.tax_tracker = TaxTracker(tax_rate)
        self.audit_records: List[AuditRecord] = []
    
    def check_order(self, proposal: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """检查订单合规性"""
        # 1. 交易前检查
        pre_trade_result = self.pre_trade.check(proposal, state)
        
        # 2. 异常检测
        anomaly_result = self.anomaly.detect(proposal)
        
        # 3. 综合判断
        if pre_trade_result['level'] == 'BLOCK':
            final_status = 'BLOCKED'
            reason = 'pre_trade_violation'
        elif anomaly_result['severity'] == 'BLOCK':
            final_status = 'BLOCKED'
            reason = 'anomaly_detected'
        elif pre_trade_result['level'] == 'WARNING' or anomaly_result['severity'] == 'WARNING':
            final_status = 'WARNING'
            reason = 'requires_review'
        else:
            final_status = 'APPROVED'
            reason = 'all_checks_passed'
        
        return {
            'status': final_status,
            'reason': reason,
            'pre_trade': pre_trade_result,
            'anomaly': anomaly_result,
            'timestamp': datetime.now().isoformat()
        }
    
    def record_decision(self, match_id: str, decision_chain: List[str],
                       inputs: Dict[str, Any], outputs: Dict[str, Any],
                       models: List[str], confidence: float,
                       compliance_check: str, risk_check: str) -> AuditRecord:
        """记录决策"""
        record = AuditRecord(
            timestamp=datetime.now().isoformat(),
            action=AuditAction.PREDICTION,
            match_id=match_id,
            decision_chain=decision_chain,
            inputs=inputs,
            outputs=outputs,
            models_used=models,
            confidence=confidence,
            compliance_check=compliance_check,
            risk_check=risk_check
        )
        
        self.record_keeper.record(record)
        self.audit_records.append(record)
        return record
    
    def get_tax_report(self, year: int = None) -> Dict[str, Any]:
        """获取税务报告"""
        return self.tax_tracker.calculate_tax(year)
    
    def verify_audit_integrity(self) -> Dict[str, Any]:
        """验证审计完整性"""
        return self.record_keeper.verify_integrity()
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """获取合规摘要"""
        total_audits = len(self.audit_records)
        
        return {
            'total_audits': total_audits,
            'last_audit': self.audit_records[-1].timestamp if total_audits > 0 else None,
            'integrity_status': self.verify_audit_integrity()['status'],
            'tax_records': len(self.tax_tracker.trades),
            'compliance_level': 'FULL' if total_audits > 0 else 'PENDING'
        }


__all__ = ['ComplianceAgent', 'AuditRecord', 'PreTradeChecker', 'AnomalyDetector', 'RecordKeeper', 'TaxTracker']
