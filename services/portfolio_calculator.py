# 포트폴리오 비중 계산 노드
# 사용자 성향별 비중 계산 + 종목별 매수 금액 · 수량 산출

from models.state import AgentState
from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

import time

from services.config import STOCK_LIST as STOCK_NAME

# 투자 기간 한글 변환
PERIOD_MAP = {
    "UNDER_1Y": "1년 미만",
    "1Y_TO_3Y": "1년~3년",
    "3Y_TO_5Y": "3년~5년",
    "OVER_5Y": "5년 이상"
}

# STOCK_NAME(종목코드 → 이름)은 services/config.py에서 관리

def calculate_weights(ranked_stocks: list, sentiment_scores: dict, profile_type: str, risk_tolerance: int = 3, investment_period: str = "") -> dict:

    weights = {}
    total = len(ranked_stocks)

    if profile_type == "AGGRESSIVE" or investment_period == "OVER_5Y":
        top_count = max(1, total // 3)
        mid_count = max(1, total // 3)
        remaining_count = total - top_count - mid_count

        for i, stock in enumerate(ranked_stocks):
            if i < top_count:
                weights[stock] = round(0.6 / top_count, 4)
            elif i < top_count + mid_count:
                weights[stock] = round(0.3 / mid_count, 4)
            else:
                weights[stock] = round(0.1 / remaining_count, 4) if remaining_count > 0 else 0

    elif profile_type == "STABLE" or investment_period == "UNDER_1Y":
        sorted_by_sentiment = sorted(
            ranked_stocks,
            key=lambda x: sentiment_scores.get(x, {}).get("score", 0),
            reverse=True
        )
        top_count = max(1, total // 2)
        remaining_count = total - top_count

        for i, stock in enumerate(sorted_by_sentiment):
            if i < top_count:
                weights[stock] = round(0.7 / top_count, 4)
            else:
                weights[stock] = round(0.3 / remaining_count, 4) if remaining_count > 0 else 0

    else:  # NEUTRAL
        for stock in ranked_stocks:
            weights[stock] = round(1.0 / total, 4)

    return weights



def calculate_portfolio(state: AgentState) -> dict:

    strategy_result = state.get("strategy_result", {})
    sentiment_scores = state.get("sentiment_scores", {})
    profile_type = state.get("risk_level", "NEUTRAL")
    investment_amount = state.get("investment_amount", 10000000)
    price_data = state.get("price_data", {})
    risk_tolerance = state.get("risk_tolerance", 3)        
    investment_period = state.get("investment_period", "") 

    ranked_stocks = strategy_result.get("ranked_stocks", list(STOCK_NAME.keys()))

    # 비중 계산
    weights = calculate_weights(
        ranked_stocks,
        sentiment_scores,
        profile_type,
        risk_tolerance,    
        investment_period  
    )

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
            "reason": "",  
            "sentiment": "positive" if sentiment_scores.get(stock_code, {}).get("score", 0) > 0.3 
                 else "negative" if sentiment_scores.get(stock_code, {}).get("score", 0) < 0 
                 else "caution"
        }

    print(f"포트폴리오 계산 완료 ({profile_type}): {len(portfolio)}개 종목")
    return portfolio


    
def generate_portfolio_reasons(portfolio: dict, sentiment_scores: dict, strategy_result: dict, user_info: dict = {}) -> dict:
    momentum_scores = strategy_result.get("momentum_scores", {})

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
다음 종목을 이 사용자에게 추천하는 이유를 자연스러운 문장으로 2~3문장 작성해주세요.
번호나 소제목 없이 줄글로 이어서 써주세요.
숫자나 점수는 언급하지 말고 의미만 풀어서 설명해주세요.
전문 금융 용어는 쓰지 마세요.

사용자 정보: {user_summary}

종목: {name}({stock_code})
뉴스 분위기: {"긍정적" if sentiment > 0.3 else "부정적" if sentiment < 0 else "중립적"}
주가 상승 힘: {"강함" if momentum > 2 else "약함" if momentum < 0 else "보통"}

종목 자체에 대한 일반적인 설명은 한두 문장으로 짧게만 언급하고,
이 사용자의 투자 목표, 투자 기간, 리스크 허용도를 중심으로
"왜 이 사용자에게 이 종목이 필요한지"를 더 자세히 설명해주세요.
예) "5년이라는 시간을 갖고 있다면 지금의 잠시 주춤한 흐름이 오히려 매수 기회가 될 수 있다"
    "단기간에 성과를 보고 싶은 만큼 지금의 강한 상승 흐름이 기회가 될 수 있다"
"""
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )
        portfolio[stock_code]["reason"] = response.text.strip()
        time.sleep(5)  # 호출 간 5초 대기 추가

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
    dummy_portfolio = {
        "402340": {"name": "SK스퀘어", "weight": 0.2, "amount": 2000000, "quantity": 0, "reason": ""},
    }
    dummy_sentiment = {"402340": {"score": 0.38}}
    dummy_strategy = {"momentum_scores": {"402340": 2.08}}
    dummy_user_info = {
        "investmentGoal": "안정적 수익",
        "investmentPeriod": "OVER_5Y",
        "profileType": "STABLE",
        "riskTolerance": 2
    }

    result = generate_portfolio_reasons(dummy_portfolio, dummy_sentiment, dummy_strategy, dummy_user_info)
    print(result["402340"]["reason"])