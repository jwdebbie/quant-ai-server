from typing import TypedDict

class AgentState(TypedDict):
    """
    LangGraph 파이프라인 전체에서 공유되는 상태 객체
    각 노드는 자신이 담당하는 필드만 채워서 반환
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
    orders:            list   # [{stock_code, qty, price, status}]

    # ── 주원 담당 (뉴스 수집 · 감성 분석 · 포트폴리오 · 추천 근거) ──
    news_articles:     list   # [{title, content, stock_code, published_at}]
    sentiment_scores:  dict   # {stock_code: {score: float, reason: str}}
    portfolio:         dict   # {stocks: list, expected_return: float, mdd: float, sharpe: float}
    portfolio_reason:  str    # 포트폴리오 추천 근거 설명 (Claude 생성)

    # ── 현정 담당 (리스크 안전장치) ─────────────────────────
    risk_ok:           bool   # True면 주문 실행 / False면 차단
    error_log:         list   # [{node: str, error: str, timestamp: str}]