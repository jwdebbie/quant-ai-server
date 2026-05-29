# 뉴스 수집 노드
# 네이버 뉴스 API로 종목별 최신 뉴스 수집 → CSV 임시 저장

import requests
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from models.state import AgentState

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 조회할 종목 목록 ex
STOCK_LIST = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "005380": "현대차",
    "000270": "기아"
}

def fetch_news(stock_name: str, display: int = 10) -> list:
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": f"{stock_name} 주식",
        "display": display,
        "sort": "date"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    return []


def collect_news_to_csv():
    all_news = []

    for stock_code, stock_name in STOCK_LIST.items():
        news_list = fetch_news(stock_name)
        for news in news_list:
            all_news.append({
                "stock_code": stock_code,
                "stock_name": stock_name,
                "title": news.get("title", "").replace("<b>", "").replace("</b>", ""),
                "content": news.get("description", "").replace("<b>", "").replace("</b>", ""),
                "published_at": news.get("pubDate", ""),
                "source": "naver",
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        print(f"{stock_name} 뉴스 {len(news_list)}건 수집 완료")

    df = pd.DataFrame(all_news)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/news_articles.csv", index=False, encoding="utf-8-sig")
    print(f"\n총 {len(all_news)}건 저장 완료 → data/news_articles.csv")
    return all_news


# 테스트
if __name__ == "__main__":
    collect_news_to_csv()
    
# agents/graph.py 연결가능하게 노드 형태로 변환
def collect_news_node(state: AgentState) -> dict:
    news_list = collect_news_to_csv()
    return {"news_articles": news_list}   