from ...kraken_trading_system import config
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
import csv
import os


class PnLTracker:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.fieldnames = ["timestamp", "symbol", "side", "price", "volume", "fee", "cumulative_pnl"]
        self.total_pnl = 0
        open(self.filepath, "w+").close() # Create .csv file if it doesn't exist already, and clear contents


    def write_fills(self, new_fills: dict[str, dict[str, Any]]):
        """Writes each filled order to the CSV file."""
        with open(self.filepath, "a+", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)

            # Write header if the CSV file is empty
            if os.path.getsize(self.filepath) == 0:
                writer.writeheader()

            for order in new_fills.values():
                fee = config.MAKER_FEE * order["price"] * order["volume"]
                if order["action"] == "buy":
                    self.total_pnl -= order["price"] * order["volume"]
                else:
                    self.total_pnl += order["price"] * order["volume"]
                self.total_pnl -= fee # Charge the fee
                
                writer.writerow({
                    "timestamp": datetime.now(timezone.utc),
                    "symbol": order["pair"],
                    "side": order["action"],
                    "price": order["price"],
                    "volume": order["volume"],
                    "fee": fee,
                    "cumulative_pnl": self.total_pnl
                })


    def summarise(self):
        """Logs the total fills, total fees paid, gross PnL and net PnL."""
        # Calculates statistics
        with open(self.filepath, "r+") as file:
            reader = csv.DictReader(file)
            total_fills = 0
            total_fees = Decimal(0)

            for row in reader:
                total_fills += 1
                total_fees += Decimal(row["fee"])

        gross_pnl = self.total_pnl + total_fees

        # Print statistics to console
        print(f"{datetime.now(timezone.utc)} Total fills: {total_fills}, Total fees paid: ${total_fees}, Gross PnL: ${gross_pnl}, Net PnL: ${self.total_pnl}")
