from typing import Any, Optional, TypedDict


class ExecuteState(TypedDict):
    """
    실행(Execute) 파이프라인 전용 상태 객체.

    recommend의 AgentState와는 완전히 별개 — 매매 1건 처리에만 쓰이는 가벼운 상태.
    """

    # ── 입력값 (A → AI서버, A의 리스크 검사를 이미 통과한 요청) ──
    user_id:   int
    stock_id:  str
    side:      str             # BUY / SELL
    quantity:  int             # amount = 수량 (금액 아님)

    # ── execute_order_node가 채움 ──────────────────────────
    order:     Optional[Any]   # 체결 성공 시 Order ORM 객체, 실패 시 None
    status:    str             # STARTED / COMPLETED / FAILED
    message:   Optional[str]   # 실패 사유 (성공 시 None)

    # ── 공통 ───────────────────────────────────────────────
    error_log: list