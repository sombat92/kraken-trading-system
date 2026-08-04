from ...kraken_trading_system import config
from ...kraken_trading_system.feed.order_book import OrderBook
from decimal import Decimal
from logging import Logger
from typing import Any
import uuid

class PaperEngine:
    def __init__(self, logger: Logger, starting_balance_usd: float = 10000):
        self.balance_usd = Decimal(str(starting_balance_usd))
        self.total_fee = Decimal(0) # Total fees accumulated
        self.positions = { # Seed the positions with initial inventory
            "BTC/USD": Decimal("0.05"),
            "XRP/USD": Decimal("500")
        }
        self.open_orders = {}
        self.logger = logger


    def _execute(self, order: dict) -> bool:
        """Executes a given buy/sell order. Returns whether the fill was executed."""
        cost = order["price"] * order["volume"]
        fee = config.MAKER_FEE * cost # Fee charged in this order
        if order["action"] == "buy":
            # Completes buy order if cost does not exceed balance
            if cost + fee > self.balance_usd:
                self.logger.info(f"Fill skipped: insufficient balance ({self.balance_usd}) for total cost ({cost+fee})")
                return False
            self.balance_usd -= cost + fee
            self.positions[order["pair"]] = self.positions.get(order["pair"], Decimal(0)) + order["volume"] # Adjusts balance available in that currency
        else:
            # Completes sell order if quantity does not exceed currency held
            held = self.positions.get(order["pair"], Decimal(0)) 
            if order["volume"] > held:
                self.logger.info((f"Fill skipped: insufficient {order['pair']} balance ({held}) for order volume {order['volume']}"))
                return False
            self.balance_usd += cost - fee
            self.positions[order["pair"]] = self.positions.get(order["pair"], Decimal(0)) - order["volume"]

        self.total_fee += fee
        return True

    
    def place_order(self, action: str, volume: Decimal, price: Decimal, pair: str) -> str | None:
        """Places an order on the paper engine."""
        # Checks if order can be placed
        cost = price * volume
        if action == "buy":
            if cost > self.balance_usd:
                self.logger.info(f"Rejected buy {pair}: cost {cost} exceeds balance {self.balance_usd}")
                return None
        else:
            held = self.positions.get(pair, Decimal(0))
            if volume > held:
                self.logger.info(f"Rejected sell {pair}: volume {volume} exceeds held {held}")
                return None

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
        for order_id, order in list(self.open_orders.items()):
            # Only use orders using the same pair
            if order["pair"] != book.symbol:
                continue

            # If there is a willing buyer/seller, execute the order
            if (order["action"] == "buy" and book.best_ask <= order["price"]) or (order["action"] == "sell" and book.best_bid >= order["price"]):
                if self._execute(order):
                    filled[order_id] = order
                    print(f"Order {order_id} executed: {order}")

        # Clears filled orders from open orders dict
        for order_id in filled:
            self.open_orders.pop(order_id)       

        return filled
