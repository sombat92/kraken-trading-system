from ...kraken_trading_system import config
from ...kraken_trading_system.feed.order_book import OrderBook
from decimal import Decimal
from typing import Any
import uuid

class PaperEngine:
    def __init__(self, starting_balance_usd: float = 10000):
        self.balance_usd = Decimal(str(starting_balance_usd))
        self.total_fee = Decimal(0) # Total fees accumulated
        self.positions = {}
        self.open_orders = {}


    def _execute(self, order: dict):
        """Executes a given buy/sell order."""
        cost = order["price"] * order["volume"]
        self.total_fee += config.MAKER_FEE * cost # Increases the total fee by the maker fee charged in this order
        if order["side"] == "buy":
            # Completes buy order
            self.balance_usd -= cost
            self.positions[order["pair"]] = self.positions.get(order["pair"], Decimal(0)) + (1 - config.MAKER_FEE) * order["volume"] # Adjusts balance available in that currency
        else:
            # Completes sell order
            self.balance_usd += cost
            self.positions[order["pair"]] = self.positions.get(order["pair"], Decimal(0)) - (1 - config.MAKER_FEE) * order["volume"]

    
    def place_order(self, action: str, volume: Decimal, price: Decimal, pair: str) -> str:
        """Places an order on the paper engine."""
        order_id = str(uuid.uuid4())[:8] # 8-character UUID
        self.open_orders[order_id] = {
            "pair": pair, "action": action, "price": price, "volume": volume
        }
        return order_id


    def cancel_order(self, order_id: str):
        """Cancels an order with a given order ID on the paper engine."""
        self.open_orders.pop(order_id, None)
    

    def check_fills(self, book: OrderBook) -> dict[str, dict[str, Any]]:
        """Checks if any resting orders get crossed. If so, execute the order. Called on every book update."""
        filled = {}
        for order_id, order in self.open_orders.items():
            # If there is a willing buyer/seller, execute the order
            if (order["action"] == "buy" and book.best_ask <= order["price"]) or (order["action"] == "sell" and book.best_bid >= order["price"]):
                self._execute(order)
                filled[order_id] = order

        # Clears filled orders from open orders dict
        for order_id in filled:
            self.open_orders.pop(order_id)       

        return filled