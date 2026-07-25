from kraken.spot import SpotAsyncClient

class KrakenClient:
    def __init__(self, key: str, secret: str):
        # TO DO: CHECK SpotAsyncClient and async
        self._key = key
        self._secret = secret
    
    async def get_balance(self):
        async with SpotAsyncClient(key=self._key, secret=self._secret) as client:
            return await client.request("POST", "/0/private/Balance")

    async def get_currency_info(self) -> dict:
        """Gets currency information for BTC/USD and XRP/USD,
        e.g. decimal places for quantity/price."""
        async with SpotAsyncClient(key=self._key, secret=self._secret) as client:
            asset_pairs = dict(await client.request("GET", "/0/public/AssetPairs"))
            currencies = {
                "BTC/USD": asset_pairs["XXBTZUSD"],
                "XRP/USD": asset_pairs["XXRPZUSD"]
            }
            return currencies
    
    async def place_order(self, action: str, volume: float, price: float, pair: str, validate: bool = True):
        """Places order.
        :param str action: either 'buy' or 'sell'.
        """
        params = {
            "ordertype": "limit",
            "type": action,
            "volume": volume,
            "pair": pair, # The symbol, e.g. BTC/USD
            "price": price,
            "validate": validate
        }
        async with SpotAsyncClient(key=self._key, secret=self._secret) as client:
            return await client.request("POST", "/0/private/AddOrder", params=params)
    
    async def cancel_order(self, txid: str):
        """Cancels an open order with a given txid."""
        params = {"txid": txid}
        async with SpotAsyncClient(key=self._key, secret=self._secret) as client:
            return await client.request("POST", "/0/private/CancelOrder", params=params)
    
    async def cancel_all_orders(self):
        """Cancels all orders."""
        async with SpotAsyncClient(key=self._key, secret=self._secret) as client:
            return await client.request("POST", "/0/private/CancelAll")