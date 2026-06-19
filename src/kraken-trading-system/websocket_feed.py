import json
import websocket

class KrakenWS:
    def __init__(self, message_queue):
        self.url = "wss://ws.kraken.com/"
        self.q = message_queue
    
    def on_message(self, ws, message):
        data = json.loads(message)
        self.q.put(data)
    
    def on_open(self, ws):
        ws.send(json.dumps({
            "event": "subscribe",
            "subscription": {"name": "trade"},
            "pair": ["XBT/USD", "XRP/USD"]
        }))
    
    def start(self):
        ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message
        )
        ws.run_forever()
