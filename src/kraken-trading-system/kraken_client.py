from dotenv import load_dotenv
from kraken.spot import SpotClient
import os

# Load environment variables
load_dotenv()
API_KEY  = os.getenv("API_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

class KrakenClient:
    def __init__(self):
        # TO DO: CHECK SpotAsyncClient and async
        self.client = SpotClient(key=API_KEY, secret=PRIVATE_KEY)
    
    def get_balance(self):
        return self.client.request("POST", "/0/private/Balance")

