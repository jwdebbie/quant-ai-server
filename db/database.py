# DB 연결 설정
# 일단 로컬로

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "quant_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )

def test_connection():
    try:
        conn = get_connection()
        print("DB 연결 성공!")
        conn.close()
    except Exception as e:
        print(f"DB 연결 실패: {e}")

if __name__ == "__main__":
    test_connection()
    
def save_news_articles(news_list: list):
    conn = get_connection()
    cur = conn.cursor()
    
    saved_count = 0
    news_id_map = {}  # stock_code별 저장된 id 목록
    
    for news in news_list:
        cur.execute("""
            INSERT INTO news_articles 
            (stock_code, title, content, source, published_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            news.get("stock_code"),
            news.get("title"),
            news.get("content"),
            news.get("source"),
            news.get("published_at")
        ))
        
        news_id = cur.fetchone()[0]
        stock_code = news.get("stock_code")
        
        if stock_code not in news_id_map:
            news_id_map[stock_code] = []
        news_id_map[stock_code].append(news_id)
        saved_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"news_articles {saved_count}건 저장 완료")
    return news_id_map


def save_news_sentiments(sentiment_scores: dict, news_id_map: dict):
    conn = get_connection()
    cur = conn.cursor()
    
    saved_count = 0
    
    for stock_code, data in sentiment_scores.items():
        score = data.get("score", 0)
        reason = data.get("reason", "")
        
        # 해당 종목의 첫번째 뉴스 id 사용
        news_ids = news_id_map.get(stock_code, [])
        news_article_id = news_ids[0] if news_ids else None
        
        cur.execute("""
            INSERT INTO news_sentiments
            (news_article_id, stock_code, score, reason)
            VALUES (%s, %s, %s, %s)
        """, (
            news_article_id,
            stock_code,
            score,
            reason
        ))
        saved_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f"news_sentiments {saved_count}건 저장 완료")


def save_collection_failures(fail_log: list):
    if not fail_log:
        return
    conn = get_connection()
    cur = conn.cursor()
    for entry in fail_log:
        cur.execute(
            "INSERT INTO collection_failures (stock_code, reason, failed_at) VALUES (%s, %s, %s)",
            (entry["stock_code"], entry["reason"], entry["failed_at"]),
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"collection_failures {len(fail_log)}건 저장 완료")