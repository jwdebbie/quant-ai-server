# 시장 리포트 생성 노드
# 주가 · 지표 · 감성 데이터 종합 → Gemini API → 시장 리포트 생성

from google import genai
import os
from dotenv import load_dotenv
from models.state import AgentState

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

STOCK_NAME = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "402340": "SK스퀘어",
    "009150": "삼성전기",
    "207940": "삼성바이오로직스",
    "005380": "현대차",
    "373220": "LG에너지솔루션",
    "032830": "삼성생명",
    "028260": "삼성물산",
    "329180": "HD현대중공업",
    "000270": "기아"
}

def generate_report(sentiment_scores: dict, strategy_result: dict, news_articles: list = []) -> str:
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

    news_summary = ""
    for stock_code in STOCK_NAME:
        titles = [a["title"] for a in news_articles if a.get("stock_code") == stock_code][:3]
        if titles:
            name = STOCK_NAME.get(stock_code, stock_code)
            news_summary += f"\n[{name}({stock_code}) 관련 뉴스]\n"
            for t in titles:
                news_summary += f"- {t}\n"

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

[종목별 실제 뉴스 제목]
{news_summary}

[모멘텀 전략 상위 종목]
{strategy_summary}

다음 형식으로 작성하세요.

1. 오늘 시장 한줄 요약
   누구나 이해할 수 있는 쉬운 문장으로 작성

2. 종목별 오늘 뉴스 흐름
   각 종목마다 아래 내용을 포함해서 설명
   - 종목명(코드) 반드시 표기
   - 실제 뉴스 제목을 참고해서 오늘 무슨 일이 있었는지 구체적으로 설명
   - 그 소식이 왜 긍정적인지 또는 부정적인지 이유 포함
   같은 표현을 반복하지 말고 다양하게 작성해주세요.

3. 오늘 시장에서 조심할 점
   오늘 뉴스에서 발견된 구체적인 주의사항만 간결하게 작성
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
    news_articles = state.get("news_articles", []) 

    print("시장 리포트 생성 중...")
    report = generate_report(sentiment_scores, strategy_result, news_articles)  # 여기도 news_articles 추가
    print("리포트 생성 완료!")
    print(report)

    return {"report": report}


if __name__ == "__main__":
    dummy_state = {
        "sentiment_scores": {
            "005930": {"score": 0.44, "count": 5},
        },
        "strategy_result": {},
        "news_articles": [
            {"stock_code": "005930", "title": "삼성전자 반도체 수요 회복 기대감 확산"},
            {"stock_code": "005930", "title": "삼성전자, 신규 AI 칩 공급 계약 체결"},
        ]
    }
    result = generate_report_node(dummy_state)