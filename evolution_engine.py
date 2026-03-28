#!/usr/bin/env python3
"""
로또 4등 최적화 - 진화 엔진
- 상위 전략 조합하여 새로운 전략 생성
- 대시보드 HTML 생성
- 예측 서비스
"""

import json
import random
import os
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple
from backtest_engine import (
    BacktestEngine, LottoStrategy,
    HotStrategy, ColdStrategy, DistributionStrategy,
    SumRangeStrategy, PairStrategy, OddEvenBalanceStrategy,
    HighLowBalanceStrategy, EndDigitStrategy
)


# ============================================================
# 진화된 하이브리드 전략들
# ============================================================

class HybridSumDistribution(LottoStrategy):
    """합계범위 + 균등분산 조합"""

    def __init__(self):
        super().__init__("합계+분산_v1", "합계 100~175 + 각 번호대 분산")
        self.introduced_round = 1

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        zones = [
            list(range(1, 10)),
            list(range(10, 20)),
            list(range(20, 30)),
            list(range(30, 40)),
            list(range(40, 46)),
        ]

        for _ in range(200):
            selected = []
            picks = [1, 1, 1, 1, 2]
            random.shuffle(picks)

            for i, zone in enumerate(zones):
                selected.extend(random.sample(zone, min(picks[i], len(zone))))

            if len(selected) >= 6:
                selected = selected[:6]
                if 100 <= sum(selected) <= 175:
                    return sorted(selected)

        return sorted(random.sample(range(1, 46), 6))


class HybridSumHot(LottoStrategy):
    """합계범위 + HOT 번호 조합"""

    def __init__(self):
        super().__init__("합계+HOT_v1", "합계 100~175 + 최근 HOT 번호 우선")
        self.introduced_round = 1

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        past = self.get_past_data(round_num, history, 10)

        freq = defaultdict(int)
        for h in past:
            for n in h['numbers']:
                freq[n] += 1

        # HOT 번호 (상위 20개)
        hot_nums = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)[:20]
        if len(hot_nums) < 6:
            hot_nums = list(range(1, 46))

        for _ in range(200):
            # HOT에서 4개, 나머지에서 2개
            hot_pick = random.sample(hot_nums, min(4, len(hot_nums)))
            rest_pool = [n for n in range(1, 46) if n not in hot_pick]
            rest_pick = random.sample(rest_pool, 2)

            selected = hot_pick + rest_pick
            if 100 <= sum(selected) <= 175:
                return sorted(selected)

        return sorted(random.sample(range(1, 46), 6))


class HybridDistributionPair(LottoStrategy):
    """균등분산 + 궁합 조합"""

    def __init__(self):
        super().__init__("분산+궁합_v1", "번호대 분산 + 궁합 좋은 쌍 포함")
        self.introduced_round = 1

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        past = self.get_past_data(round_num, history, 50)

        # 궁합 계산
        pair_freq = defaultdict(int)
        for h in past:
            nums = h['numbers']
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    pair = tuple(sorted([nums[i], nums[j]]))
                    pair_freq[pair] += 1

        # 상위 궁합 쌍
        top_pairs = sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        if top_pairs:
            # 상위 궁합에서 1쌍 선택
            best_pair = list(random.choice(top_pairs)[0])
        else:
            best_pair = random.sample(range(1, 46), 2)

        # 나머지 4개는 분산으로
        zones = [
            list(range(1, 10)),
            list(range(10, 20)),
            list(range(20, 30)),
            list(range(30, 40)),
            list(range(40, 46)),
        ]

        selected = list(best_pair)
        for zone in zones:
            available = [n for n in zone if n not in selected]
            if available and len(selected) < 6:
                selected.append(random.choice(available))

        while len(selected) < 6:
            n = random.randint(1, 45)
            if n not in selected:
                selected.append(n)

        return sorted(selected[:6])


