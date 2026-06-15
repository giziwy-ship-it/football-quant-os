import pandas as pd
import numpy as np
from scipy.stats import poisson
from sklearn.metrics import mean_absolute_error, accuracy_score, f1_score
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path

# ====================== 1. 数据加载 ======================
DATA_DIR = Path("D:/openclaw-workspace/football_quant_os/data")

def load_worldcup_data(years=[2018, 2014, 2022]) -> pd.DataFrame:
    """加载多届世界杯数据"""
    frames = []
    
    # 2022 Qatar
    df2022 = pd.read_csv(DATA_DIR / "kaggle/worldcup_2022_qatar/Fifa_WC_2022_Match_data.csv", encoding='latin-1')
    df2022['year'] = 2022
    df2022['home_goals'] = df2022['1_goals']
    df2022['away_goals'] = df2022['2_goals']
    df2022['home_team'] = df2022['1']
    df2022['away_team'] = df2022['2']
    df2022['total_goals'] = df2022['home_goals'] + df2022['away_goals']
    df2022['stage'] = df2022['group'].apply(lambda x: 'group' if 'Group' in str(x) else 'knockout')
    # xG features
    df2022['home_xg'] = df2022['1_xg']
    df2022['away_xg'] = df2022['2_xg']
    df2022['home_poss'] = df2022['1_poss']
    df2022['away_poss'] = df2022['2_poss']
    df2022['home_shots'] = df2022['1_attempts']
    df2022['away_shots'] = df2022['2_attempts']
    df2022['home_shots_on'] = df2022['1_ontarget']
    df2022['away_shots_on'] = df2022['2_ontarget']
    frames.append(df2022)
    
    # 2018/2014
    df_hist = pd.read_csv(DATA_DIR / "kaggle/worldcup_1930-2018/wcmatches.csv")
    for year in [2018, 2014]:
        df_y = df_hist[df_hist['year'] == year].copy()
        df_y['home_goals'] = df_y['home_score']
        df_y['away_goals'] = df_y['away_score']
        df_y['total_goals'] = df_y['home_goals'] + df_y['away_goals']
        df_y['stage'] = df_y['stage'].apply(
            lambda x: 'group' if 'Group' in str(x) else 'knockout'
        )
        # 无xG数据，用进球代替
        df_y['home_xg'] = df_y['home_goals']
        df_y['away_xg'] = df_y['away_goals']
        df_y['home_poss'] = 50.0
        df_y['away_poss'] = 50.0
        df_y['home_shots'] = df_y['home_goals'] * 3
        df_y['away_shots'] = df_y['away_goals'] * 3
        df_y['home_shots_on'] = df_y['home_goals'] * 2
        df_y['away_shots_on'] = df_y['away_goals'] * 2
        frames.append(df_y)
    
    df = pd.concat(frames, ignore_index=True)
    print(f"[Data] Loaded {len(df)} matches from {years}")
    return df


