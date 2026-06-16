import yfinance as yf
import pandas as pd
import os
import json
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")

TICKERS_OVERSEAS = []

TICKERS_DOMESTIC = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "402340",  # SK스퀘어
    "009150",  # 삼성전기
    "005380",  # 현대차
    "373220",  # LG에너지솔루션
    "032830",  # 삼성생명
    "028260",  # 삼성물산
    "329180",  # HD현대중공업
    "000270",  # 기아
]

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

_TOKEN_CACHE_FILE = ".kis_token.json"

def get_kis_token() -> str:
    now = datetime.now().timestamp()

    if os.path.exists(_TOKEN_CACHE_FILE):
        with open(_TOKEN_CACHE_FILE) as f:
            cached = json.load(f)
        if cached.get("token") and now < cached.get("expires_at", 0):
            return cached["token"]

    res = requests.post(
        "https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
        json={
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "grant_type": "client_credentials"
        }
    )
    data = res.json()
    if "access_token" not in data:
        raise RuntimeError(f"KIS 토큰 발급 실패: {data}")
    token = data["access_token"]
    with open(_TOKEN_CACHE_FILE, "w") as f:
        json.dump({"token": token, "expires_at": now + 23 * 3600}, f)
    return token

def get_domestic_price(token: str, stock_code: str) -> dict:
    res = requests.get(
        "https://openapivts.koreainvestment.com:29443/uapi/domestic-stock/v1/quotations/inquire-price",
        headers={
            "authorization": f"Bearer {token}",
            "tr_id": "FHKST01010100",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET
        },
        params={
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": stock_code
        }
    )
    return res.json()

def collect_domestic_prices() -> dict:
    result = {}
    for code in TICKERS_DOMESTIC:
        df = yf.download(f"{code}.KS", period="1y", auto_adjust=True)
        df.columns = df.columns.get_level_values(0)
        result[code] = df
        print(f"{code} 수집 완료: {len(df)}개 데이터")
    return result

if __name__ == "__main__":
    print("=== 해외 주가 수집 시작 ===")
    price_data = collect_overseas_prices()
    save_to_csv(price_data)

    print("\n=== 국내 주가 수집 시작 ===")
    domestic_data = collect_domestic_prices()
    print("\n국내 주가 수집 결과:", {k: len(v) for k, v in domestic_data.items()})
    print("완료!")