class HybridOddEvenSum(LottoStrategy):
    """홀짝균형 + 합계범위 조합"""

    def __init__(self):
        super().__init__("홀짝+합계_v1", "홀수3 짝수3 + 합계 100~175")
        self.introduced_round = 1

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        odds = [n for n in range(1, 46) if n % 2 == 1]
        evens = [n for n in range(1, 46) if n % 2 == 0]

        for _ in range(200):
            selected = random.sample(odds, 3) + random.sample(evens, 3)
            if 100 <= sum(selected) <= 175:
                return sorted(selected)

        return sorted(random.sample(odds, 3) + random.sample(evens, 3))


class HybridHighLowSum(LottoStrategy):
    """고저균형 + 합계범위 조합"""

    def __init__(self):
        super().__init__("고저+합계_v1", "저3 고3 + 합계 100~175")
        self.introduced_round = 1

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        low = list(range(1, 23))
        high = list(range(23, 46))

        for _ in range(200):
            selected = random.sample(low, 3) + random.sample(high, 3)
            if 100 <= sum(selected) <= 175:
                return sorted(selected)

        return sorted(random.sample(low, 3) + random.sample(high, 3))


class HybridAllBalance(LottoStrategy):
    """올밸런스 - 모든 균형 조건 적용"""

    def __init__(self):
        super().__init__("올밸런스_v1", "홀짝3:3 + 고저3:3 + 합계100~175 + 분산")
        self.introduced_round = 1

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        for _ in range(500):
            nums = random.sample(range(1, 46), 6)

            # 홀짝 체크
            odd_count = len([n for n in nums if n % 2 == 1])
            if odd_count != 3:
                continue

            # 고저 체크
            low_count = len([n for n in nums if n < 23])
            if low_count != 3:
                continue

            # 합계 체크
            if not (100 <= sum(nums) <= 175):
                continue

            # 분산 체크 (최소 4개 구간)
            zones_hit = set()
            for n in nums:
                if n < 10:
                    zones_hit.add(0)
                elif n < 20:
                    zones_hit.add(1)
                elif n < 30:
                    zones_hit.add(2)
                elif n < 40:
                    zones_hit.add(3)
                else:
                    zones_hit.add(4)

            if len(zones_hit) >= 4:
                return sorted(nums)

        return sorted(random.sample(range(1, 46), 6))


class HybridHotCold(LottoStrategy):
    """HOT + COLD 혼합"""

    def __init__(self):
        super().__init__("HOT+COLD_v1", "HOT 3개 + COLD 3개 혼합")
        self.introduced_round = 1

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        past = self.get_past_data(round_num, history, 10)

        freq = defaultdict(int)
        for h in past:
            for n in h['numbers']:
                freq[n] += 1

        sorted_nums = sorted(range(1, 46), key=lambda x: freq[x], reverse=True)
        hot = sorted_nums[:15]
        cold = sorted_nums[-15:]

        for _ in range(100):
            selected = random.sample(hot, 3) + random.sample(cold, 3)
            if len(set(selected)) == 6:
                return sorted(selected)

        return sorted(random.sample(range(1, 46), 6))


class HybridEndDigitSum(LottoStrategy):
    """끝수분산 + 합계범위"""

    def __init__(self):
        super().__init__("끝수+합계_v1", "끝수 다양화 + 합계 100~175")
        self.introduced_round = 1

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        by_end = defaultdict(list)
        for n in range(1, 46):
            by_end[n % 10].append(n)

        for _ in range(200):
            ends = random.sample(range(10), 6)
            selected = []
            for end in ends:
                if by_end[end]:
                    selected.append(random.choice(by_end[end]))

            if len(selected) == 6 and 100 <= sum(selected) <= 175:
                return sorted(selected)

        return sorted(random.sample(range(1, 46), 6))


# ============================================================
# 진화 엔진
# ============================================================

class EvolutionEngine(BacktestEngine):
    """진화 기능이 추가된 백테스팅 엔진"""

    def __init__(self, data_path: str):
        super().__init__(data_path)
        self.add_evolved_strategies()

    def add_evolved_strategies(self):
        """진화된 하이브리드 전략 추가"""
        evolved = [
            HybridSumDistribution(),
            HybridSumHot(),
            HybridDistributionPair(),
            HybridOddEvenSum(),
            HybridHighLowSum(),
            HybridAllBalance(),
            HybridHotCold(),
            HybridEndDigitSum(),
        ]
        self.strategies.extend(evolved)
        self.evolution_log.append({
            'round': 1,
            'action': 'add_hybrid',
            'strategies': [s.name for s in evolved],
            'reason': '기본 전략 조합으로 하이브리드 생성'
        })

    def generate_dashboard(self, output_path: str):
        """대시보드 HTML 생성"""
        stats = self.get_statistics()
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['4등이상율'], reverse=True)

        latest_round = max(h['round'] for h in self.history)
        next_round = latest_round + 1
        predictions = self.predict_next(next_round)

        html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>로또 4등 최적화 대시보드</title>
