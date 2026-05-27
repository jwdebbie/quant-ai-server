from models.state import AgentState
from services.quant.price_collector import collect_overseas_prices

def collect_price_node(state: AgentState) -> dict:
    print("주가 수집 시작...")
    price_data = collect_overseas_prices()
    print("주가 수집 완료!")
    return {"price_data": price_data}

def calculate_indicators_node(state: AgentState) -> dict:
    return {"indicators": {}}
