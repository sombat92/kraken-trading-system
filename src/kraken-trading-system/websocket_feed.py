from kraken.spot import SpotWSClient
from order_book import OrderBook

class KrakenWS(SpotWSClient):
    def __init__(self, key, secret):
        super().__init__(key=key, secret=secret)
        self.currencies = []
        self.currency_info = {}
        self.books = {}
    
    def configure(self, currencies, currency_info):
        """Updates KrakenWS to include the currencies being used.
        Initialises the order book for each currency."""
        self.currencies = currencies
        self.currency_info = currency_info
        self.books = {
            c: OrderBook(
                c,
                self.currency_info[c]["pair_decimals"],
                self.currency_info[c]["lot_decimals"]
            ) for c in self.currencies
        }

    async def on_message(self, message: dict):
        """Receives the websocket messages"""
        if message.get("method") == "pong" or message.get("channel") == "heartbeat":
            return

        try:
            if message.get("channel") == "book":
                symbol = message.get("data")[0].get("symbol")
                if message.get("type") == "snapshot":
                    self.books[symbol].apply_snapshot(message)
                elif message.get("type") == "update":
                    self.books[symbol].apply_update(message)

        except TypeError:
            return