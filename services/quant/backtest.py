import numpy as np
import pandas as pd
from services.quant.strategy import calculate_momentum_score

MIN_HISTORY = 63  # 3개월 수익률 계산에 필요한 최소 거래일


def run_backtest(price_data: dict, ranked_stocks: list, top_n: int = 3) -> dict:
    # 전체 종가 DataFrame (공통 날짜 기준)
    all_closes = pd.DataFrame({
        code: price_data[code]["Close"]
        for code in price_data
        if not price_data[code].empty and "Close" in price_data[code].columns
    }).dropna(how="all")

    empty_result = {
        "top_stocks":      ranked_stocks[:top_n],
        "curve":           [1.0],
        "monthly_returns": [],
        "mdd":             0.0,
        "sharpe":          0.0,
        "expected_return": 0.0,
    }

    if all_closes.empty or len(all_closes) < MIN_HISTORY:
        return empty_result

    # 월말 리밸런싱 날짜 목록
    monthly_dates = all_closes.resample("ME").last().index.tolist()
    if len(monthly_dates) < 2:
        return empty_result

    portfolio_value = 1.0
    curve = [1.0]
    monthly_returns = []

    for i in range(len(monthly_dates) - 1):
        rebalance_date = monthly_dates[i]
        next_date      = monthly_dates[i + 1]

        # 리밸런싱 시점까지 이용 가능한 데이터만 사용 (look-ahead bias 제거)
        history = all_closes[all_closes.index <= rebalance_date]
        if len(history) < MIN_HISTORY:
            continue

        # 그 시점 모멘텀 점수로 종목 선택
        scores = {}
        for code in all_closes.columns:
            series = history[code].dropna()
            scores[code] = calculate_momentum_score(series) if len(series) >= MIN_HISTORY else -999.0

        selected = [
            c for c in sorted(scores, key=lambda c: scores[c], reverse=True)
            if scores[c] > -999.0
        ][:top_n]

        if not selected:
            continue

        # 다음 달 수익률 계산
        period = all_closes.loc[
            (all_closes.index > rebalance_date) & (all_closes.index <= next_date),
            selected
        ]

        if len(period) < 2:
            monthly_returns.append(0.0)
            curve.append(round(portfolio_value, 6))
            continue

        daily_ret  = period.pct_change().dropna()
        port_daily = daily_ret.mean(axis=1)
        monthly_ret = float((1 + port_daily).prod() - 1)

        portfolio_value *= (1 + monthly_ret)
        monthly_returns.append(round(monthly_ret, 6))
        curve.append(round(portfolio_value, 6))

    if not monthly_returns:
        return empty_result

    # MDD (최고점 대비 최대 낙폭)
    curve_s     = pd.Series(curve)
    drawdown    = (curve_s - curve_s.cummax()) / curve_s.cummax()
    mdd         = round(float(drawdown.min()), 6)

    # Sharpe (월별 기준 × √12)
    m_series = pd.Series(monthly_returns)
    mean_m   = m_series.mean()
    std_m    = m_series.std()
    sharpe   = round(float((mean_m / std_m) * np.sqrt(12)) if std_m > 0 else 0.0, 4)

    # 기대수익률 (전체 누적)
    expected_return = round(float(curve[-1] - 1), 6)

    return {
        "top_stocks":      ranked_stocks[:top_n],
        "curve":           curve,
        "monthly_returns": monthly_returns,
        "mdd":             mdd,
        "sharpe":          sharpe,
        "expected_return": expected_return,
    }


if __name__ == "__main__":
    from services.quant.price_collector import collect_domestic_prices
    from services.quant.strategy import rank_stocks

    print("=== 6주차 롤링 백테스트 단독 테스트 ===\n")
    price_data = collect_domestic_prices()
    strategy   = rank_stocks(price_data)
    ranked     = strategy["ranked_stocks"]

    result = run_backtest(price_data, ranked, top_n=3)

    print(f"대상 종목:   {result['top_stocks']}")
    print(f"기대수익률:  {result['expected_return']:.2%}")
    print(f"MDD:         {result['mdd']:.2%}")
    print(f"Sharpe:      {result['sharpe']:.4f}")
    print(f"\n월별 수익률:")
    for i, r in enumerate(result["monthly_returns"], 1):
        bar = ("+" if r >= 0 else "-") * min(int(abs(r) * 100), 30)
        print(f"  {i:>2}개월: {r:>+.2%}  {bar}")
    print(f"\n자산 곡선 ({len(result['curve'])}개 값): {result['curve']}")
