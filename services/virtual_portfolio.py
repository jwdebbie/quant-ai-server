"""
VirtualPortfolio - 사용자별 가상 계좌 관리 클래스

- db/database.py의 get_connection()을 그대로 재사용 (SQLAlchemy 안 씀, 팀 컨벤션 맞춤)
- 잔고/보유종목/평균단가는 DB(portfolios, holdings 테이블)에서 관리
- 체결 결과는 orders 테이블에 저장
- 현재가는 Redis (B파트가 price:{stock_code} 형식으로 write한 값)에서 read
- stock_code 유효성은 services/config.py의 STOCK_CODES로 검증
"""

import json
from datetime import datetime, timedelta, timezone

from db.database import get_connection
from services.config import STOCK_CODES

PRICE_STALE_THRESHOLD_MINUTES = 10
DEFAULT_INITIAL_BALANCE = 10_000_000  # 초기 가상 잔고 (1천만원), 정책 확정되면 조정


class PriceNotAvailableError(Exception):
    """Redis에 해당 종목 현재가가 없을 때"""


class PriceStaleError(Exception):
    """현재가가 임계 시간(10분) 이상 오래됐을 때"""


class InvalidStockError(Exception):
    """STOCK_CODES에 없는 종목일 때"""


class InsufficientBalanceError(Exception):
    """매수 시 잔고가 부족할 때"""


class InsufficientHoldingError(Exception):
    """매도 시 보유 수량이 부족할 때"""


