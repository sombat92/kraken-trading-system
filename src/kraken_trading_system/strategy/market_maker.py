from ..feed.order_book import OrderBook
from ...kraken_trading_system import config
from decimal import Decimal

class MMStrategy:
    """Returns a (bid price, ask price) tuple."""
    def compute_quotes(self, book: OrderBook, position: Decimal, skew_factor: Decimal = Decimal("0.0005")) -> tuple[Decimal, Decimal]:
        resv_price = book.mid - position * skew_factor
        edge = book.mid * config.EDGE
        bid_price = resv_price - edge
        ask_price = resv_price + edge

        # Use symmetric widening to widen the quotes so that spread >= min spread
        if ask_price - bid_price < book.mid * config.MIN_SPREAD:
            half = ((book.mid * config.MIN_SPREAD) - (ask_price - bid_price)) / 2
            ask_price += half
            bid_price -= half

        return (bid_price, ask_price)