from models.state import AgentState


def strategy_node(state: AgentState) -> dict:
    return {"strategy_result": {}}


def backtest_node(state: AgentState) -> dict:
    return {"backtest_result": {}}
