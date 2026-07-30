from ...kraken_trading_system import config
from ...kraken_trading_system.feed.kraken_client import KrakenClient
from ...kraken_trading_system.paper.paper_engine import PaperEngine
from decimal import Decimal
import asyncio


class Executor:
    def __init__(self, client: KrakenClient, paper_engine: PaperEngine):
        self.client = client
        self.paper_engine = paper_engine
        self.active_orders = {}

    async def refresh_quotes(self, pair: str, bid: Decimal, ask: Decimal, size: Decimal):
        """Cancels all existing orders for given pair, then places a fresh bid and ask."""
        await self.cancel_pair_orders(pair)
        await asyncio.sleep(0.1) # Sleep a bit between cancelling and placing orders
        bid_id = await self._place(pair, "buy", bid, size)
        ask_id = await self._place(pair, "sell", ask, size)
        self.active_orders[pair] = {"bid": bid_id, "ask": ask_id}


    async def _place(self, pair: str, side: str, price: Decimal, size: Decimal, retries: int = 3):
        """Places a single order. Uses an exponential backoff retry loop."""
        await asyncio.sleep(0.1) # Wait 0.1 seconds per order to prevent being rate limited by API
        for t in range(1,retries+1):
            try:
                if config.PAPER_MODE:
                    resp = self.paper_engine.place_order(side, size, price, pair)
                    return resp
                else:
                    resp = await self.client.place_order(side, size, price, pair)
                    txids = resp.get("result", {}).get("txid", [])
                    return txids[0] if txids else None
            except Exception as e:
                print(f"Order attempt {t} failed: {e}")
                await asyncio.sleep(2**t) # Exponential backoff
        print("All retries exhausted.")
        return None


    async def cancel_pair_orders(self, pair: str):
        """Cancels all active tracked orders for the given pair."""
        ids = self.active_orders.pop(pair, {})
        for order_id in ids.values():
            if config.PAPER_MODE:
                self.paper_engine.cancel_order(order_id)
            else:
                await self.client.cancel_order(order_id)


    async def cancel_all(self):
        """Cancels all active tracked orders for all pairs."""
        for pair in list(self.active_orders):
            await self.cancel_pair_orders(pair)