from kraken.spot import SpotWSClient
from order_book import OrderBook

symbol = "BTC/USD"
book = OrderBook(symbol)

class KrakenWS(SpotWSClient):
    async def on_message(self, message: dict):
        """Receives the websocket messages"""
        if message.get("method") == "pong" or message.get("channel") == "heartbeat":
            return

        try:
            if message.get("channel") == "book" and message.get("type") == "snapshot":
                print(message)
                book.apply_snapshot(message)
        except TypeError:
            return