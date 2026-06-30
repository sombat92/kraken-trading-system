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