class VirtualPortfolio:
    def __init__(self, redis_client, user_id: int):
        self.redis_client = redis_client
        self.user_id = user_id

    # ---------- 현재가 조회 (Redis) ----------

    def get_current_price(self, stock_code: str) -> float:
        raw = self.redis_client.get(f"price:{stock_code}")
        if raw is None:
            raise PriceNotAvailableError(f"{stock_code}의 현재가를 Redis에서 찾을 수 없습니다")

        data = json.loads(raw)
        updated_at = datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if now - updated_at > timedelta(minutes=PRICE_STALE_THRESHOLD_MINUTES):
            raise PriceStaleError(
                f"{stock_code}의 현재가가 {PRICE_STALE_THRESHOLD_MINUTES}분 이상 오래되었습니다"
            )
        return float(data["price"])

    # ---------- 매수 ----------

    def buy(self, stock_code: str, quantity: int) -> dict:
        self._validate_stock(stock_code)
        price = self.get_current_price(stock_code)
        cost = price * quantity

        conn = get_connection()
        try:
            cur = conn.cursor()

            # 잔고 조회 (없으면 생성)
            cur.execute("SELECT balance FROM portfolios WHERE user_id = %s", (self.user_id,))
            row = cur.fetchone()
            if row is None:
                balance = float(DEFAULT_INITIAL_BALANCE)
                cur.execute(
                    "INSERT INTO portfolios (user_id, balance) VALUES (%s, %s)",
                    (self.user_id, balance),
                )
            else:
                balance = float(row[0])

            if cost > balance:
                raise InsufficientBalanceError(f"잔고 부족: 필요 {cost}, 보유 {balance}")

            # 보유 종목 조회 (없으면 생성)
            cur.execute(
                "SELECT quantity, avg_price FROM holdings WHERE user_id = %s AND stock_code = %s",
                (self.user_id, stock_code),
            )
            holding_row = cur.fetchone()
            if holding_row is None:
                old_quantity, old_avg_price = 0, 0.0
                cur.execute(
                    "INSERT INTO holdings (user_id, stock_code, quantity, avg_price) "
                    "VALUES (%s, %s, 0, 0)",
                    (self.user_id, stock_code),
                )
            else:
                old_quantity, old_avg_price = holding_row[0], float(holding_row[1])

            new_quantity = old_quantity + quantity
            # 평균단가 재계산: (기존수량*기존단가 + 신규수량*신규단가) / 총수량
            new_avg_price = (old_avg_price * old_quantity + price * quantity) / new_quantity
            new_balance = balance - cost

            cur.execute(
                "UPDATE holdings SET quantity = %s, avg_price = %s, updated_at = NOW() "
                "WHERE user_id = %s AND stock_code = %s",
                (new_quantity, new_avg_price, self.user_id, stock_code),
            )
            cur.execute(
                "UPDATE portfolios SET balance = %s, updated_at = NOW() WHERE user_id = %s",
                (new_balance, self.user_id),
            )
            cur.execute(
                """
                INSERT INTO orders (user_id, stock_code, side, quantity, price, amount, balance_after)
                VALUES (%s, %s, 'BUY', %s, %s, %s, %s)
                RETURNING id
                """,
                (self.user_id, stock_code, quantity, price, cost, new_balance),
            )
            order_id = cur.fetchone()[0]

            conn.commit()
            cur.close()

            return {
                "orderId": order_id,
                "stockCode": stock_code,
                "side": "BUY",
                "quantity": quantity,
                "price": price,
                "amount": cost,
                "balanceAfter": new_balance,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ---------- 매도 ----------

    def sell(self, stock_code: str, quantity: int) -> dict:
        self._validate_stock(stock_code)
        price = self.get_current_price(stock_code)

        conn = get_connection()
        try:
            cur = conn.cursor()

            cur.execute(
                "SELECT quantity, avg_price FROM holdings WHERE user_id = %s AND stock_code = %s",
                (self.user_id, stock_code),
            )
            holding_row = cur.fetchone()
            held_quantity = holding_row[0] if holding_row else 0

            if held_quantity < quantity:
                raise InsufficientHoldingError(
                    f"보유 수량 부족: 매도요청 {quantity}, 보유 {held_quantity}"
                )

            proceeds = price * quantity
            new_quantity = held_quantity - quantity
            new_avg_price = 0.0 if new_quantity == 0 else float(holding_row[1])

            cur.execute(
                "UPDATE holdings SET quantity = %s, avg_price = %s, updated_at = NOW() "
                "WHERE user_id = %s AND stock_code = %s",
                (new_quantity, new_avg_price, self.user_id, stock_code),
            )

            cur.execute("SELECT balance FROM portfolios WHERE user_id = %s", (self.user_id,))
            balance = float(cur.fetchone()[0])
            new_balance = balance + proceeds

            cur.execute(
                "UPDATE portfolios SET balance = %s, updated_at = NOW() WHERE user_id = %s",
                (new_balance, self.user_id),
            )
            cur.execute(
                """
                INSERT INTO orders (user_id, stock_code, side, quantity, price, amount, balance_after)
                VALUES (%s, %s, 'SELL', %s, %s, %s, %s)
                RETURNING id
                """,
                (self.user_id, stock_code, quantity, price, proceeds, new_balance),
            )
            order_id = cur.fetchone()[0]

            conn.commit()
            cur.close()

            return {
                "orderId": order_id,
                "stockCode": stock_code,
                "side": "SELL",
                "quantity": quantity,
                "price": price,
                "amount": proceeds,
                "balanceAfter": new_balance,
            }
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_order(self, stock_code: str, side: str, quantity: int) -> dict:
        """side: 'BUY' 또는 'SELL'. execute_order_node에서 이 메서드 하나만 호출하면 됨"""
        if side == "BUY":
            return self.buy(stock_code, quantity)
        if side == "SELL":
            return self.sell(stock_code, quantity)
        raise ValueError(f"알 수 없는 side: {side}")

    # ---------- 평가손익 ----------

    def evaluate(self) -> dict:
        """평가손익 계산: (현재가 - 평균단가) * 보유수량, 종목별 + 전체 요약"""
        conn = get_connection()
        try:
            cur = conn.cursor()

            cur.execute("SELECT balance FROM portfolios WHERE user_id = %s", (self.user_id,))
            row = cur.fetchone()
            balance = float(row[0]) if row else float(DEFAULT_INITIAL_BALANCE)

            cur.execute(
                "SELECT stock_code, quantity, avg_price FROM holdings "
                "WHERE user_id = %s AND quantity > 0",
                (self.user_id,),
            )
            holding_rows = cur.fetchall()
            cur.close()
        finally:
            conn.close()

        holdings_eval = []
        total_unrealized_pnl = 0.0
        total_value = balance

        for stock_code, quantity, avg_price in holding_rows:
            current_price = self.get_current_price(stock_code)
            avg_price = float(avg_price)
            market_value = current_price * quantity
            unrealized_pnl = (current_price - avg_price) * quantity

            holdings_eval.append(
                {
                    "stockCode": stock_code,
                    "quantity": quantity,
                    "avgPrice": avg_price,
                    "currentPrice": current_price,
                    "marketValue": market_value,
                    "unrealizedPnl": unrealized_pnl,
                }
            )
            total_unrealized_pnl += unrealized_pnl
            total_value += market_value

        return {
            "userId": self.user_id,
            "balance": balance,
            "holdings": holdings_eval,
            "totalUnrealizedPnl": total_unrealized_pnl,
            "totalValue": total_value,
        }

    # ---------- 검증 ----------

    @staticmethod
    def _validate_stock(stock_code: str) -> None:
        if stock_code not in STOCK_CODES:
            raise InvalidStockError(f"{stock_code}는 거래 가능 종목이 아닙니다")
