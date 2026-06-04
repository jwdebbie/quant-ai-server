# 시장 리포트 생성 노드
# 주가 · 지표 · 감성 데이터 종합 → Gemini API → 시장 리포트 생성

from google import genai
import os
from dotenv import load_dotenv
from models.state import AgentState

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

STOCK_NAME = {
    "005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER",
    "005380": "현대차", "000270": "기아",
    "AAPL": "애플", "TSLA": "테슬라", "NVDA": "엔비디아",
    "MSFT": "마이크로소프트", "GOOGL": "구글"
}

def generate_report(sentiment_scores: dict, strategy_result: dict) -> str:
    sentiment_summary = ""
    for stock_code, data in sentiment_scores.items():
        score = data.get("score", 0)
        count = data.get("count", 0)
        name = STOCK_NAME.get(stock_code, stock_code)
        sentiment_summary += f"- {name}({stock_code}): 감성 점수 {score} ({count}건 분석)\n"

    strategy_summary = ""
    if strategy_result:
        ranked = strategy_result.get("ranked_stocks", [])[:5]
        scores = strategy_result.get("momentum_scores", {})
        for stock in ranked:
            score = scores.get(stock, 0)
            name = STOCK_NAME.get(stock, stock)
            strategy_summary += f"- {name}({stock}): 모멘텀 점수 {score:.2f}\n"

    prompt = f"""
당신은 주식 초보자도 이해할 수 있게 설명해주는 친절한 투자 어시스턴트입니다.
아래 데이터만 바탕으로 오늘의 시장 리포트를 작성하세요.
데이터 외 배경지식은 사용하지 마세요.
이모지는 사용하지 마세요.
종목명과 코드를 함께 표기해주세요. 예) 삼성전자(005930)

주의사항 작성 시
- "감성 점수가 낮다" → "최근 부정적인 뉴스가 많다"
- "모멘텀 점수가 높다" → "주가가 강하게 오르고 있다"
- "모멘텀 점수가 낮다" → "주가 상승 힘이 약하다"
- "감성 점수가 음수다" → "시장에서 우려의 목소리가 나오고 있다"
- "지표 간 괴리가 있다" → "뉴스와 실제 주가 흐름이 엇갈리고 있다"
- "변동성이 확대될 수 있다" → "주가가 크게 오르내릴 수 있다"
- "신중한 접근이 필요하다" → "지금 당장 사기보다 조금 더 지켜보는 것이 좋을 수 있다"
- 숫자나 지표 용어는 절대 사용하지 마세요.
- 전문 금융 용어도 쓰지 마세요.

[종목별 뉴스 감성 점수]
{sentiment_summary}

[모멘텀 전략 상위 종목]
{strategy_summary}

다음 형식으로 작성하세요.

1. 오늘 시장 한줄 요약
   누구나 이해할 수 있는 쉬운 문장으로 작성

2. 주목할 종목
   각 종목마다 아래 내용을 포함해서 설명
   - 종목명(코드) 반드시 표기
   - 최근 뉴스 분위기가 어떤지
   - 주가가 지금 오르는 힘이 얼마나 강한지
   - 왜 주목해야 하는지
   점수 숫자는 직접 언급하지 말고 의미만 풀어서 설명

3. 오늘 투자 시 주의할 점
   오늘 데이터에서 발견된 구체적인 주의사항만 간결하게 작성
   일반적인 투자 조언은 쓰지 마세요
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )

    return response.text


def generate_report_node(state: AgentState) -> dict:
    sentiment_scores = state.get("sentiment_scores", {})
    strategy_result = state.get("strategy_result", {})

    print("시장 리포트 생성 중...")
    report = generate_report(sentiment_scores, strategy_result)
    print("리포트 생성 완료!")
    print(report)

    return {"portfolio_reason": report}


if __name__ == "__main__":
    dummy_state = {
        "sentiment_scores": {
            "005930": {"score": 0.12, "count": 10},
            "000660": {"score": 0.32, "count": 10},
            "035420": {"score": 0.13, "count": 10},
            "005380": {"score": 0.50, "count": 10},
            "000270": {"score": 0.30, "count": 10}
        },
        "strategy_result": {}
    }
    result = generate_report_node(dummy_state)
    print(result)