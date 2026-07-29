from ...kraken_trading_system import config
from ...kraken_trading_system.execution.executor import Executor
from ...kraken_trading_system.paper.paper_engine import PaperEngine
from ...kraken_trading_system.pnl.pnl_tracker import PnLTracker
from ...kraken_trading_system.strategy.market_maker import MMStrategy
from .kraken_client import KrakenClient
from .order_book import OrderBook
from decimal import Decimal
from kraken.spot import SpotWSClient
from logging import Logger
import asyncio

class KrakenWS(SpotWSClient):
    def __init__(self, key: str, secret: str, client: KrakenClient, paper_engine: PaperEngine, market_maker: MMStrategy, executor: Executor, pnl_tracker: PnLTracker, logger: Logger):
        super().__init__(key=key, secret=secret)
        self.currencies = []
        self.currency_info = {}
        self.books = {}
        self.client = client
        self.paper_engine = paper_engine
        self.market_maker = market_maker
        self.executor = executor
        self.pnl_tracker = pnl_tracker
        self.logger = logger


    def configure(self, currencies: list[str], currency_info: dict[str, dict]):
        """Updates KrakenWS to include the currencies being used.
        Initialises the order book for each currency."""
        self.currencies = currencies
        self.currency_info = currency_info
        self.books = {
            c: OrderBook(
                c,
                self.currency_info[c]["pair_decimals"],
                self.currency_info[c]["lot_decimals"],
                self.logger,
                self.client,
                self.paper_engine,
                self.market_maker,
                self.executor,
                self.pnl_tracker
            )
            for c in self.currencies
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


    def get_user_balance(self, pair: str) -> Decimal:
        """Gets user available balance for the given pair."""
        return self.client.get_balance(self.currency_info[pair][0])


    async def _quote_loop(self, pair: str):
        try:
            while True:
                await self.books[pair].refresh_quotes()
                await asyncio.sleep(config.REBALANCE_INTERVAL)
        except asyncio.CancelledError:
            return
