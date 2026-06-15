# 포트폴리오 비중 계산 노드
# 사용자 성향별 비중 계산 + 종목별 매수 금액 · 수량 산출

from models.state import AgentState

# 투자 기간 한글 변환
PERIOD_MAP = {
    "UNDER_1Y": "1년 미만",
    "1Y_TO_3Y": "1년~3년",
    "3Y_TO_5Y": "3년~5년",
    "OVER_5Y": "5년 이상"
}

# 종목명 매핑
STOCK_NAME = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "402340": "SK스퀘어",
    "009150": "삼성전기",
    "005380": "현대차",
    "373220": "LG에너지솔루션",
    "032830": "삼성생명",
    "028260": "삼성물산",
    "329180": "HD현대중공업",
    "000270": "기아"
}

def calculate_weights(ranked_stocks: list, sentiment_scores: dict, profile_type: str) -> dict:
    """사용자 성향별 종목 비중 계산"""

    weights = {}

    if profile_type == "AGGRESSIVE":
        # 모멘텀 상위 종목 위주 (상위 5개에 집중)
        top_stocks = ranked_stocks[:5]
        remaining = ranked_stocks[5:]
        for i, stock in enumerate(top_stocks):
            weights[stock] = 0.12  # 상위 5개 각 12%
        for stock in remaining:
            weights[stock] = 0.04  # 나머지 각 4%

    elif profile_type == "STABLE":
        # 감성 점수 좋고 변동성 낮은 종목 위주
        sorted_by_sentiment = sorted(
            sentiment_scores.keys(),
            key=lambda x: sentiment_scores.get(x, {}).get("score", 0),
            reverse=True
        )
        for i, stock in enumerate(sorted_by_sentiment):
            if i < 5:
                weights[stock] = 0.12
            else:
                weights[stock] = 0.04

    else:  # NEUTRAL
        # 균등 배분
        for stock in ranked_stocks:
            weights[stock] = 0.10

    return weights


def calculate_portfolio(state: AgentState) -> dict:
    """포트폴리오 비중 + 매수 금액 · 수량 산출"""

    strategy_result = state.get("strategy_result", {})
    sentiment_scores = state.get("sentiment_scores", {})
    profile_type = state.get("risk_level", "NEUTRAL")
    investment_amount = state.get("investment_amount", 10000000)
    price_data = state.get("price_data", {})

    ranked_stocks = strategy_result.get("ranked_stocks", list(STOCK_NAME.keys()))

    # 비중 계산
    weights = calculate_weights(ranked_stocks, sentiment_scores, profile_type)

    # 종목별 금액 · 수량 산출
    portfolio = {}
    for stock_code, weight in weights.items():
        amount = int(investment_amount * weight)
        
        # 현재가 가져오기
        current_price = 0
        if stock_code in price_data:
            try:
                current_price = int(price_data[stock_code]["MA5"].iloc[-1])
            except:
                current_price = 0

        quantity = int(amount / current_price) if current_price > 0 else 0

        portfolio[stock_code] = {
            "name": STOCK_NAME.get(stock_code, stock_code),
            "weight": weight,
            "amount": amount,
            "quantity": quantity,
            "reason": ""  # 추후 Gemini로 채울 예정
        }

    print(f"포트폴리오 계산 완료 ({profile_type}): {len(portfolio)}개 종목")
    return portfolio


def portfolio_calc_node(state: AgentState) -> dict:
    portfolio = calculate_portfolio(state)
    return {"portfolio": portfolio}


if __name__ == "__main__":
    # 더미 테스트
    dummy_state = {
        "risk_level": "AGGRESSIVE",
        "investment_amount": 10000000,
        "strategy_result": {
            "ranked_stocks": ["005930", "000660", "009150", "005380", "373220",
                            "402340", "032830", "028260", "329180", "000270"],
            "momentum_scores": {}
        },
        "sentiment_scores": {
            "005930": {"score": 0.5},
            "000660": {"score": 0.6},
        },
        "price_data": {}
    }
    result = portfolio_calc_node(dummy_state)
    print(result)