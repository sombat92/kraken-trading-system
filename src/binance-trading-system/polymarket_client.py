import os

from dotenv import load_dotenv
from py_clob_client.client import ClobClient

load_dotenv()

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOST = "https://clob.polymarket.com"
CHAIN_ID = 137

# Initialise client
client = ClobClient(
    host=HOST,
    key=PRIVATE_KEY,
    chain_id=CHAIN_ID,
    signature_type=1 # 1 for email/Magic eallet, 0 for raw EDA/metamask
    funder=FUNDER_ADDRESS
)

# Create API credentials
api_creds = client.create_or_derive_api_creds()
client.set_api_creds(api_creds)

