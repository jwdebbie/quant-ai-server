# 시장 리포트 생성 노드
# 주가 · 지표 · 감성 데이터 종합 → Gemini API → 시장 리포트 생성

from google import genai
import os
from dotenv import load_dotenv
from models.state import AgentState

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_report(sentiment_scores: dict, strategy_result: dict) -> str:
    # 감성 점수 요약
    sentiment_summary = ""
    for stock_code, data in sentiment_scores.items():
        score = data.get("score", 0)
        count = data.get("count", 0)
        sentiment_summary += f"- {stock_code}: 감성 점수 {score} ({count}건 분석)\n"

    # 전략 결과 요약 추가
    strategy_summary = ""
    if strategy_result:
        ranked = strategy_result.get("ranked_stocks", [])[:5]  # 상위 5개
        scores = strategy_result.get("momentum_scores", {})
        for stock in ranked:
            score = scores.get(stock, 0)
            strategy_summary += f"- {stock}: 모멘텀 점수 {score:.2f}\n"

    prompt = f"""
당신은 주식 시장 전문 애널리스트입니다.
아래 데이터만 바탕으로 오늘의 시장 리포트를 작성하세요.
데이터 외 배경지식은 사용하지 마세요.

[종목별 뉴스 감성 점수]
{sentiment_summary}

[모멘텀 전략 상위 종목]
{strategy_summary}

다음 형식으로 리포트를 작성하세요.
1. 시장 전반 요약 (2~3문장)
2. 주목 종목 (모멘텀 점수와 감성 점수 종합 상위 종목)
3. 투자 시 유의사항 (1~2문장)

간결하고 전문적으로 작성하세요.
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