from ...kraken_trading_system import config
from ...kraken_trading_system.execution.executor import Executor
from ...kraken_trading_system.paper.paper_engine import PaperEngine
from ...kraken_trading_system.strategy.market_maker import MMStrategy
from .kraken_client import KrakenClient
from .websocket_feed import KrakenWS
from dotenv import load_dotenv
import asyncio
import os

# Load environment variables
load_dotenv()
API_KEY  = os.getenv("API_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

async def main():
    client = KrakenClient(API_KEY, PRIVATE_KEY)
    paper_engine = PaperEngine()
    market_maker = MMStrategy()
    executor = Executor(client, paper_engine)
    ws = KrakenWS(API_KEY, PRIVATE_KEY, client, paper_engine, market_maker, executor)
    print("Initialised user client and websocket feed.")

    await ws.start()
    print("Started websocket feed.")

    try:
        currency_info = await client.get_currency_info()
        ws.configure(config.SYMBOLS, currency_info)
        print("Configured websocket feed.")

        for pair in config.SYMBOLS:
            asyncio.create_task(ws._quote_loop(pair))

        await ws.subscribe(params={
            "channel": "book",
            "symbol": config.SYMBOLS,
            "depth": config.DEPTH
        })
        print("Subscription completed.")

        while not ws.exception_occur:
            await asyncio.sleep(5)

    
    finally:
        await executor.cancel_all()
        await ws.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass