import pandas as pd


def score_stock(code: str, ind: dict) -> float:
    score = 0.0

    # RSI: 30~70 사이면 정상, 50 초과면 상승 모멘텀
    rsi = float(ind["RSI"].iloc[-1])
    if 30 < rsi < 70:
        score += (rsi - 50) / 20  # -1.0 ~ +1.0

    # MACD 히스토그램 양수 = 상승 신호
    macd_hist = float(ind["MACD_hist"].iloc[-1])
    score += 1.0 if macd_hist > 0 else -1.0

    # 종가가 MA20 위 = 상승 추세
    close = float(ind["MA5"].iloc[-1])   # MA5 ≈ 현재가 근사
    ma20  = float(ind["MA20"].iloc[-1])
    score += 1.0 if close > ma20 else -1.0

    # 종가가 MA60 위 = 장기 상승 추세
    ma60 = float(ind["MA60"].iloc[-1])
    score += 0.5 if close > ma60 else -0.5

    # 거래량 급등 = 관심 증가
    volume_spike = bool(ind["volume_spike"].iloc[-1])
    score += 0.5 if volume_spike else 0.0

    return round(score, 4)


def rank_stocks(indicators: dict) -> dict:
    scores = {code: score_stock(code, ind) for code, ind in indicators.items()}
    ranked = sorted(scores, key=lambda c: scores[c], reverse=True)
    return {
        "ranked_stocks":   ranked,
        "momentum_scores": scores,
    }
