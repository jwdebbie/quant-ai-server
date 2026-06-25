import os
import redis
from models.state import AgentState
from services.quant.price_collector import (
    collect_overseas_prices,
    collect_domestic_prices,
    save_current_prices_to_redis,
    get_fail_log,
)
from services.quant.indicators import calculate_indicators

def _get_redis():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=0,
        decode_responses=True,
    )

def collect_price_node(state: AgentState) -> dict:
    print("주가 수집 시작...")

    # 현재가 Redis 저장 (파이프라인 시작 직전 1회)
    try:
        r = _get_redis()
        save_current_prices_to_redis(r)
        print("현재가 Redis 저장 완료")
    except Exception as e:
        print(f"[WARN] Redis 저장 실패 (파이프라인 계속 진행): {e}")

    overseas = collect_overseas_prices()
    domestic = collect_domestic_prices()

    # 수집 실패 내역 로그
    fails = get_fail_log()
    if fails:
        print(f"[WARN] 수집 실패 {len(fails)}건: {[f['stock_code'] for f in fails]}")

    print("주가 수집 완료!")
    return {"price_data": {**overseas, **domestic}}


def calculate_indicators_node(state: AgentState) -> dict:
    print("지표 계산 시작...")
    indicators = {}
    for code, df in state["price_data"].items():
        indicators[code] = calculate_indicators(df)
        print(f"{code} 지표 계산 완료")
    print("지표 계산 완료!")
    return {"indicators": indicators}
