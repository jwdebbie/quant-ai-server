from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Quant AI Server")


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