from ...kraken_trading_system import config
from datetime import datetime
from typing import Any
import csv

class PnLTracker:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.fieldnames = ["timestamp", "symbol", "side", "price", "volume", "fee", "cumulative_pnl"]
        self.total_pnl = 0


    def write_fills(self, new_fills: dict[str, dict[str, Any]]):
        """Writes each filled order to the CSV file."""
        with open(self.filepath, "a+") as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            for order in new_fills.values():
                if order["action"] == "buy":
                    self.total_pnl -= order["price"] * order["volume"]
                else:
                    self.total_pnl += order["price"] * order["volume"]
                
                writer.writerow({
                    "timestamp": datetime.now(),
                    "symbol": order["pair"],
                    "side": order["action"],
                    "price": order["price"],
                    "volume": order["volume"],
                    "fee": config.MAKER_FEE * order["price"] * order["volume"],
                    "cumulative_pnl": self.total_pnl
                })


    def summarise(self):
        """Prints the total fills, total fees paid, gross PnL and net PnL."""
        with open(self.filepath, "r+") as file:
            reader = csv.DictReader(file, fieldnames=self.fieldnames)
            total_fills = 0
            total_fees = 0

            for row in reader:
                total_fills += 1
                total_fees += float(row["fee"])

        gross_pnl = self.total_pnl + total_fees
        print(f"Total fills: {total_fills}\nTotal fees paid:{total_fees}\nGross PnL:{gross_pnl}\nNet PnL: {self.total_pnl}")
