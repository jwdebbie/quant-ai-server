from models.state import AgentState
from services.quant.price_collector import collect_overseas_prices, collect_domestic_prices
from services.quant.indicators import calculate_indicators

def collect_price_node(state: AgentState) -> dict:
    print("주가 수집 시작...")
    overseas = collect_overseas_prices()
    domestic = collect_domestic_prices()
    print("주가 수집 완료!")
    return {"price_data": {**overseas, **domestic}}

def calculate_indicators_node(state: AgentState) -> dict:
    print("지표 계산 시작...")
    indicators = {}
    for code, df in state["price_data"].items():
        indicators[code] = calculate_indicators(df)
        print(f"{code} 지표 계산 완료")
    print("지표 계산 완료!")
    return {"indicators": indicators}
