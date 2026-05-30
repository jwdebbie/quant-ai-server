from langgraph.graph import StateGraph, END
from models.state import AgentState
from services.nlp.news_collector import collect_news_node
from services.nlp.sentiment import analyze_sentiment_node
from services.nlp.report_generator import generate_report_node

#임시
import os
import json

# 희재 노드 import
from agents.agent1_collect import collect_price_node, calculate_indicators_node
from agents.agent2_strategy import strategy_node, backtest_node

# 주원 더미 노드

# (1) 뉴스 더미 함수 교체 완료
# (2) 감성 분석 더미 함수 교체 완료
# (3) 종목 추천 근거 함수 교체 완료

def portfolio_calc_node(state: AgentState) -> dict:
    return {"portfolio": {}}

def execute_order_node(state: AgentState) -> dict:
    return {"orders": []}

# StateGraph 구성
def build_graph():
    graph = StateGraph(AgentState)

    # 노드 등록
    graph.add_node("collect_price", collect_price_node)
    graph.add_node("calculate_indicators", calculate_indicators_node)
    graph.add_node("collect_news", collect_news_node)
    graph.add_node("analyze_sentiment", analyze_sentiment_node)
    graph.add_node("strategy", strategy_node)
    graph.add_node("backtest", backtest_node)
    graph.add_node("portfolio_calc", portfolio_calc_node)
    graph.add_node("recommendation_reason", generate_report_node)
    graph.add_node("execute_order", execute_order_node)

    # 실행 순서 연결
    graph.set_entry_point("collect_price")
    graph.add_edge("collect_price", "calculate_indicators")
    graph.add_edge("calculate_indicators", "collect_news")
    graph.add_edge("collect_news", "analyze_sentiment")
    graph.add_edge("analyze_sentiment", "strategy")
    graph.add_edge("strategy", "backtest")
    graph.add_edge("backtest", "portfolio_calc")
    graph.add_edge("portfolio_calc", "recommendation_reason")
    graph.add_edge("recommendation_reason", "execute_order")
    graph.add_edge("execute_order", END)

    return graph.compile()


# 테스트
if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({
        "user_id": 1,
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
    # 결과 JSON 저장
    save_data = {
        "sentiment_scores": result.get("sentiment_scores", {}),
        "strategy_result": result.get("strategy_result", {}),
        "backtest_result": {
            "curve": result.get("backtest_result", {}).get("curve", []),
            "mdd": result.get("backtest_result", {}).get("mdd", 0),
            "sharpe": result.get("backtest_result", {}).get("sharpe", 0),
            "expected_return": result.get("backtest_result", {}).get("expected_return", 0),
        },
        "portfolio_reason": result.get("portfolio_reason", ""),
        "risk_level": result.get("risk_level", "AGGRESSIVE"),
        "generated_at": "2026-05-31 08:00:00"
    }

    os.makedirs("data", exist_ok=True)
    with open("data/result.json", "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    print("결과 저장 완료 → data/result.json")