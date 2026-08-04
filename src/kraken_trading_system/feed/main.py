from ...kraken_trading_system import config
from ...kraken_trading_system.execution.executor import Executor
from ...kraken_trading_system.paper.paper_engine import PaperEngine
from ...kraken_trading_system.pnl.pnl_tracker import PnLTracker
from ...kraken_trading_system.risk.risk_manager import RiskManager
from ...kraken_trading_system.strategy.market_maker import MMStrategy
from .kraken_client import KrakenClient
from .websocket_feed import KrakenWS
from dotenv import load_dotenv
import asyncio
import logging
import os
import time
import signal

# Load environment variables
load_dotenv()
API_KEY  = os.getenv("API_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")


async def shutdown(executor: Executor, quote_tasks: list[asyncio.Task], ws: KrakenWS):
    """Performs a graceful shutdown.
    Cancels all orders in executor and quote tasks. Finally closes the websocket feed."""
    await executor.cancel_all()
    for task in quote_tasks:
        task.cancel()
    await asyncio.gather(*quote_tasks, return_exceptions=True)
    await ws.close()


async def daily_loss_reset_loop(risk_manager: RiskManager, get_current_capital, interval_seconds: int = 86400):
    """
    Resets the RiskManager's daily loss limit every `interval_seconds` (default: 24h),
    starting from the moment this task is created (i.e. program start).

    :param risk_manager: the running RiskManager instance
    :param get_current_capital: zero-arg callable returning current capital as a Decimal
                                 (e.g. lambda: paper_engine.balance_usd)
    :param interval_seconds: how often to reset the window, in seconds (86400 = 24h)
    """
    try:
        while True:
            await asyncio.sleep(interval_seconds)

            current_capital = get_current_capital()
            risk_manager.set_starting_capital(current_capital)  # re-bases starting_capital + floor off *today's* opening balance
            risk_manager.halted = False  # lift any halt carried over from the previous window

            risk_manager.logger.info(
                f"Daily loss limit window reset. New starting capital: {current_capital}, "
                f"new floor: {risk_manager.floor}"
            )
    except asyncio.CancelledError:
        return


async def main():
    # Check that config's variables are correct
    if config.EDGE <= 0:
        raise ValueError("Edge must be positive.")
    if config.MIN_SPREAD <= 0:
        raise ValueError("Minimum spread must be positive")
    if config.MAX_POSITION_USD <= config.ORDER_SIZE_USD:
        raise ValueError("The maximum position must be greater than the order size.")

    # Configure logging
    file_handler = logging.FileHandler(config.MESSAGES_LOG_FILEPATH, mode="w")
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    formatter.converter = time.gmtime
    file_handler.setFormatter(formatter)
    m_logger = logging.getLogger(__name__)
    m_logger.setLevel(logging.DEBUG)
    m_logger.addHandler(file_handler)

    # Initialise key components
    client = KrakenClient(API_KEY, PRIVATE_KEY)
    market_maker = MMStrategy()
    pnl_tracker = PnLTracker(config.PNL_CSV_FILEPATH)
    paper_engine = PaperEngine(m_logger)
    risk_manager = RiskManager(m_logger)
    executor = Executor(client, paper_engine, m_logger)
    ws = KrakenWS(API_KEY, PRIVATE_KEY, client, paper_engine, market_maker, executor, pnl_tracker, risk_manager, m_logger)
    print("Initialised user client and websocket feed.")

    # Start and configure websocket feed
    await ws.start()
    currency_info = await client.get_currency_info()
    ws.configure(config.SYMBOLS, currency_info)
    print("Configured websocket feed.")
    
    quote_tasks = [asyncio.create_task(ws._quote_loop(pair)) for pair in config.SYMBOLS]
    quote_tasks.append(
        asyncio.create_task(daily_loss_reset_loop(
            risk_manager,
            lambda: paper_engine.balance_usd # NOTE: currently only works for paper mode
        ))
    )

    # Handle graceful shutdown when run as a background service (using SIGTERM). Not on Windows.
    if os.name != "nt":
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(executor, quote_tasks, ws)))

    try:
        await ws.subscribe(params={
            "channel": "book",
            "symbol": config.SYMBOLS,
            "depth": config.DEPTH
        })
        print("Subscription completed.")

        while not ws.exception_occur:
            await asyncio.sleep(5)

        # If there is an websocket exception, restart the connection
        await ws.start()
        m_logger.debug("Websocket connection restarted.")
        
  
    finally:
        await shutdown(executor, quote_tasks, ws)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass