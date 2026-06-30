from dotenv import load_dotenv
import asyncio
import os

from kraken_client import KrakenClient
from websocket_feed import KrakenWS


# Load environment variables
load_dotenv()
API_KEY  = os.getenv("API_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

currencies = ["BTC/USD", "XRP/USD"]


async def main():
    client = KrakenClient(API_KEY, PRIVATE_KEY)
    ws = KrakenWS(key=API_KEY, secret=PRIVATE_KEY)

    await ws.start()

    try:
        currency_info = await client.get_currency_info()
        ws.configure(currencies, currency_info)

        await ws.subscribe(params={
            "channel": "book",
            "symbol": currencies,
            "depth": 10
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