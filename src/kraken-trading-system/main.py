from dotenv import load_dotenv
import asyncio
import os

from websocket_feed import KrakenWS
from kraken_client import KrakenClient


# Load environment variables
load_dotenv()
API_KEY  = os.getenv("API_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")


async def main():
    client = KrakenClient(API_KEY, PRIVATE_KEY)
    ws = KrakenWS(key=API_KEY, secret=PRIVATE_KEY)

    await ws.start()

    try:
        await ws.subscribe(params={
            "channel": "book",
            "symbol": ["BTC/USD"],
            "depth": 10
        })

        await ws.subscribe(params={
            "channel": "trade",
            "symbol": ["BTC/USD"]
        })

        while not ws.exception_occur:
            await asyncio.sleep(5)
    finally:
        await ws.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass