# 감성 분석 노드
#  뉴스 텍스트 → Gemini API → 호재/악재 점수 (-1.0 ~ +1.0)
#  수집된 뉴스 전체 분석 후 종목별 평균 점수 반환

from google import genai
import json
import os
import re
import time 
from dotenv import load_dotenv
from models.state import AgentState
from db.database import save_news_sentiments

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_sentiment(news_text: str) -> dict:
    prompt = f"""
당신은 주식 시장 전문가입니다.
다음 뉴스가 해당 종목 주가에 미치는 영향을 분석하세요.

점수 기준: -1.0(매우 악재) ~ +1.0(매우 호재)
뉴스: {news_text}

반드시 아래 JSON 형식으로만 응답하세요. 다른 말은 하지 마세요.
{{"score": 0.7, "reason": "이유를 여기에"}}
"""
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )

    try:
        result = json.loads(response.text)
    except:
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            result = {"score": 0.0, "reason": "분석 실패"}

    return result


    
# 종목별 뉴스 감성 분석 노드
# 수집된 뉴스 전체 → Gemini API 분석 → 종목별 평균 점수 반환

def analyze_sentiment_node(state: AgentState) -> dict:
    news_articles = state["news_articles"]
    sentiment_scores = {}

    for news in news_articles:
        stock_code = news["stock_code"]
        text = news["title"] + " " + news["content"]

        result = analyze_sentiment(text)
        
        # 각 호출 사이 4초 대기 (분당 15건 한도 안전유지 위해)
        time.sleep(4)

        if stock_code not in sentiment_scores:
            sentiment_scores[stock_code] = []
        sentiment_scores[stock_code].append(result)

    # 종목별 평균 점수 계산
    avg_scores = {}
    for stock_code, scores in sentiment_scores.items():
        avg_score = sum(s["score"] for s in scores) / len(scores)
        avg_scores[stock_code] = {
            "score": round(avg_score, 2),
            "count": len(scores)
        }
        print(f"{stock_code} 감성 점수: {avg_score:.2f} ({len(scores)}건)")
    
    # DB 저장
    try:
        from services.nlp.news_collector import collect_news_node
        # news_id_map은 state에서 가져와야 해서 일단 빈 dict로
        save_news_sentiments(avg_scores, {})
    except Exception as e:
        print(f"감성 분석 DB 저장 실패: {e}") 

    return {"sentiment_scores": avg_scores}


if __name__ == "__main__":
    # 더미 State로 테스트
    dummy_state = {
        "news_articles": [
            {
                "stock_code": "005930",
                "stock_name": "삼성전자",
                "title": "삼성전자, 3분기 영업이익 예상치 30% 상회",
                "content": "어닝 서프라이즈 달성으로 주가 상승 기대"
            }
        ]
    }
    result = analyze_sentiment_node(dummy_state)
    print(result)