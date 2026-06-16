from langgraph.graph import StateGraph, END
from models.state import AgentState
from services.nlp.news_collector import collect_news_node
from services.nlp.sentiment import analyze_sentiment_node
from services.nlp.report_generator import generate_report_node
from services.portfolio_calculator import portfolio_calc_node

# 희재 노드 import
from agents.agent1_collect import collect_price_node, calculate_indicators_node
from agents.agent2_strategy import strategy_node, backtest_node

# 주원 더미 노드

# (1) 뉴스 더미 함수 교체 완료
# (2) 감성 분석 더미 함수 교체 완료
# (3) 종목 추천 근거 함수 교체 완료
# (4) 포트폴리오 계산 더미 함수 교체 완료


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
        "investment_goal": "자산 성장",
        "risk_tolerance": 5,
        "investment_period": "UNDER_1Y",
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
    print(result)