# ====================== 2. 特征工程 ======================
class FeatureEngineer:
    """世界杯大小球特征工程"""
    
    @staticmethod
    def calculate_team_stats(df: pd.DataFrame) -> pd.DataFrame:
        """计算球队历史统计（近5-10场）"""
        # 按球队和年份计算平均进球/失球
        home_stats = df.groupby(['year', 'home_team']).agg({
            'home_goals': 'mean',
            'away_goals': 'mean',  # 主场时对手的进球 = 主队失球
        }).rename(columns={'home_goals': 'avg_goals_scored_home', 'away_goals': 'avg_goals_conceded_home'})
        
        away_stats = df.groupby(['year', 'away_team']).agg({
            'away_goals': 'mean',
            'home_goals': 'mean',  # 客场时对手的进球 = 客队失球
        }).rename(columns={'away_goals': 'avg_goals_scored_away', 'home_goals': 'avg_goals_conceded_away'})
        
        return home_stats, away_stats
    
    @staticmethod
    def build_features(df: pd.DataFrame) -> pd.DataFrame:
        """构建大小球特征"""
        df = df.copy()
        
        # 基础进攻/防守能力（用本届世界杯数据近似）
        # 注：实际应用应该用赛前历史数据
        df['home_avg_goals_scored'] = df.groupby('home_team')['home_goals'].transform('mean')
        df['home_avg_goals_conceded'] = df.groupby('home_team')['away_goals'].transform('mean')
        df['away_avg_goals_scored'] = df.groupby('away_team')['away_goals'].transform('mean')
        df['away_avg_goals_conceded'] = df.groupby('away_team')['home_goals'].transform('mean')
        
        # 填充缺失值（新球队用全局平均）
        global_avg_scored = df['home_goals'].mean()
        global_avg_conceded = df['away_goals'].mean()
        df['home_avg_goals_scored'] = df['home_avg_goals_scored'].fillna(global_avg_scored)
        df['home_avg_goals_conceded'] = df['home_avg_goals_conceded'].fillna(global_avg_conceded)
        df['away_avg_goals_scored'] = df['away_avg_goals_scored'].fillna(global_avg_scored)
        df['away_avg_goals_conceded'] = df['away_avg_goals_conceded'].fillna(global_avg_conceded)
        
        # xG特征（2022有，2018/2014用进球近似）
        df['home_xg_avg'] = df.groupby('home_team')['home_xg'].transform('mean')
        df['away_xg_avg'] = df.groupby('away_team')['away_xg'].transform('mean')
        df['home_xg_avg'] = df['home_xg_avg'].fillna(global_avg_scored)
        df['away_xg_avg'] = df['away_xg_avg'].fillna(global_avg_scored)
        
        # 核心特征：预期总进球数（泊松参数 λ 的基础）
        # 公式：λ = (主队进攻 + 客队防守) / 2 + (客队进攻 + 主队防守) / 2
        df['lambda_base'] = (
            (df['home_avg_goals_scored'] + df['away_avg_goals_conceded']) / 2 +
            (df['away_avg_goals_scored'] + df['home_avg_goals_conceded']) / 2
        )
        
        # xG调整（如果xG数据可用）
        df['lambda_xg'] = (
            (df['home_xg_avg'] + df['away_xg_avg']) / 2
        )
        
        # 混合：70% 历史统计 + 30% xG
        df['lambda_mixed'] = df['lambda_base'] * 0.7 + df['lambda_xg'] * 0.3
        
        # 阶段因子（淘汰赛更保守）
        stage_factor = {
            'group': 1.0,
            'knockout': 0.90,  # 淘汰赛总进球少10%
        }
        df['stage_factor'] = df['stage'].map(stage_factor).fillna(0.95)
        df['lambda_stage'] = df['lambda_mixed'] * df['stage_factor']
        
        # 控球率影响（控球率高的队可能创造更多机会）
        df['possession_diff'] = (df['home_poss'] - df['away_poss']) / 100
        df['lambda_poss'] = df['lambda_stage'] * (1 + df['possession_diff'] * 0.1)
        
        # 射门效率
        df['home_shot_eff'] = df['home_shots_on'] / df['home_shots'].clip(lower=1)
        df['away_shot_eff'] = df['away_shots_on'] / df['away_shots'].clip(lower=1)
        df['avg_shot_eff'] = (df['home_shot_eff'] + df['away_shot_eff']) / 2
        df['lambda_eff'] = df['lambda_poss'] * (0.9 + df['avg_shot_eff'] * 0.2)
        
        # 最终泊松参数（限制在合理范围）
        df['lambda_total'] = df['lambda_eff'].clip(lower=1.5, upper=4.5)
        
        return df


