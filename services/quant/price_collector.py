import yfinance as yf
import pandas as pd
import os
import json
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from services.config import STOCK_LIST, STOCK_CODES

load_dotenv()

TICKERS_OVERSEAS = []
TICKERS_DOMESTIC = STOCK_CODES  # config.py에서 가져옴

# ── 재시도 로직 ──────────────────────────────────────────────
def _download_with_retry(ticker: str, period: str = "1y", max_retry: int = 3) -> pd.DataFrame:
    delay = 1
    for attempt in range(1, max_retry + 1):
        try:
            df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
            if not df.empty:
                df.columns = df.columns.get_level_values(0)
                return df
            raise ValueError("빈 DataFrame 반환")
        except Exception as e:
            if attempt == max_retry:
                print(f"[ERROR] {ticker} 수집 최종 실패: {e}")
                return pd.DataFrame()
            print(f"[WARN] {ticker} 수집 실패 ({attempt}/{max_retry}), {delay}초 후 재시도: {e}")
            time.sleep(delay)
            delay *= 2  # 지수 백오프: 1→2→4초
    return pd.DataFrame()


# ── 데이터 품질 검증 ─────────────────────────────────────────
def _validate(code: str, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    before = len(df)

    # 주가 0 이하 필터링
    df = df[df["Close"] > 0]

    # 등락률 ±30% 초과 이상치 감지 (제거하지 않고 경고만)
    pct = df["Close"].pct_change().abs()
    spikes = df[pct > 0.30]
    if not spikes.empty:
        print(f"[WARN] {code} 등락률 ±30% 초과 {len(spikes)}건 감지:")
        for date, row in spikes.iterrows():
            print(f"       {date.date()} 종가={row['Close']:,.0f}  등락률={pct[date]:.1%}")

    after = len(df)
    if after < before:
        print(f"[INFO] {code} 이상 데이터 {before - after}건 제거 ({before}→{after})")

    return df


# ── 수집 실패 로그 ────────────────────────────────────────────
_fail_log: list[dict] = []

def _record_fail(code: str, reason: str):
    _fail_log.append({
        "stock_code": code,
        "reason":     reason,
        "failed_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    print(f"[FAIL] {code} 수집 실패 기록: {reason}")


def get_fail_log() -> list[dict]:
    return _fail_log


def clear_fail_log():
    _fail_log.clear()


# ── 주가 수집 ────────────────────────────────────────────────
def collect_overseas_prices() -> dict:
    result = {}
    for ticker in TICKERS_OVERSEAS:
        df = _download_with_retry(ticker)
        if df.empty:
            _record_fail(ticker, "yfinance 수집 실패")
            continue
        df = _validate(ticker, df)
        result[ticker] = df
        print(f"{ticker} 수집 완료: {len(df)}개 데이터")
    return result


def collect_domestic_prices() -> dict:
    result = {}
    for code in TICKERS_DOMESTIC:
        df = _download_with_retry(f"{code}.KS")
        if df.empty:
            _record_fail(code, "yfinance 수집 실패")
            continue
        df = _validate(code, df)
        result[code] = df
        print(f"{code}({STOCK_LIST.get(code, '')}) 수집 완료: {len(df)}개 데이터")
    return result


def save_to_csv(price_data: dict):
    os.makedirs("data", exist_ok=True)
    for ticker, df in price_data.items():
        path = f"data/{ticker}.csv"
        df.to_csv(path)
        print(f"{ticker} CSV 저장 완료: {path}")


# ── 현재가 조회 (yfinance) ────────────────────────────────────
def get_current_price_yfinance(stock_code: str) -> int:
    try:
        ticker = yf.Ticker(f"{stock_code}.KS")
        price = ticker.fast_info["last_price"]
        return int(price) if price and price > 0 else 0
    except Exception as e:
        print(f"[WARN] {stock_code} yfinance 현재가 조회 실패: {e}")
        return 0


# ── 현재가 Redis 저장 ─────────────────────────────────────────
def save_current_prices_to_redis(redis_client) -> dict:
    saved = {}

    for code in TICKERS_DOMESTIC:
        price = get_current_price_yfinance(code)
        if price <= 0:
            print(f"[WARN] {code} 현재가 0원 — Redis 저장 건너뜀")
            continue

        value = json.dumps({
            "price":     price,
            "updatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        redis_client.set(f"price:{code}", value)
        saved[code] = price
        print(f"price:{code} → {price:,}원 저장 완료")

    return saved


if __name__ == "__main__":
    import sys

    # ── 주가 수집 테스트 ──────────────────────────────────────
    print("=== 국내 주가 수집 시작 ===")
    price_data = collect_domestic_prices()
    print(f"\n수집 완료: {len(price_data)}/{len(TICKERS_DOMESTIC)}종목")

    fails = get_fail_log()
    if fails:
        print(f"\n[실패 목록] {len(fails)}건:")
        for f in fails:
            print(f"  {f['stock_code']}: {f['reason']}")

    # ── Redis 저장 테스트 (fakeredis 우선, 없으면 실제 Redis) ──
    print("\n=== 현재가 Redis 저장 테스트 ===")
    try:
        import fakeredis
        r = fakeredis.FakeRedis(decode_responses=True)
        print("[INFO] fakeredis 사용 (로컬 테스트 모드)")
    except ImportError:
        import redis as _redis
        r = _redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
        )
        print("[INFO] 실제 Redis 사용")

    try:
        saved = save_current_prices_to_redis(r)
        print(f"\nRedis 저장 완료: {len(saved)}/{len(TICKERS_DOMESTIC)}종목")
        # 저장된 값 확인
        for code in list(saved.keys())[:3]:
            val = r.get(f"price:{code}")
            print(f"  price:{code} = {val}")
    except Exception as e:
        print(f"[ERROR] Redis 저장 실패: {e}")
        sys.exit(1)
