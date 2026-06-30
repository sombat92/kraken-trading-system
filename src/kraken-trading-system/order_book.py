from decimal import Decimal
from itertools import islice
from sortedcontainers import SortedDict
import zlib

class OrderBook:
    def __init__(self, symbol: str, price_decimals: int, qty_decimals: int, depth: int = 10, checksum_check: int = 10):
        self.asks = SortedDict(lambda k: k)
        self.bids = SortedDict(lambda k: -k)
        self.symbol = symbol
        self.price_decimals = price_decimals
        self.qty_decimals = qty_decimals
        self.depth = depth
        self.checksum_check = checksum_check # Check checksum validity every X updates
        self.update_no = 0
        self._is_ready = False # Whether first snapshot has been applied yet
        
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
    

    def _truncate(self) -> None:
        """Removes excess levels beyond the subscribed depth."""
        for key in list(self.asks.keys())[self.depth:]:
            del self.asks[key]
        
        for key in list(self.bids.keys())[self.depth:]:
            del self.bids[key]
    

    def compute_checksum(self) -> int:
        """Computes checksum string from the top 10 bid and asks levels."""
        parts = []
        for ask, qty in islice(self.asks.items(), 10):
            parts.append(f"{ask:.{self.price_decimals}f}".replace(".", "").lstrip("0")
                         + f"{qty:.{self.qty_decimals}f}".replace(".", "").lstrip("0"))
            
        for bid, qty in islice(self.bids.items(), 10):
            parts.append(f"{bid:.{self.price_decimals}f}".replace(".", "").lstrip("0") 
                         + f"{qty:.{self.qty_decimals}f}".replace(".", "").lstrip("0"))
        
        checksum = "".join(parts)
        return zlib.crc32(checksum.encode("utf-8")) & 0xffffffff
    
    
    def apply_snapshot(self, snapshot: dict) -> None:
        """Clears bids and asks. Sets initial bids and ask from a given snapshot."""

        # Clear bids and asks
        self.asks.clear()
        self.bids.clear()

        # Set asks
        for ask in snapshot["data"][0]["asks"]:
            price, quantity = Decimal(str(ask["price"])), Decimal(str(ask["qty"]))
            self.asks[price] = quantity

        # Set bids
        for bid in snapshot["data"][0]["bids"]:
            price, quantity = Decimal(str(bid["price"])), Decimal(str(bid["qty"]))
            self.bids[price] = quantity
        
        self._truncate()
        self._is_ready = True
  
        # Output key properties
        print(f"SNAPSHOT ({self.symbol}): Best bid: {self.best_bid}, Best ask: {self.best_ask}, Mid: {self.mid}, Spread: {self.spread}")
    

    def apply_update(self, update: dict) -> None:
        """Updates bids and asks to reflect new quantities.
        Removes any price levels with a new quantity of 0.
        Then truncates the bids/asks."""

        if self._is_ready:
            # Update asks
            for ask in update["data"][0]["asks"]:
                price, quantity = Decimal(str(ask["price"])), Decimal(str(ask["qty"]))
                if quantity > 0:
                    self.asks[price] = quantity
                else:
                    self.asks.pop(price, None)

            # Update bids
            for bid in update["data"][0]["bids"]:
                price, quantity = Decimal(str(bid["price"])), Decimal(str(bid["qty"]))
                if quantity > 0:
                    self.bids[price] = quantity
                else:
                    self.bids.pop(price, None)
            
            self._truncate() # Truncates bids and asks

            # Output key properties
            print(f"UPDATE ({self.symbol}): Best bid: {self.best_bid}, Best ask: {self.best_ask}, Mid: {self.mid}, Spread: {self.spread}")

            # If checksum does not match expected checksum, log warning and reinitialise
            if self.update_no % self.checksum_check == 0:
                actual_checksum = update["data"][0]["checksum"]
                computed_checksum = self.compute_checksum()
                if actual_checksum != computed_checksum:
                    self._is_ready = False
                    print(f"WARNING: Computed checksum ({computed_checksum}) does not equal actual checksum ({actual_checksum}).")
                self.update_no = 1
            else:
                self.update_no += 1