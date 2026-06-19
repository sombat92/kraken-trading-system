import threading
import time
from queue import Queue

from websocket_feed import KrakenWS
from kraken_client import KrakenClient

def strategy_loop(q, client):
    while True:
        msg = q.get()
        print("Received:",msg)

        # Placeholder logic
        # e.g. if signal: client.place_order(...)


def main():
    q = Queue()
    client = KrakenClient()
    ws = KrakenWS(q)

    threading.Thread(target=ws.start, daemon=True).start()
    threading.Thread(target=strategy_loop, args=(q,client), daemon=True).start()

    while True:
        time.sleep(5)

if __name__ == "__main__":
    main()
