from ...kraken_trading_system import config
from decimal import Decimal

class RiskManager:
    def __init__(self):
        self.max_position = Decimal(str(config.MAX_POSITION_USD))
        self.daily_loss_limit = Decimal(str(config.DAILY_LOSS_LIMIT))
        self.starting_capital = None
        self.positions = {}
        self.halted = False

    def set_starting_capital(self, capital: Decimal):
        """Sets starting capital."""
        self.starting_capital = capital
        self.floor = capital * Decimal(str(1 - self.daily_loss_limit)) # Lowest capital before halting

    def check_daily_loss(self, current_capital: Decimal) -> bool:
        """Returns whether trading should halt, based on remaining capital."""
        if current_capital < self.floor:
            print(f"CRITICAL: Daily loss limit hit. Capital: {current_capital}")
            self.halted = True
        return self.halted

    def update_position(self, action: str, volume: Decimal, price: Decimal, pair: str):
        """Updates position based on given order."""
        cost = volume * price
        if action == "buy":
            self.positions[pair] = self.positions.get(pair, Decimal(0)) + cost
        else:
            self.positions[pair] = self.positions.get(pair, Decimal(0)) - cost

    def get_position(self, pair: str) -> Decimal:
        """Returns position for a given pair."""
        return self.positions.get(pair, Decimal(0))

    def can_quote(self, action: str, volume_usd: Decimal, pair: str) -> bool:
        """Returns whether a given order would cause max position to be breached by a given pair."""
        if self.halted:
            return False
        
        position = self.get_position(pair)
        if action == "buy":
            projected = position + volume_usd
        else:
            projected = position - volume_usd

        if abs(projected) > self.max_position:
            print(f"Position limit would be breached with the {action} action for {pair}: ${projected}")
            return False
        else:
            return True