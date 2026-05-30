import numpy as np
import pandas as pd


def run_backtest(price_data: dict, ranked_stocks: list, top_n: int = 3) -> dict:
    selected = ranked_stocks[:top_n]

    # 선택 종목의 종가만 추출 후 공통 날짜로 정렬
    closes = pd.DataFrame({
        code: price_data[code]["Close"]
        for code in selected
        if code in price_data
    }).dropna()

    if closes.empty:
        return {"curve": [], "mdd": 0.0, "sharpe": 0.0, "expected_return": 0.0}

    # 일별 수익률 → 균등 비중 포트폴리오
    daily_returns = closes.pct_change().dropna()
    portfolio_return = daily_returns.mean(axis=1)

    # 누적 수익률 곡선
    cumulative = (1 + portfolio_return).cumprod()
    curve = [round(v, 6) for v in cumulative.tolist()]

    # MDD (최대 낙폭)
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    mdd = round(float(drawdown.min()), 6)

    # Sharpe 비율 (무위험 수익률 = 0 가정, 연환산)
    mean_r = portfolio_return.mean()
    std_r  = portfolio_return.std()
    sharpe = round(float((mean_r / std_r) * np.sqrt(252)) if std_r > 0 else 0.0, 4)

    # 기간 전체 기대 수익률
    expected_return = round(float(cumulative.iloc[-1] - 1), 6)

    return {
        "curve":           curve,
        "mdd":             mdd,
        "sharpe":          sharpe,
        "expected_return": expected_return,
    }
