import os

DAILY_LOSS_LIMIT = 0.03
DEPTH = 10
EDGE = 0.0003 # Fraction of the price used as an edge
MAKER_FEE = 0.0016
MAX_POSITION_USD = 200.0
MIN_SPREAD = 0.0002 # Fraction of mid
ORDER_SIZE_USD = 25.0
PAPER_MODE = True
PNL_CSV_FILEPATH = os.path.join(os.getcwd(), "data", "pnl_report.csv")
REBALANCE_INTERVAL = 30
SYMBOLS = ["BTC/USD", "XRP/USD"]
SYMBOLS_API = {
    "BTC/USD": "XXBTZUSD", 
    "XRP/USD": "XXRZPUSD"
}