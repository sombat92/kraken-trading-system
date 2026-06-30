from decimal import Decimal
from sortedcontainers import SortedDict

class OrderBook:
    def __init__(self, symbol: str, depth: int = 10):
        self.asks = SortedDict(lambda k: k)
        self.bids = SortedDict(lambda k: -k)
        self.symbol = symbol
        self.depth = depth
        
    @property
    def best_ask(self):
        return next(iter(self.asks)) if len(self.asks) > 0 else None
    
    @property
    def best_bid(self):
        return next(iter(self.bids)) if len(self.bids) > 0 else None

    @property
    def mid(self):
        """Midpoint between best ask and best bid"""
        if len(self.asks) > 0 and len(self.bids) > 0:
            return (self.best_ask + self.best_bid) / 2
        else:
            return None
    
    @property
    def spread(self):
        """Difference between best ask and best bid"""
        if len(self.asks) > 0 and len(self.bids) > 0:
            return self.best_ask - self.best_bid
        else:
            return None
    
    
    def apply_snapshot(self, snapshot: dict) -> None:
        """Updates bids and asks to reflect new quantities.
        Removes any price levels with a new quantity of 0."""

        # Update asks
        for ask in snapshot["data"][0]["asks"]:
            price, quantity = Decimal(str(ask["price"])), Decimal(str(ask["qty"]))
            if quantity > 0:
                self.asks[price] = quantity
            else:
                self.asks.pop(price, None)

        # Update bids
        for bid in snapshot["data"][0]["bids"]:
            price, quantity = Decimal(str(bid["price"])), Decimal(str(bid["qty"]))
            if quantity > 0:
                self.bids[price] = quantity
            else:
                self.bids.pop(price, None)

        # Output key properties
        print(f"Best bid: {self.best_bid}, Best ask: {self.best_ask}, Mid: {self.mid}, Spread: {self.spread}")