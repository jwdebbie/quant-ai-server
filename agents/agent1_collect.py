from models.state import AgentState


def collect_price_node(state: AgentState) -> dict:
    return {"price_data": {}}


def calculate_indicators_node(state: AgentState) -> dict:
    return {"indicators": {}}
