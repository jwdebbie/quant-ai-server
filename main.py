from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from agents.graph import build_recommend_graph
from agents.agent3_execute import build_execute_graph

app = FastAPI(title="Quant AI Server")


# Spring에서 받는 입력 형태 (추천)
class AgentRequest(BaseModel):
    user_id: int
    investmentGoal: str       # 투자 목표 텍스트
    riskTolerance: int        # 리스크 수용 정도 (1~5)
    investmentPeriod: str     # UNDER_1Y / 1Y_TO_3Y / 3Y_TO_5Y / OVER_5Y
    investableAmount: int     # 투자 가능 금액
    profileType: str          # AGGRESSIVE / NEUTRAL / STABLE


# Spring으로 돌려주는 응답 형태 (추천)
class PortfolioResponse(BaseModel):
    portfolio: dict
    backtest_result: dict
    report: str
    risk_type: str


class ReportResponse(BaseModel):
    sentiment_scores: dict
    report: str


# 국면4: 실행(execute) 요청/응답
class ExecuteRequest(BaseModel):
    userId: int
    stockId: str
    side: str      # BUY / SELL
    amount: int    # 수량(주식 수). 금액 아님


class ExecuteResponse(BaseModel):
    status: str               # COMPLETED / FAILED
    stockId: str
    side: str
    quantity: int
    price: Optional[float] = None
    amount: Optional[float] = None
    balanceAfter: Optional[float] = None
    message: Optional[str] = None


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Quant AI Server Running"}


@app.post("/api/portfolio/recommend")
def run_agent(request: AgentRequest):
    graph = build_recommend_graph()
    result = graph.invoke({
        "user_id": request.user_id,
        "risk_level": request.profileType,
        "investment_amount": request.investableAmount,
        "investment_goal": request.investmentGoal,
        "risk_tolerance": request.riskTolerance,
        "investment_period": request.investmentPeriod,
        "price_data": {},
        "indicators": {},
        "strategy_result": {},
        "backtest_result": {},
        "news_articles": [],
        "sentiment_scores": {},
        "portfolio": {},
        "report": "",
        "error_log": []
    })
    return PortfolioResponse(
        portfolio=result.get("portfolio", {}),
        backtest_result=result.get("backtest_result", {}),
        report=result.get("report", ""),
        risk_type=request.profileType
    )


@app.post("/report/generate")
def generate_report():
    graph = build_recommend_graph()
    result = graph.invoke({
        "user_id": 0,
        "risk_level": "NEUTRAL",
        "investment_amount": 0,
        "investment_goal": "",
        "risk_tolerance": 3,
        "investment_period": "",
        "price_data": {},
        "indicators": {},
        "strategy_result": {},
        "backtest_result": {},
        "news_articles": [],
        "sentiment_scores": {},
        "portfolio": {},
        "report": "",
        "error_log": []
    })
    return ReportResponse(
        sentiment_scores=result.get("sentiment_scores", {}),
        report=result.get("report", "")
    )


@app.post("/api/portfolio/execute")
def run_execute(request: ExecuteRequest):
    """A의 리스크 검사를 통과한 요청만 들어온다고 간주 (risk_ok 체크 없음)"""
    graph = build_execute_graph()
    result = graph.invoke({
        "user_id": request.userId,
        "stock_id": request.stockId,
        "side": request.side,
        "quantity": request.amount,
        "order": None,
        "status": "STARTED",
        "message": None,
        "error_log": [],
    })

    order = result.get("order")
    return ExecuteResponse(
        status=result.get("status", "FAILED"),
        stockId=request.stockId,
        side=request.side,
        quantity=request.amount,
        price=order["price"] if order else None,
        amount=order["amount"] if order else None,
        balanceAfter=order["balanceAfter"] if order else None,
        message=result.get("message"),
    )