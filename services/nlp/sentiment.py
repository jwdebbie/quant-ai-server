# gemini api 테스트 코드

from google import genai
import json
import os
import re
from dotenv import load_dotenv

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
        model="gemini-2.5-flash-lite",
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


# 테스트
if __name__ == "__main__":
    news = "삼성전자, 3분기 영업이익 예상치 30% 상회하며 어닝 서프라이즈 달성"
    result = analyze_sentiment(news)
    print(result)