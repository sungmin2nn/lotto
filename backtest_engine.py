#!/usr/bin/env python3
"""
로또 4등 최적화 백테스팅 엔진
- 다양한 번호 생성 방식 정의
- 1회~현재까지 시뮬레이션
- 방식별 성과 비교 및 진화
"""

import json
import random
import math
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Set, Tuple, Optional

# ============================================================
# 기본 번호 생성 방식들 (Phase 1: 15개)
# ============================================================

class LottoStrategy:
    """번호 생성 전략 기본 클래스"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.introduced_round = 1  # 도입 회차
        self.active = True

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        """번호 6개 생성 (하위 클래스에서 구현)"""
        raise NotImplementedError

    def get_past_data(self, round_num: int, history: List[Dict], n: int = 10) -> List[Dict]:
        """해당 회차 이전 n개 회차 데이터 반환"""
        past = [h for h in history if h['round'] < round_num]
        return sorted(past, key=lambda x: x['round'], reverse=True)[:n]


class HotStrategy(LottoStrategy):
    """HOT 번호 집중 - 최근 N회 출현 빈도 상위"""

    def __init__(self):
        super().__init__("HOT_집중", "최근 10회 출현 빈도 상위 번호 선택")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        past = self.get_past_data(round_num, history, 10)
        if len(past) < 3:
            return random.sample(range(1, 46), 6)

        freq = defaultdict(int)
        for h in past:
            for n in h['numbers']:
                freq[n] += 1

        # 빈도 상위 15개 중 6개 랜덤 선택
        sorted_nums = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)[:15]
        if len(sorted_nums) < 6:
            sorted_nums = list(range(1, 46))
        return sorted(random.sample(sorted_nums, 6))


class ColdStrategy(LottoStrategy):
    """COLD 역발상 - 장기 미출현 번호"""

    def __init__(self):
        super().__init__("COLD_역발상", "최근 10회 미출현 or 저빈도 번호 선택")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        past = self.get_past_data(round_num, history, 10)
        if len(past) < 3:
            return random.sample(range(1, 46), 6)

        appeared = set()
        for h in past:
            appeared.update(h['numbers'])

        # 미출현 번호
        cold = [n for n in range(1, 46) if n not in appeared]
        if len(cold) >= 6:
            return sorted(random.sample(cold, 6))

        # 부족하면 저빈도 번호 추가
        freq = defaultdict(int)
        for h in past:
            for n in h['numbers']:
                freq[n] += 1

        all_nums = sorted(range(1, 46), key=lambda x: freq[x])
        return sorted(random.sample(all_nums[:15], 6))


class DistributionStrategy(LottoStrategy):
    """균등 분산 - 각 번호대에서 균등 선택"""

    def __init__(self):
        super().__init__("균등_분산", "1-9, 10-19, 20-29, 30-39, 40-45 각 구간에서 선택")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        zones = [
            list(range(1, 10)),    # 1-9: 9개
            list(range(10, 20)),   # 10-19: 10개
            list(range(20, 30)),   # 20-29: 10개
            list(range(30, 40)),   # 30-39: 10개
            list(range(40, 46)),   # 40-45: 6개
        ]

        # 각 구간에서 1~2개씩 선택 (총 6개)
        selected = []
        picks = [1, 1, 1, 1, 2]  # 기본 분배
        random.shuffle(picks)

        for i, zone in enumerate(zones):
            selected.extend(random.sample(zone, min(picks[i], len(zone))))

        while len(selected) < 6:
            zone = random.choice(zones)
            n = random.choice(zone)
            if n not in selected:
                selected.append(n)

        return sorted(selected[:6])


class FibonacciStrategy(LottoStrategy):
    """피보나치 - 피보나치 수열 기반"""

    def __init__(self):
        super().__init__("피보나치", "피보나치 수열 중 1-45 범위 + 인접 번호")
        self.fib = [1, 2, 3, 5, 8, 13, 21, 34]  # 45 이하 피보나치

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        # 피보나치 수 + 인접 번호들
        candidates = set(self.fib)
        for f in self.fib:
            if f > 1:
                candidates.add(f - 1)
            if f < 45:
                candidates.add(f + 1)

        candidates = [n for n in candidates if 1 <= n <= 45]

        if len(candidates) >= 6:
            return sorted(random.sample(candidates, 6))

        # 부족하면 랜덤 추가
        while len(candidates) < 6:
            n = random.randint(1, 45)
            if n not in candidates:
                candidates.append(n)

        return sorted(random.sample(candidates, 6))


class PrimeStrategy(LottoStrategy):
    """소수 - 소수만 선택"""

    def __init__(self):
        super().__init__("소수_전략", "1-45 범위의 소수 중심 선택")
        self.primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        return sorted(random.sample(self.primes, 6))


class PureRandomStrategy(LottoStrategy):
    """완전 랜덤 - 순수 랜덤"""

    def __init__(self):
        super().__init__("완전_랜덤", "순수 랜덤 선택 (기준선)")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        return sorted(random.sample(range(1, 46), 6))


class RoundSeedStrategy(LottoStrategy):
    """회차 시드 - 회차 번호 기반 시드"""

    def __init__(self):
        super().__init__("회차_시드", "회차 번호를 시드로 사용한 결정적 랜덤")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        random.seed(round_num * 7919)  # 소수 곱해서 분산
        result = sorted(random.sample(range(1, 46), 6))
        random.seed()  # 시드 초기화
        return result


class ExcludeRecentStrategy(LottoStrategy):
    """최근 제외 - 최근 N회 당첨번호 제외"""

    def __init__(self):
        super().__init__("최근_제외", "최근 3회 당첨번호 완전 제외")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        past = self.get_past_data(round_num, history, 3)

        excluded = set()
        for h in past:
            excluded.update(h['numbers'])
            if h.get('bonus'):
                excluded.add(h['bonus'])

        pool = [n for n in range(1, 46) if n not in excluded]

        if len(pool) >= 6:
            return sorted(random.sample(pool, 6))

        # 부족하면 전체에서 선택
        return sorted(random.sample(range(1, 46), 6))


class PairStrategy(LottoStrategy):
    """궁합 기반 - 함께 자주 나오는 번호"""

    def __init__(self):
        super().__init__("궁합_기반", "과거 데이터에서 함께 자주 출현한 번호 조합")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        past = self.get_past_data(round_num, history, 50)
        if len(past) < 10:
            return random.sample(range(1, 46), 6)

        # 번호 쌍 빈도 계산
        pair_freq = defaultdict(int)
        for h in past:
            nums = h['numbers']
            for i in range(len(nums)):
                for j in range(i + 1, len(nums)):
                    pair = tuple(sorted([nums[i], nums[j]]))
                    pair_freq[pair] += 1

        # 상위 쌍에서 번호 수집
        top_pairs = sorted(pair_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        candidates = set()
        for pair, _ in top_pairs:
            candidates.update(pair)

        candidates = list(candidates)
        if len(candidates) >= 6:
            return sorted(random.sample(candidates, 6))

        while len(candidates) < 6:
            n = random.randint(1, 45)
            if n not in candidates:
                candidates.append(n)

        return sorted(candidates[:6])


class OddEvenBalanceStrategy(LottoStrategy):
    """홀짝 균형 - 3:3 홀짝"""

    def __init__(self):
        super().__init__("홀짝_균형", "홀수 3개 + 짝수 3개")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        odds = [n for n in range(1, 46) if n % 2 == 1]
        evens = [n for n in range(1, 46) if n % 2 == 0]

        selected = random.sample(odds, 3) + random.sample(evens, 3)
        return sorted(selected)


class HighLowBalanceStrategy(LottoStrategy):
    """고저 균형 - 3:3 고저"""

    def __init__(self):
        super().__init__("고저_균형", "저번호(1-22) 3개 + 고번호(23-45) 3개")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        low = list(range(1, 23))
        high = list(range(23, 46))

        selected = random.sample(low, 3) + random.sample(high, 3)
        return sorted(selected)


class EndDigitStrategy(LottoStrategy):
    """끝수 분산 - 다양한 끝수"""

    def __init__(self):
        super().__init__("끝수_분산", "0~9 끝수가 최대한 다양하게")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        # 끝수별 번호 그룹
        by_end = defaultdict(list)
        for n in range(1, 46):
            by_end[n % 10].append(n)

        # 6개 끝수 선택 (중복 최소화)
        ends = random.sample(range(10), 6)
        selected = []
        for end in ends:
            if by_end[end]:
                selected.append(random.choice(by_end[end]))

        # 부족하면 추가
        while len(selected) < 6:
            n = random.randint(1, 45)
            if n not in selected:
                selected.append(n)

        return sorted(selected[:6])


class SumRangeStrategy(LottoStrategy):
    """합계 범위 - 100~175 합계"""

    def __init__(self):
        super().__init__("합계_범위", "번호 합이 100~175 범위 (통계적 최다)")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        for _ in range(100):
            nums = sorted(random.sample(range(1, 46), 6))
            if 100 <= sum(nums) <= 175:
                return nums
        return sorted(random.sample(range(1, 46), 6))


class ConsecutiveStrategy(LottoStrategy):
    """연속번호 포함 - 연속번호 1쌍 포함"""

    def __init__(self):
        super().__init__("연속번호_포함", "연속된 2개 번호 1쌍 포함")

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        # 연속 쌍 선택
        start = random.randint(1, 44)
        consecutive = [start, start + 1]

        # 나머지 4개 선택
        pool = [n for n in range(1, 46) if n not in consecutive]
        rest = random.sample(pool, 4)

        return sorted(consecutive + rest)


class GoldenRatioStrategy(LottoStrategy):
    """황금비율 - 황금비 기반 번호 선택"""

    def __init__(self):
        super().__init__("황금비율", "황금비(1.618) 기반 번호 간격")
        self.phi = 1.618033988749

    def generate(self, round_num: int, history: List[Dict]) -> List[int]:
        # 시작점 랜덤
        start = random.randint(1, 10)
        selected = [start]

        # 황금비 간격으로 번호 추가
        for i in range(1, 6):
            next_num = int(start + (45 - start) * (1 - 1/self.phi**i))
            next_num = max(1, min(45, next_num))
            if next_num not in selected:
                selected.append(next_num)

        # 부족하면 랜덤 추가
        while len(selected) < 6:
            n = random.randint(1, 45)
            if n not in selected:
                selected.append(n)

        return sorted(selected[:6])


# ============================================================
# 백테스팅 엔진
# ============================================================

class BacktestEngine:
    """백테스팅 엔진"""

    def __init__(self, data_path: str):
        self.data_path = data_path
        self.history = self.load_data()
        self.strategies = self.init_strategies()
        self.results = {}  # {round: {strategy_name: {numbers, match, rank}}}
        self.evolution_log = []  # 방식 진화 이력

    def load_data(self) -> List[Dict]:
        """로또 데이터 로드"""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return sorted(data, key=lambda x: x['round'])

    def init_strategies(self) -> List[LottoStrategy]:
        """기본 전략들 초기화"""
        return [
            HotStrategy(),
            ColdStrategy(),
            DistributionStrategy(),
            FibonacciStrategy(),
            PrimeStrategy(),
            PureRandomStrategy(),
            RoundSeedStrategy(),
            ExcludeRecentStrategy(),
            PairStrategy(),
            OddEvenBalanceStrategy(),
            HighLowBalanceStrategy(),
            EndDigitStrategy(),
            SumRangeStrategy(),
            ConsecutiveStrategy(),
            GoldenRatioStrategy(),
        ]

    def check_match(self, prediction: List[int], actual: List[int], bonus: int) -> Tuple[int, str]:
        """당첨 확인 (일치 개수, 등수)"""
        match_count = len(set(prediction) & set(actual))
        bonus_match = bonus in prediction

        if match_count == 6:
            return match_count, "1등"
        elif match_count == 5 and bonus_match:
            return match_count, "2등"
        elif match_count == 5:
            return match_count, "3등"
        elif match_count == 4:
            return match_count, "4등"
        elif match_count == 3:
            return match_count, "5등"
        else:
            return match_count, "낙첨"

    def run_backtest(self, start_round: int = 1, end_round: Optional[int] = None):
        """백테스팅 실행"""
        if end_round is None:
            end_round = max(h['round'] for h in self.history)

        print(f"🚀 백테스팅 시작: {start_round}회 ~ {end_round}회")
        print(f"📊 전략 수: {len(self.strategies)}개")
        print("-" * 60)

        for h in self.history:
            round_num = h['round']
            if round_num < start_round or round_num > end_round:
                continue

            actual = h['numbers']
            bonus = h.get('bonus', 0)

            self.results[round_num] = {}

            for strategy in self.strategies:
                if not strategy.active:
                    continue
                if round_num < strategy.introduced_round:
                    continue

                # 번호 생성 (해당 회차 이전 데이터만 사용)
                prediction = strategy.generate(round_num, self.history)
                match_count, rank = self.check_match(prediction, actual, bonus)

                self.results[round_num][strategy.name] = {
                    'numbers': prediction,
                    'match': match_count,
                    'rank': rank,
                    'actual': actual,
                    'bonus': bonus
                }

            if round_num % 100 == 0:
                print(f"  ✅ {round_num}회 완료")

        print("-" * 60)
        print("✅ 백테스팅 완료!")

    def get_statistics(self) -> Dict:
        """전체 통계 계산"""
        stats = {}

        for strategy in self.strategies:
            name = strategy.name
            results = []

            for round_num, round_results in self.results.items():
                if name in round_results:
                    results.append(round_results[name])

            if not results:
                continue

            total = len(results)
            rank_counts = defaultdict(int)
            match_sum = 0

            for r in results:
                rank_counts[r['rank']] += 1
                match_sum += r['match']

            stats[name] = {
                'total': total,
                'avg_match': round(match_sum / total, 2),
                '1등': rank_counts['1등'],
                '2등': rank_counts['2등'],
                '3등': rank_counts['3등'],
                '4등': rank_counts['4등'],
                '5등': rank_counts['5등'],
                '4등이상': rank_counts['1등'] + rank_counts['2등'] + rank_counts['3등'] + rank_counts['4등'],
                '4등이상율': round((rank_counts['1등'] + rank_counts['2등'] + rank_counts['3등'] + rank_counts['4등']) / total * 100, 2),
                '5등이상': rank_counts['1등'] + rank_counts['2등'] + rank_counts['3등'] + rank_counts['4등'] + rank_counts['5등'],
                '5등이상율': round((rank_counts['1등'] + rank_counts['2등'] + rank_counts['3등'] + rank_counts['4등'] + rank_counts['5등']) / total * 100, 2),
            }

        return stats

    def print_summary(self):
        """결과 요약 출력"""
        stats = self.get_statistics()

        print("\n" + "=" * 70)
        print("📊 백테스팅 결과 요약")
        print("=" * 70)

        # 4등 이상 비율로 정렬
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['4등이상율'], reverse=True)

        print(f"\n{'순위':<4} {'전략명':<20} {'총회차':<8} {'4등+':<6} {'4등+율':<8} {'5등+':<6} {'평균일치':<8}")
        print("-" * 70)

        for i, (name, s) in enumerate(sorted_stats, 1):
            print(f"{i:<4} {name:<20} {s['total']:<8} {s['4등이상']:<6} {s['4등이상율']:<8}% {s['5등이상']:<6} {s['avg_match']:<8}")

        print("=" * 70)

    def save_results(self, output_path: str):
        """결과 저장"""
        output = {
            'generated_at': datetime.now().isoformat(),
            'strategies': [{'name': s.name, 'description': s.description} for s in self.strategies],
            'statistics': self.get_statistics(),
            'results': {str(k): v for k, v in self.results.items()},
            'evolution_log': self.evolution_log
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n💾 결과 저장: {output_path}")

    def predict_next(self, round_num: int) -> Dict:
        """다음 회차 예측"""
        predictions = {}

        for strategy in self.strategies:
            if strategy.active:
                nums = strategy.generate(round_num, self.history)
                predictions[strategy.name] = {
                    'numbers': nums,
                    'description': strategy.description
                }

        return predictions


# ============================================================
# 메인 실행
# ============================================================

def main():
    import os

    # 데이터 경로
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'lotto_data.json')
    output_path = os.path.join(script_dir, 'backtest_results.json')

    # 엔진 초기화 및 실행
    engine = BacktestEngine(data_path)
    engine.run_backtest(start_round=1)
    engine.print_summary()
    engine.save_results(output_path)

    # 다음 회차 예측
    latest_round = max(h['round'] for h in engine.history)
    next_round = latest_round + 1

    print(f"\n🎯 {next_round}회 예측 번호")
    print("-" * 50)

    predictions = engine.predict_next(next_round)
    stats = engine.get_statistics()

    # 상위 3개 전략
    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['4등이상율'], reverse=True)[:3]

    for name, s in sorted_stats:
        pred = predictions[name]
        print(f"\n[{name}] (4등이상율: {s['4등이상율']}%)")
        print(f"  번호: {pred['numbers']}")
        print(f"  설명: {pred['description']}")


if __name__ == '__main__':
    main()
