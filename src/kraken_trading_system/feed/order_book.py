from ...kraken_trading_system import config
from decimal import Decimal
from itertools import islice
from logging import Logger
from sortedcontainers import SortedDict
import zlib


class OrderBook:
    def __init__(self, symbol: str, price_decimals: int, qty_decimals: int, logger: Logger, client, paper_engine, market_maker, executor, risk_manager, pnl_tracker, depth: int = 10, checksum_check: int = 10):
        self.asks = SortedDict(lambda k: k)
        self.bids = SortedDict(lambda k: -k)
        self.symbol = symbol
        self.price_decimals = price_decimals
        self.qty_decimals = qty_decimals
        self.logger = logger
        self.client = client
        self.paper_engine = paper_engine
        self.market_maker = market_maker
        self.executor = executor
        self.pnl_tracker = pnl_tracker
        self.risk_manager = risk_manager
        self.depth = depth
        self.checksum_check = checksum_check # Check checksum validity every X updates
        self.update_no = 0
        self._is_ready = False # Whether first snapshot has been applied yet
        self.risk_manager.set_starting_capital(self.user_balance)

        
    @property
    def best_ask(self) -> Decimal | None:
        return next(iter(self.asks)) if len(self.asks) > 0 else None
    
    @property
    def best_bid(self) -> Decimal | None:
        return next(iter(self.bids)) if len(self.bids) > 0 else None

    @property
    def mid(self) -> Decimal | None:
        """Midpoint between best ask and best bid"""
        if len(self.asks) > 0 and len(self.bids) > 0:
            return (self.best_ask + self.best_bid) / 2
        else:
            return None
    
    @property
    def spread(self) -> Decimal | None:
        """Difference between best ask and best bid"""
        if len(self.asks) > 0 and len(self.bids) > 0:
            return self.best_ask - self.best_bid
        else:
            return None

    @property
    # NOTE: Calling this from async self.refresh_quotes() will block event loop if paper mode is off
    def user_balance(self) -> Decimal:
        if config.PAPER_MODE:
            return self.paper_engine.balance_usd
        else:
            return self.client.get_balance(config.SYMBOLS_API[self.symbol])
    

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
            fills = self.paper_engine.check_fills(self) # Gets filled orders on paper engine to be exxecuted
            self.pnl_tracker.write_fills(fills) # Writes filled orders to PnL tracker

            # Update risk manager's position based on each order
            for order in fills.values():
                self.risk_manager.update_position(order["action"], order["volume"], order["price"], self.symbol)

            # If checksum does not match expected checksum, log warning and reinitialise
            if self.update_no % self.checksum_check == 0:
                actual_checksum = update["data"][0]["checksum"]
                computed_checksum = self.compute_checksum()
                if actual_checksum != computed_checksum:
                    self._is_ready = False
                    self.logger.warning(f"Computed checksum ({computed_checksum}) does not equal actual checksum ({actual_checksum}).")
                self.update_no = 0
            else:
                self.update_no += 1

    
    async def refresh_quotes(self):
        """Computes the quotes from the strategy market maker, and passes them to the order executor.
        Then checks whether the daily loss has been executed, and if so trading is halted."""
        if not self._is_ready or self.mid is None:
            return
        
        try:
            bid, ask = self.market_maker.compute_quotes(self, self.risk_manager.get_position(self.symbol))

            # Calculates volume of order, rounded to the pair's qty decimals
            volume = (config.ORDER_SIZE_USD / self.mid).quantize(Decimal(1).scaleb(-self.qty_decimals))

            # If max position in the risk manager would be breached, do not refresh quotes
            if not self.risk_manager.can_quote("buy", volume*bid, self.symbol) or not self.risk_manager.can_quote("ask", volume*ask, self.symbol):
                return

            await self.executor.refresh_quotes(self.symbol, bid, ask, volume)
            self.risk_manager.check_daily_loss(self.user_balance)
        except Exception:
            import traceback
            traceback.print_exc()
