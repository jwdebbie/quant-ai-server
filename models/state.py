from typing import TypedDict


class AgentState(TypedDict):
    """
    추천(Recommend) 파이프라인 전용 상태 객체.

    국면4부터 execute는 별도 상태(ExecuteState, models/execute_state.py)와
    별도 그래프(agents/agent3_execute.py)로 분리됨.

    변경 사항 (국면3 → 국면4):
    - risk_ok 제거: A가 리스크 검사를 먼저 끝내고 통과한 요청만 AI서버로 보내기로 했으므로
      AI서버 쪽에서 risk_ok를 들고 있을 이유가 없어짐
    - orders 제거: execute가 별도 API/그래프로 빠지면서 추천 파이프라인 결과물이 아니게 됨
    """

    # ── 입력값 (현정 → Python 서버로 전달) ──────────────────
    user_id:           int
    risk_level:        str    # AGGRESSIVE / NEUTRAL / STABLE
    investment_amount: int
    investment_goal:   str    # 투자 목표
    risk_tolerance:    int    # 리스크 허용도 (1~5)
    investment_period: str    # UNDER_1Y / 1Y_TO_3Y / 3Y_TO_5Y / OVER_5Y

    # ── 희재 담당 (주가 수집 · 지표 계산 · 전략 · 백테스트) ──
    price_data:        dict   # {stock_code: OHLCV DataFrame}
    indicators:        dict   # {stock_code: {RSI, MACD, BB, MA5, MA20, MA60}}
    strategy_result:   dict   # {ranked_stocks: list, momentum_scores: dict}
    backtest_result:   dict   # {curve: list, mdd: float, sharpe: float, expected_return: float}

    # ── 주원 담당 (뉴스 수집 · 감성 분석 · 포트폴리오 · 추천 근거) ──
    news_articles:     list   # [{title, content, stock_code, published_at}]
    news_id_map:       dict   # {stock_code: [DB에 저장된 news_articles.id, ...]}
    sentiment_scores:  dict   # {stock_code: {score: float, reason: str}}
    portfolio:         dict   # {stocks: list, expected_return: float, mdd: float, sharpe: float}
    report:            str

    # ── 공통 ─────────────────────────────────────────────
    error_log:         list   # [{node: str, error: str, timestamp: str}]