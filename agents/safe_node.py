"""
추천(Recommend) 파이프라인 전용 safe_node.

execute 쪽 safe_node(agents/agent3_execute.py)랑 다른 점:
- AgentState엔 'status' 필드가 없어서, 실패해도 status를 따로 안 건드림
- 그냥 error_log에 기록만 하고, 그 노드가 채웠어야 할 state 값은 비워둔 채로 다음 노드로 넘어감
  (예: collect_price 실패하면 price_data가 빈 채로 calculate_indicators로 넘어감 → 빈 결과로 계속 진행)
"""


def safe_node(node_fn):
    def wrapped(state) -> dict:
        try:
            return node_fn(state)
        except Exception as e:
            return {
                "error_log": state.get("error_log", [])
                + [{"node": node_fn.__name__, "error": str(e)}]
            }

    wrapped.__name__ = f"safe_{node_fn.__name__}"
    return wrapped
