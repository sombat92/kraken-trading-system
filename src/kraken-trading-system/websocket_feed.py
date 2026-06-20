from kraken.spot import SpotWSClient

class KrakenWS(SpotWSClient):
    async def on_message(self, message):
        """Receives the websocket messages"""
        if message.get("method") == "pong" or message.get("channel") == "heartbeat":
            return

        try:
            print(message)
        except TypeError:
            return