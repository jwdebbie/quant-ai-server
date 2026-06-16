from fastapi import FastAPI
from pydantic import BaseModel
from agents.graph import build_graph
import json

app = FastAPI(title="Quant AI Server")

# Spring에서 받는 입력 형태
class AgentRequest(BaseModel):
    user_id: int
    investmentGoal: str       # 투자 목표 텍스트
    riskTolerance: int        # 리스크 수용 정도 (1~5)
    investmentPeriod: str     # UNDER_1Y / 1Y_TO_3Y / 3Y_TO_5Y / OVER_5Y
    investableAmount: int     # 투자 가능 금액
    profileType: str          # AGGRESSIVE / NEUTRAL / STABLE

# Spring으로 돌려주는 응답 형태
class PortfolioResponse(BaseModel):
    portfolio: dict
    backtest_result: dict
    report: str
    risk_type: str

class ReportResponse(BaseModel):
    sentiment_scores: dict
    report: str

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Quant AI Server Running"}

@app.post("/agent/run")
def run_agent(request: AgentRequest):
    graph = build_graph()
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
        "orders": [],
        "news_articles": [],
        "sentiment_scores": {},
        "portfolio": {},
        "portfolio_reason": "",
        "risk_ok": False,
        "error_log": []
    })
    return PortfolioResponse(
        portfolio=result.get("portfolio", {}),
        backtest_result=result.get("backtest_result", {}),
        report=result.get("portfolio_reason", ""),
        risk_type=request.profileType
    )

@app.post("/report/generate")
def generate_report():
    graph = build_graph()
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
        "orders": [],
        "news_articles": [],
        "sentiment_scores": {},
        "portfolio": {},
        "portfolio_reason": "",
        "risk_ok": False,
        "error_log": []
    })
    return ReportResponse(
        sentiment_scores=result.get("sentiment_scores", {}),
        report=result.get("portfolio_reason", "")
    )