# ====================== 3. 泊松分布模型 ======================
class PoissonOUModel:
    """泊松分布大小球模型"""
    
    def __init__(self, max_goals=8):
        self.max_goals = max_goals
    
    def predict_distribution(self, lambda_total: float) -> np.ndarray:
        """预测总进球数分布 P(0), P(1), ..., P(max_goals)"""
        return np.array([poisson.pmf(i, lambda_total) for i in range(self.max_goals + 1)])
    
    def calculate_over_under(self, lambda_total: float, line: float = 2.5) -> dict:
        """
        计算 Over/Under 概率
        
        Args:
            lambda_total: 泊松参数（预期总进球）
            line: 盘口线（2.5, 3.0, 3.5 等）
        
        Returns:
            {
                'over_prob': 大球概率,
                'under_prob': 小球概率,
                'expected_goals': 预期总进球,
                'most_likely': 最可能总进球数,
                'p_over_2.5': 大球2.5概率,
                'p_under_2.5': 小球2.5概率
            }
        """
        # 对于 .5 盘口（如2.5），直接计算
        if line == int(line) + 0.5:
            under_prob = sum(poisson.pmf(i, lambda_total) for i in range(int(line) + 1))
            over_prob = 1 - under_prob
        else:
            # 整数盘口（如3.0），需要处理平局退款
            under_prob = sum(poisson.pmf(i, lambda_total) for i in range(int(line)))
            exact_prob = poisson.pmf(int(line), lambda_total)
            over_prob = 1 - under_prob - exact_prob
            
            # 按比例分配
            under_prob += exact_prob / 2
            over_prob += exact_prob / 2
        
        # 最可能总进球数
        dist = self.predict_distribution(lambda_total)
        most_likely = int(np.argmax(dist))
        
        return {
            'over_prob': round(over_prob, 4),
            'under_prob': round(under_prob, 4),
            'expected_goals': round(lambda_total, 2),
            'most_likely': most_likely,
            'p_over_2.5': round(1 - sum(poisson.pmf(i, lambda_total) for i in range(3)), 4),
            'p_under_2.5': round(sum(poisson.pmf(i, lambda_total) for i in range(3)), 4)
        }
    
    def predict_match(self, lambda_total: float, lines: list = [2.0, 2.5, 3.0, 3.5]) -> dict:
        """预测多个盘口"""
        return {
            f"line_{line}": self.calculate_over_under(lambda_total, line)
            for line in lines
        }


# ====================== 4. 模型评估 ======================
class ModelEvaluator:
    """模型评估器"""
    
    @staticmethod
    def evaluate_regression(df: pd.DataFrame) -> dict:
        """回归评估（预测总进球数）"""
        mae = mean_absolute_error(df['total_goals'], df['lambda_total'])
        rmse = np.sqrt(np.mean((df['total_goals'] - df['lambda_total']) ** 2))
        
        return {
            'mae': round(mae, 3),
            'rmse': round(rmse, 3),
            'mean_actual': round(df['total_goals'].mean(), 2),
            'mean_predicted': round(df['lambda_total'].mean(), 2)
        }
    
    @staticmethod
    def evaluate_classification(df: pd.DataFrame, line: float = 2.5) -> dict:
        """分类评估（Over/Under）"""
        y_true = df['total_goals'] > line
        y_pred = df['lambda_total'] > line
        
        accuracy = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        # 计算 ROI（假设投注大球/小球赔率均为1.90）
        # 简化：预测概率 > 0.55 时投注
        df_eval = df.copy()
        df_eval['bet_over'] = df_eval['lambda_total'] > line + 0.1
        df_eval['won_over'] = df_eval['total_goals'] > line
        
        # 计算盈亏
        wins = ((df_eval['bet_over'] & df_eval['won_over']).sum() * 0.90 -
                (df_eval['bet_over'] & ~df_eval['won_over']).sum() * 1.0)
        total_bets = df_eval['bet_over'].sum()
        roi = (wins / total_bets * 100) if total_bets > 0 else 0
        
        return {
            'accuracy': round(accuracy, 3),
            'f1_score': round(f1, 3),
            'roi_percent': round(roi, 2),
            'total_bets': int(total_bets),
            'wins': int((df_eval['bet_over'] & df_eval['won_over']).sum()),
            'losses': int((df_eval['bet_over'] & ~df_eval['won_over']).sum())
        }
    
    @staticmethod
    def evaluate_by_stage(df: pd.DataFrame) -> dict:
        """分阶段评估"""
        results = {}
        for stage in df['stage'].unique():
            df_stage = df[df['stage'] == stage]
            if len(df_stage) > 0:
                reg = ModelEvaluator.evaluate_regression(df_stage)
                cls = ModelEvaluator.evaluate_classification(df_stage)
                results[stage] = {**reg, **cls}
        return results
    
    @staticmethod
    def evaluate_by_year(df: pd.DataFrame) -> dict:
        """分年份评估"""
        results = {}
        for year in df['year'].unique():
            df_year = df[df['year'] == year]
            if len(df_year) > 0:
                reg = ModelEvaluator.evaluate_regression(df_year)
                cls = ModelEvaluator.evaluate_classification(df_year)
                results[int(year)] = {**reg, **cls}
        return results


