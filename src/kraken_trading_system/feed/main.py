from dotenv import load_dotenv
import asyncio
import os

from .kraken_client import KrakenClient
from .websocket_feed import KrakenWS
from ...kraken_trading_system import config
from ...kraken_trading_system.execution.executor import Executor



# Load environment variables
load_dotenv()
API_KEY  = os.getenv("API_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

async def main():
    client = KrakenClient(API_KEY, PRIVATE_KEY)
    ws = KrakenWS(key=API_KEY, secret=PRIVATE_KEY)

    await ws.start()

    try:
        currency_info = await client.get_currency_info()
        ws.configure(config.SYMBOLS, currency_info)

        executor = Executor(client)

        #print(await client.place_order("buy", 2, 109.2, "BTC/USD"))
        #print(await executor.place("BTC/USD", "buy", 1.2, 2.3))
        await executor.refresh_quotes("XBTUSD", 1.5, 1.6, 2)

        await ws.subscribe(params={
            "channel": "book",
            "symbol": config.SYMBOLS,
            "depth": config.DEPTH
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