from fastapi import FastAPI
from pydantic import BaseModel
from agents.graph import build_graph

app = FastAPI(title="Quant AI Server")


## 웹 대시보드 (임시 시연용)
import json
from fastapi.responses import HTMLResponse

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("templates/dashboard.html", "r", encoding="utf-8") as f:
        return f.read()
@app.get("/api/result")
def get_result():
    try:
        with open("data/result.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": "분석 결과가 없습니다."}


# Spring에서 받는 입력 형태
class AgentRequest(BaseModel):
    user_id: int
    risk_level: str           # AGGRESSIVE / NEUTRAL / CONSERVATIVE
    investment_amount: int    # 투자 가능 금액 (원)


# Spring으로 돌려주는 응답 형태
class AgentResponse(BaseModel):
    portfolio: dict
    portfolio_reason: str
    orders: list


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Quant AI Server Running"}


@app.post("/agent/run")
def run_agent(request: AgentRequest):
    # 국면 1: 더미 응답
    # 국면 2~4에서 실제 StateGraph로 교체
    return AgentResponse(
        portfolio={"stocks": [], "expected_return": 0.0, "mdd": 0.0, "sharpe": 0.0},
        portfolio_reason="더미 응답입니다.",
        orders=[]
    )

class ReportResponse(BaseModel):
    sentiment_scores: dict
    portfolio_reason: str

@app.post("/report/generate")
def generate_report():
    graph = build_graph()
    result = graph.invoke({
        "user_id": 0,
        "risk_level": "AGGRESSIVE",
        "investment_amount": 10000000,
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
    # 결과 저장
    app.state.latest_result = result
    return ReportResponse(
        sentiment_scores=result.get("sentiment_scores", {}),
        portfolio_reason=result.get("portfolio_reason", "")
    )