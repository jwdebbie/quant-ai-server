from langgraph.graph import END, StateGraph

from models.state import AgentState
from services.nlp.news_collector import collect_news_node
from services.nlp.sentiment import analyze_sentiment_node
from services.nlp.report_generator import generate_report_node
from services.portfolio_calculator import portfolio_calc_node

# 희재 노드 import
from agents.agent1_collect import collect_price_node, calculate_indicators_node
from agents.agent2_strategy import strategy_node, backtest_node
from agents.safe_node import safe_node

# 국면4: execute_order는 별도 그래프(agents/agent3_execute.py의 build_execute_graph)로 분리됨
# recommend와 execute가 별개 API(/api/portfolio/recommend, /api/portfolio/execute)이기 때문


def build_recommend_graph():
    """추천 파이프라인 전용 그래프 (collect_price ~ recommendation_reason)

    모든 노드를 safe_node로 감싸서, 한 노드가 예외를 던져도 그래프 전체가 죽지 않고
    error_log에 기록한 뒤 다음 노드로 넘어가게 함
    """
    graph = StateGraph(AgentState)

    # 노드 등록 (전부 safe_node로 감쌈)
    graph.add_node("collect_price", safe_node(collect_price_node))
    graph.add_node("calculate_indicators", safe_node(calculate_indicators_node))
    graph.add_node("collect_news", safe_node(collect_news_node))
    graph.add_node("analyze_sentiment", safe_node(analyze_sentiment_node))
    graph.add_node("strategy", safe_node(strategy_node))
    graph.add_node("backtest", safe_node(backtest_node))
    graph.add_node("portfolio_calc", safe_node(portfolio_calc_node))
    graph.add_node("recommendation_reason", safe_node(generate_report_node))

    # 실행 순서 연결
    graph.set_entry_point("collect_price")
    graph.add_edge("collect_price", "calculate_indicators")
    graph.add_edge("calculate_indicators", "collect_news")
    graph.add_edge("collect_news", "analyze_sentiment")
    graph.add_edge("analyze_sentiment", "strategy")
    graph.add_edge("strategy", "backtest")
    graph.add_edge("backtest", "portfolio_calc")
    graph.add_edge("portfolio_calc", "recommendation_reason")
    graph.add_edge("recommendation_reason", END)

    return graph.compile()


# 테스트
if __name__ == "__main__":
    app = build_recommend_graph()
    result = app.invoke({
        "user_id": 1,
        "risk_level": "NEUTRAL",
        "investment_amount": 10000000,
        "investment_goal": "균형 잡힌 수익",
        "risk_tolerance": 3,
        "investment_period": "OVER_5Y",
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

    print("\n" + "="*50)
    print("리포트")
    print("="*50)
    print(result.get("report", ""))

    print("\n" + "="*50)
    print("포트폴리오")
    print("="*50)
    for code, data in result.get("portfolio", {}).items():
        print(f"\n{data['name']}({code}) - {data['weight']*100:.1f}%")
        print(f"금액: {data['amount']:,}원")
        print(f"추천 근거: {data['reason'][:100]}...")