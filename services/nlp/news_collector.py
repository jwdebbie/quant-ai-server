# 뉴스 수집 노드
# 네이버 뉴스 API로 종목별 최신 뉴스 수집 → CSV 임시 저장

import requests
import pandas as pd
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models.state import AgentState
from db.database import save_news_articles
from services.config import STOCK_LIST, STOCK_TO_CORP

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 조회할 종목 목록, 종목코드 → DART 고유번호 매핑은 services/config.py에서 관리

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

DART_API_KEY = os.getenv("DART_API_KEY")

def fetch_dart_disclosures(stock_code: str, count: int = 2) -> list:
    """DART OpenAPI로 전자공시 수집"""
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": stock_code,
        "bgn_de": (datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
        "end_de": datetime.now().strftime("%Y%m%d"),
        "page_count": count
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "000":
                return data.get("list", [])
    except Exception as e:
        print(f"DART 수집 오류: {e}")
    return []

def collect_news_to_csv():
    all_news = []

    for stock_code, stock_name in STOCK_LIST.items():
        # 네이버 뉴스 수집 (5건)
        news_list = fetch_news(stock_name, display=5)
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
        print(f"{stock_name} 네이버 뉴스 {len(news_list)}건 수집 완료")

        # DART 공시 수집 (2건)
        corp_code = STOCK_TO_CORP.get(stock_code)
        if corp_code:
            dart_list = fetch_dart_disclosures(corp_code, count=2)
            for dart in dart_list:
                all_news.append({
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "title": dart.get("report_nm", "").strip(),
                    "content": f"공시유형: {dart.get('corp_cls', '')} | 접수일: {dart.get('rcept_dt', '')}",
                    "published_at": dart.get("rcept_dt", ""),
                    "source": "dart",
                    "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            print(f"{stock_name} DART 공시 {len(dart_list)}건 수집 완료")

    df = pd.DataFrame(all_news)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/news_articles.csv", index=False, encoding="utf-8-sig")
    print(f"\n총 {len(all_news)}건 저장 완료 → data/news_articles.csv")
    
    # DB 저장 + news_id_map 받기 (전엔 결과를 버리고 있었음)
    news_id_map = {}
    try:
        news_id_map = save_news_articles(all_news)
    except Exception as e:
        print(f"DB 저장 실패 (CSV는 정상 저장됨): {e}")
    
    return all_news, news_id_map

if __name__ == "__main__":
    collect_news_to_csv()
    
    
def collect_news_node(state: AgentState) -> dict:
    news_list, news_id_map = collect_news_to_csv()
    return {"news_articles": news_list, "news_id_map": news_id_map}