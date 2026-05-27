import yfinance as yf
import pandas as pd
import os
from datetime import datetime

TICKERS_OVERSEAS = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]
TICKERS_DOMESTIC = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER

def collect_overseas_prices() -> dict:
    result = {}
    for ticker in TICKERS_OVERSEAS:
        df = yf.download(ticker, period="1y", auto_adjust=True)
        df.columns = df.columns.get_level_values(0)
        result[ticker] = df
        print(f"{ticker} 수집 완료: {len(df)}개 데이터")
    return result

def save_to_csv(price_data: dict):
    os.makedirs("data", exist_ok=True)
    for ticker, df in price_data.items():
        path = f"data/{ticker}.csv"
        df.to_csv(path)
        print(f"{ticker} CSV 저장 완료: {path}")

if __name__ == "__main__":
    print("해외 주가 수집 시작...")
    price_data = collect_overseas_prices()
    save_to_csv(price_data)
    print("완료!")
