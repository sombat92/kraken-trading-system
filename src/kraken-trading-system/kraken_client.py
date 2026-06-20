from kraken.spot import SpotAsyncClient

class KrakenClient:
    def __init__(self, key, secret):
        # TO DO: CHECK SpotAsyncClient and async
        self._key = key
        self._secret = secret
    
    async def get_balance(self):
        async with SpotAsyncClient(key=self._key, secret=self._secret) as client:
            return await client.request("POST", "/0/private/Balance")

