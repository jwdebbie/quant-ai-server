# 포트폴리오 비중 계산 노드
# 사용자 성향별 비중 계산 + 종목별 매수 금액 · 수량 산출

from models.state import AgentState
from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

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


    
def generate_portfolio_reasons(portfolio: dict, sentiment_scores: dict, strategy_result: dict, user_info: dict = {}) -> dict:
    """Gemini API로 종목별 추천 근거 생성"""
    
    momentum_scores = strategy_result.get("momentum_scores", {})
    
    # 사용자 정보 요약
    user_summary = ""
    if user_info:
        goal = user_info.get("investmentGoal", "")
        period = PERIOD_MAP.get(user_info.get("investmentPeriod", ""), "")
        profile = user_info.get("profileType", "")
        user_summary = f"투자 목표: {goal}, 투자 기간: {period}, 투자 성향: {profile}"

    for stock_code in portfolio:
        name = STOCK_NAME.get(stock_code, stock_code)
        sentiment = sentiment_scores.get(stock_code, {}).get("score", 0)
        momentum = momentum_scores.get(stock_code, 0)

        prompt = f"""
다음 종목의 포트폴리오 편입 근거를 2~3문장으로 작성해주세요.
숫자나 점수는 언급하지 말고 의미만 풀어서 설명해주세요.
전문 금융 용어는 쓰지 마세요.

{f'''
사용자 정보: {user_summary}
위 사용자 정보를 자연스럽게 녹여서 설명해주세요.
"~~한 분께" 같은 형식적인 표현은 쓰지 마세요.
대신 사용자의 투자 목표, 기간, 성향이
이 종목과 왜 잘 맞는지 자연스럽게 연결해서 설명해주세요.
예) "장기적으로 안정적인 수익을 원한다면 이 종목의 꾸준한 성장세가 도움이 될 수 있습니다."
    "단기간에 높은 수익을 노린다면 지금의 강한 상승 흐름이 기회가 될 수 있습니다."
''' if user_summary else ""}

종목: {name}({stock_code})
뉴스 분위기: {"긍정적" if sentiment > 0.3 else "부정적" if sentiment < 0 else "중립적"}
주가 상승 힘: {"강함" if momentum > 2 else "약함" if momentum < 0 else "보통"}
"""
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )
        portfolio[stock_code]["reason"] = response.text.strip()

    return portfolio


def portfolio_calc_node(state: AgentState) -> dict:
    portfolio = calculate_portfolio(state)
    
    # 추천 근거 생성
    user_info = {
        "investmentGoal": state.get("investment_goal", ""),
        "investmentPeriod": state.get("investment_period", ""),
        "profileType": state.get("risk_level", "")
    }
    
    portfolio = generate_portfolio_reasons(
        portfolio,
        state.get("sentiment_scores", {}),
        state.get("strategy_result", {}),
        user_info
    )
    
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