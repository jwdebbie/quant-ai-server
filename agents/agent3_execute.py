"""
국면4 - 실행(Agent3) 노드

execute_order_node: VirtualPortfolio.execute_order() 호출 (dict 반환)
notify_callback_node: 체결 결과를 A(Spring)에 HTTP 콜백
safe_node: 한 노드가 예외를 던져도 그래프 전체가 죽지 않게 감싸는 데코레이터

콜백 설계:
- POST {A_SERVER_CALLBACK_URL} (orderId는 path가 아니라 body에 포함, nullable)
  → 종목검증/잔고부족 등으로 order 자체가 안 만들어진 실패 케이스도 커버하려고
  ⚠️ 아직 현정한테 전달 전 — 합의 필요
"""

import os

import requests
from langgraph.graph import END, StateGraph

from models.execute_state import ExecuteState
from services.redis_client import get_redis_client
from services.virtual_portfolio import (
    InsufficientBalanceError,
    InsufficientHoldingError,
    InvalidStockError,
    PriceNotAvailableError,
    PriceStaleError,
    VirtualPortfolio,
)

A_SERVER_CALLBACK_URL = os.getenv(
    "A_SERVER_CALLBACK_URL", "http://localhost:8080/internal/orders/status"
)

# 예상 가능한 실패(서버 버그가 아니라 정상적인 거부 케이스)로 분류할 예외들
EXPECTED_EXECUTION_ERRORS = (
    InvalidStockError,
    InsufficientBalanceError,
    InsufficientHoldingError,
    PriceNotAvailableError,
    PriceStaleError,
)


def safe_node(node_fn):
    """노드 실행 중 예외가 나도 그래프가 죽지 않게, error_log에 기록하고 FAILED로 처리
    (execute_order_node처럼 '이 노드 실패 = 거래 실패'인 경우에 씀)"""

    def wrapped(state: ExecuteState) -> dict:
        try:
            return node_fn(state)
        except Exception as e:  # 여기서 잡아야 그래프 전체가 안 죽음
            return {
                "status": "FAILED",
                "message": str(e),
                "error_log": state.get("error_log", [])
                + [{"node": node_fn.__name__, "error": str(e)}],
            }

    wrapped.__name__ = f"safe_{node_fn.__name__}"
    return wrapped


def safe_callback_node(node_fn):
    """콜백 전용 safe wrapper. 콜백(A한테 알리기) 실패는 거래 성공/실패와 무관하므로
    status/message는 그대로 두고 error_log에만 기록"""

    def wrapped(state: ExecuteState) -> dict:
        try:
            return node_fn(state)
        except Exception as e:
            return {
                "error_log": state.get("error_log", [])
                + [{"node": node_fn.__name__, "error": f"콜백 전송 실패: {e}"}]
            }

    wrapped.__name__ = f"safe_{node_fn.__name__}"
    return wrapped


def _execute_order_node(state: ExecuteState) -> dict:
    redis_client = get_redis_client()
    try:
        portfolio = VirtualPortfolio(redis_client=redis_client, user_id=state["user_id"])
        order = portfolio.execute_order(
            stock_code=state["stock_id"],
            side=state["side"],
            quantity=state["quantity"],
        )
        return {"order": order, "status": "COMPLETED", "message": None}
    except EXPECTED_EXECUTION_ERRORS as e:
        # 사용자/데이터 문제로 인한 실패 - 정상적인 거부 케이스라 안전하게 FAILED 처리
        return {"order": None, "status": "FAILED", "message": str(e)}


def _notify_callback_node(state: ExecuteState) -> dict:
    order = state.get("order")  # dict 또는 None
    payload = {
        "orderId": order["orderId"] if order else None,
        "userId": state["user_id"],
        "stockId": state["stock_id"],
        "side": state["side"],
        "status": state["status"],
        "message": state.get("message"),
    }
    # 콜백 실패해도(네트워크 에러 등) 매매 자체는 이미 끝났으므로 safe_node가 처리하게 둠
    requests.post(A_SERVER_CALLBACK_URL, json=payload, timeout=5)
    return {}


execute_order_node = safe_node(_execute_order_node)
notify_callback_node = safe_callback_node(_notify_callback_node)


def build_execute_graph():
    graph = StateGraph(ExecuteState)
    graph.add_node("execute_order", execute_order_node)
    graph.add_node("notify_callback", notify_callback_node)

    graph.set_entry_point("execute_order")
    graph.add_edge("execute_order", "notify_callback")
    graph.add_edge("notify_callback", END)

    return graph.compile()


# 단독 실행 테스트용
if __name__ == "__main__":
    app = build_execute_graph()
    result = app.invoke(
        {
            "user_id": 999,
            "stock_id": "005930",
            "side": "BUY",
            "quantity": 1,
            "order": None,
            "status": "STARTED",
            "message": None,
            "error_log": [],
        }
    )
    print(result.get("status"), result.get("message"))