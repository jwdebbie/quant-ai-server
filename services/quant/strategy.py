import pandas as pd


MAX_RETURN = 5.0  # 500% 초과 수익률은 데이터 이상으로 처리


def calculate_momentum_score(close: pd.Series) -> float:
    n = len(close)
    curr = float(close.iloc[-1])

    # 3개월(63거래일) · 6개월(126거래일) · 12개월(252거래일) 수익률
    ret_3m  = (curr / float(close.iloc[-63])  - 1) if n >= 63  else 0.0
    ret_6m  = (curr / float(close.iloc[-126]) - 1) if n >= 126 else 0.0
    ret_12m = (curr / float(close.iloc[-252]) - 1) if n >= 252 else 0.0

    # 비정상 수익률 감지 (yfinance 데이터 오류 방어)
    if any(abs(r) > MAX_RETURN for r in [ret_3m, ret_6m, ret_12m]):
        print(f"  [경고] 비정상 수익률 감지 → 점수 0 처리 (3M:{ret_3m:.1%} 6M:{ret_6m:.1%} 12M:{ret_12m:.1%})")
        return 0.0

    return round(ret_3m * 0.5 + ret_6m * 0.3 + ret_12m * 0.2, 4)


def rank_stocks(price_data: dict) -> dict:
    scores = {}
    for code, df in price_data.items():
        if df.empty or "Close" not in df.columns:
            continue
        scores[code] = calculate_momentum_score(df["Close"])

    ranked = sorted(scores, key=lambda c: scores[c], reverse=True)
    return {
        "ranked_stocks":   ranked,
        "momentum_scores": scores,
    }


if __name__ == "__main__":
    from services.quant.price_collector import collect_domestic_prices

    print("=== 5주차 모멘텀 전략 단독 테스트 ===\n")
    price_data = collect_domestic_prices()
    result = rank_stocks(price_data)

    ranked = result["ranked_stocks"]
    scores = result["momentum_scores"]

    print(f"{'순위':<5} {'종목':<12} {'점수':>10}  {'신호'}")
    print("-" * 40)
    for i, code in enumerate(ranked, 1):
        s = scores[code]
        bar = ("+" * int(s * 10)) if s >= 0 else ("-" * int(abs(s) * 10))
        tag = "  << 매수" if i <= 3 else ""
        print(f"{i:<5} {code:<12} {s:>10.4f}  {bar}{tag}")

    print(f"\n상위 3종목: {ranked[:3]}")