# ====================== 5. 主流程 ======================
def main():
    print("=" * 60)
    print("Football Quant OS - Poisson Over/Under Model v1.0")
    print("=" * 60)
    
    # 1. 加载数据
    print("\n[Step 1] Loading World Cup Data...")
    df = load_worldcup_data(years=[2022, 2018, 2014])
    
    # 2. 特征工程
    print("\n[Step 2] Feature Engineering...")
    engineer = FeatureEngineer()
    df = engineer.build_features(df)
    
    # 3. 泊松模型
    print("\n[Step 3] Poisson Model...")
    model = PoissonOUModel()
    
    # 4. 预测示例
    print("\n[Step 4] Prediction Examples (2022)...")
    df_2022 = df[df['year'] == 2022]
    
    famous_matches = [
        ('ARGENTINA', 'SAUDI ARABIA'),
        ('GERMANY', 'JAPAN'),
        ('MOROCCO', 'SPAIN'),
        ('CROATIA', 'BRAZIL')
    ]
    
    for home, away in famous_matches:
        match = df_2022[(df_2022['home_team'] == home) & (df_2022['away_team'] == away)]
        if len(match) == 0:
            match = df_2022[(df_2022['home_team'] == away) & (df_2022['away_team'] == home)]
        
        if len(match) > 0:
            m = match.iloc[0]
            result = model.calculate_over_under(m['lambda_total'], 2.5)
            actual = m['total_goals']
            
            print(f"  {home} vs {away}:")
            print(f"    λ={result['expected_goals']}, P(Over 2.5)={result['over_prob']}, P(Under 2.5)={result['under_prob']}")
            print(f"    Actual: {actual} goals, Predicted most likely: {result['most_likely']}")
    
    # 5. 模型评估
    print("\n[Step 5] Model Evaluation...")
    evaluator = ModelEvaluator()
    
    print("\n  Overall:")
    reg = evaluator.evaluate_regression(df)
    cls = evaluator.evaluate_classification(df)
    print(f"    MAE: {reg['mae']}, RMSE: {reg['rmse']}")
    print(f"    Accuracy: {cls['accuracy']}, F1: {cls['f1_score']}")
    print(f"    ROI: {cls['roi_percent']}% ({cls['wins']}W/{cls['losses']}L)")
    
    print("\n  By Stage:")
    stage_results = evaluator.evaluate_by_stage(df)
    for stage, metrics in stage_results.items():
        print(f"    {stage}: Acc={metrics['accuracy']}, F1={metrics['f1_score']}, ROI={metrics['roi_percent']}%")
    
    print("\n  By Year:")
    year_results = evaluator.evaluate_by_year(df)
    for year, metrics in sorted(year_results.items()):
        print(f"    {year}: Acc={metrics['accuracy']}, F1={metrics['f1_score']}, ROI={metrics['roi_percent']}%")
    
    # 6. 保存结果
    print("\n[Step 6] Saving Results...")
    output = {
        'metadata': {
            'model': 'Poisson Over/Under v1.0',
            'total_matches': len(df),
            'years': sorted(df['year'].unique().tolist())
        },
        'overall': {**reg, **cls},
        'by_stage': stage_results,
        'by_year': year_results
    }
    
    output_path = DATA_DIR / "poisson_ou_evaluation.json"
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {output_path}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    
    return df


if __name__ == "__main__":
    df_result = main()
