from models.state import AgentState
from services.quant.strategy import rank_stocks
from services.quant.backtest import run_backtest


def strategy_node(state: AgentState) -> dict:
    print("전략 수립 시작...")
    result = rank_stocks(state["indicators"])
    print(f"랭킹: {result['ranked_stocks']}")
    print(f"점수: {result['momentum_scores']}")
    return {"strategy_result": result}


def backtest_node(state: AgentState) -> dict:
    print("백테스트 시작...")
    ranked = state["strategy_result"]["ranked_stocks"]
    result = run_backtest(state["price_data"], ranked, top_n=3)
    print(f"기대수익률: {result['expected_return']:.2%}")
    print(f"MDD: {result['mdd']:.2%}")
    print(f"Sharpe: {result['sharpe']:.4f}")
    return {"backtest_result": result}