<style>
:root {{
  --bg: #0d1117;
  --card: #161b22;
  --border: #30363d;
  --text: #c9d1d9;
  --text2: #8b949e;
  --primary: #58a6ff;
  --success: #3fb950;
  --warning: #d29922;
  --danger: #f85149;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  padding: 20px;
}}
.container {{ max-width: 1200px; margin: 0 auto; }}
h1 {{ color: var(--primary); margin-bottom: 8px; }}
.subtitle {{ color: var(--text2); margin-bottom: 24px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
}}
.card-title {{ font-size: 14px; color: var(--text2); margin-bottom: 12px; }}
.card-value {{ font-size: 32px; font-weight: bold; color: var(--primary); }}
.card-sub {{ font-size: 12px; color: var(--text2); margin-top: 4px; }}
table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}}
th, td {{
  padding: 12px 8px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}}
th {{ color: var(--text2); font-weight: 500; }}
tr:hover {{ background: rgba(88,166,255,0.1); }}
.rank {{ color: var(--warning); font-weight: bold; }}
.highlight {{ color: var(--success); font-weight: bold; }}
.balls {{ display: flex; gap: 6px; flex-wrap: wrap; }}
.ball {{
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: bold;
  color: #fff;
}}
.ball.r1 {{ background: linear-gradient(135deg, #fbc531, #f39c12); }}
.ball.r2 {{ background: linear-gradient(135deg, #74b9ff, #0984e3); }}
.ball.r3 {{ background: linear-gradient(135deg, #ff7675, #d63031); }}
.ball.r4 {{ background: linear-gradient(135deg, #636e72, #2d3436); }}
.ball.r5 {{ background: linear-gradient(135deg, #55efc4, #00b894); }}
.predict-card {{
  background: var(--card);
  border: 2px solid var(--primary);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}}
.predict-title {{ font-size: 16px; font-weight: bold; margin-bottom: 12px; }}
.predict-rate {{ color: var(--success); font-size: 13px; }}
.section {{ margin-bottom: 32px; }}
.section-title {{ font-size: 20px; margin-bottom: 16px; color: var(--text); }}
.bar {{
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
}}
.bar-fill {{
  height: 100%;
  background: var(--primary);
  border-radius: 4px;
}}
.evolution-item {{
  padding: 12px;
  border-left: 3px solid var(--primary);
  background: rgba(88,166,255,0.1);
  margin-bottom: 8px;
  border-radius: 0 8px 8px 0;
}}
</style>
</head>
<body>
<div class="container">
  <h1>🎯 로또 4등 최적화 대시보드</h1>
  <p class="subtitle">1회 ~ {latest_round}회 백테스팅 결과 | {len(self.strategies)}개 전략 | 생성: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

  <div class="grid">
    <div class="card">
      <div class="card-title">📊 분석 회차</div>
      <div class="card-value">{latest_round}</div>
      <div class="card-sub">2002년 12월 ~ 현재</div>
    </div>
    <div class="card">
      <div class="card-title">🧬 전략 수</div>
      <div class="card-value">{len(self.strategies)}</div>
      <div class="card-sub">기본 15개 + 하이브리드 8개</div>
    </div>
    <div class="card">
      <div class="card-title">🏆 최고 4등+ 달성</div>
      <div class="card-value">{sorted_stats[0][1]['4등이상']}회</div>
      <div class="card-sub">{sorted_stats[0][0]} ({sorted_stats[0][1]['4등이상율']}%)</div>
    </div>
    <div class="card">
      <div class="card-title">📈 최고 평균 일치</div>
      <div class="card-value">{max(s[1]['avg_match'] for s in sorted_stats)}</div>
      <div class="card-sub">개 / 회차</div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">🎯 {next_round}회 예측 번호 (TOP 5)</div>
'''

        # TOP 5 예측
        for i, (name, s) in enumerate(sorted_stats[:5], 1):
            pred = predictions.get(name, {})
            nums = pred.get('numbers', [])
            desc = pred.get('description', '')

            balls_html = ''
            for n in nums:
                if n < 10:
                    cls = 'r1'
                elif n < 20:
                    cls = 'r2'
                elif n < 30:
                    cls = 'r3'
                elif n < 40:
                    cls = 'r4'
                else:
                    cls = 'r5'
                balls_html += f'<div class="ball {cls}">{n}</div>'

            html += f'''
    <div class="predict-card">
      <div class="predict-title">{i}. {name} <span class="predict-rate">4등+율: {s['4등이상율']}%</span></div>
      <div class="balls" style="margin-bottom:8px">{balls_html}</div>
      <div style="font-size:12px;color:var(--text2)">{desc}</div>
    </div>
'''

        html += '''
  </div>

  <div class="section">
    <div class="section-title">📊 전략별 성과 순위</div>
    <div class="card">
      <table>
        <tr>
          <th>순위</th>
          <th>전략명</th>
          <th>4등+</th>
          <th>4등+율</th>
          <th>5등+</th>
          <th>평균일치</th>
          <th>성과</th>
        </tr>
'''

        for i, (name, s) in enumerate(sorted_stats, 1):
            bar_width = min(s['4등이상율'] * 100, 100)
            html += f'''
        <tr>
          <td class="rank">{i}</td>
          <td>{name}</td>
          <td class="highlight">{s['4등이상']}</td>
          <td>{s['4등이상율']}%</td>
          <td>{s['5등이상']}</td>
          <td>{s['avg_match']}</td>
          <td style="width:100px"><div class="bar"><div class="bar-fill" style="width:{bar_width}%"></div></div></td>
        </tr>
'''

        html += '''
      </table>
    </div>
  </div>

  <div class="section">
    <div class="section-title">🧬 전략 진화 이력</div>
    <div class="card">
'''

        for log in self.evolution_log:
            html += f'''
      <div class="evolution-item">
        <strong>{log['round']}회:</strong> {log['action']}<br>
        <span style="color:var(--text2)">{log['reason']}</span><br>
        <span style="color:var(--primary)">{', '.join(log.get('strategies', []))}</span>
      </div>
'''

        html += '''
    </div>
  </div>

</div>
</body>
</html>
'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"📊 대시보드 생성: {output_path}")


# ============================================================
# 메인 실행
# ============================================================

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'lotto_data.json')
    results_path = os.path.join(script_dir, 'backtest_results.json')
    dashboard_path = os.path.join(script_dir, 'dashboard.html')

    print("🧬 진화 엔진 시작...")
    engine = EvolutionEngine(data_path)

    print(f"\n📊 전략 수: {len(engine.strategies)}개")
    print("  - 기본 전략: 15개")
    print("  - 하이브리드 전략: 8개")

    print("\n🚀 백테스팅 실행...")
    engine.run_backtest(start_round=1)

    print("\n📈 결과 요약:")
    engine.print_summary()

    print("\n💾 결과 저장...")
    engine.save_results(results_path)

    print("\n📊 대시보드 생성...")
    engine.generate_dashboard(dashboard_path)

    # 다음 회차 예측
    latest_round = max(h['round'] for h in engine.history)
    next_round = latest_round + 1
    stats = engine.get_statistics()
    predictions = engine.predict_next(next_round)

    print(f"\n{'='*60}")
    print(f"🎯 {next_round}회 예측 번호 (TOP 5)")
    print('='*60)

    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['4등이상율'], reverse=True)[:5]
    for i, (name, s) in enumerate(sorted_stats, 1):
        pred = predictions[name]
        print(f"\n{i}. [{name}] (4등+율: {s['4등이상율']}%)")
        print(f"   번호: {pred['numbers']}")
        print(f"   설명: {pred['description']}")


if __name__ == '__main__':
    main()
