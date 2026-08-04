from decimal import Decimal
import os

DAILY_LOSS_LIMIT = Decimal(str(0.03))
DEPTH = 10
EDGE = Decimal(str(0.0001)) # Fraction of the price used as an edge 
MAKER_FEE = Decimal(str(0.0016))
MAX_POSITION_USD = Decimal(500)
MESSAGES_LOG_FILEPATH = os.path.join(os.getcwd(), "logs", "messages.log")
MIN_SPREAD = Decimal(str(0.0002)) # Fraction of mid
ORDER_SIZE_USD = Decimal(25)
PAPER_MODE = True
PNL_CSV_FILEPATH = os.path.join(os.getcwd(), "logs", "pnl_report.csv")
REBALANCE_INTERVAL = 30
SYMBOLS = ["BTC/USD", "XRP/USD"]
SYMBOLS_API = {
    "BTC/USD": "XXBTZUSD", 
    "XRP/USD": "XXRPZUSD"
}