from decimal import Decimal
from src.kraken_trading_system.risk.risk_manager import RiskManager
from unittest.mock import MagicMock
import pytest


@pytest.mark.parametrize(
    "existing_position, action, volume_usd",
    [
        (Decimal("150"), "buy", Decimal("60")),    # 150 + 60 = 210 > 200 [MAX_POSITION_USD] (long breach)
        (Decimal("-150"), "sell", Decimal("60")),  # -150 - 60 = -210, |.| > 200 (short breach)
        (Decimal("200"), "buy", Decimal("0.01")),  # just tips over the limit
    ],
)
def test_position_limit_breached(existing_position, action, volume_usd):
    """Tests that can_quote returns False when the projected position exceeds max_position."""
    risk_manager = RiskManager(MagicMock())
    # Seed the existing position directly for a known starting point.
    risk_manager.positions["BTC/USD"] = existing_position

    assert risk_manager.can_quote(action, volume_usd, "BTC/USD") is False


@pytest.mark.parametrize(
    "existing_position, action, volume_usd",
    [
        (Decimal("100"), "buy", Decimal("50")),    # 100 + 50 = 150 <= 200
        (Decimal("-100"), "sell", Decimal("50")),  # -100 - 50 = -150, |.| <= 200
        (Decimal("0"), "buy", Decimal("200")),     # exactly at the limit, not breached
    ],
)
def test_can_quote_returns_true_when_within_position_limit(existing_position, action, volume_usd):
    """Tests that can_quote returns True when the projected position stays within max_position."""
    risk_manager = RiskManager(MagicMock())
    risk_manager.positions["BTC/USD"] = existing_position

    assert risk_manager.can_quote(action, volume_usd, "BTC/USD") is True


def test_can_quote_position_limit_is_per_pair():
    """Tests that a breach on one pair does not affect quoting on another pair."""
    risk_manager = RiskManager(MagicMock())
    risk_manager.positions["BTC/USD"] = Decimal("190")
    risk_manager.positions["XRP/USD"] = Decimal("0")

    assert risk_manager.can_quote("buy", Decimal("50"), "BTC/USD") is False
    assert risk_manager.can_quote("buy", Decimal("50"), "XRP/USD") is True


def test_can_quote_returns_false_when_already_halted_even_within_limit():
    """Tests that a halted RiskManager refuses to quote regardless of position headroom."""
    risk_manager = RiskManager(MagicMock())
    risk_manager.halted = True

    assert risk_manager.can_quote("buy", Decimal("1"), "BTC/USD") is False


# --- check_daily_loss: halt threshold ---
# DAILY_LOSS_LIMIT = 0.03, so floor = starting_capital * 0.97

def test_check_daily_loss_sets_halted_true_below_threshold():
    """Tests that halted becomes True once capital drops below the daily loss floor."""
    risk_manager = RiskManager(MagicMock())
    risk_manager.set_starting_capital(Decimal("10000"))
    assert risk_manager.floor == Decimal("9700.00")

    result = risk_manager.check_daily_loss(Decimal("9699.99"))

    assert result is True
    assert risk_manager.halted is True


def test_check_daily_loss_does_not_halt_exactly_at_threshold():
    """Tests the boundary: capital exactly equal to the floor should not trigger a halt."""
    risk_manager = RiskManager(MagicMock())
    risk_manager.set_starting_capital(Decimal("10000"))

    result = risk_manager.check_daily_loss(Decimal("9700.00"))

    assert result is False
    assert risk_manager.halted is False


def test_check_daily_loss_does_not_halt_above_threshold():
    """Tests that capital comfortably above the floor leaves trading un-halted."""
    risk_manager = RiskManager(MagicMock())
    risk_manager.set_starting_capital(Decimal("10000"))

    result = risk_manager.check_daily_loss(Decimal("9750"))

    assert result is False
    assert risk_manager.halted is False


def test_check_daily_loss_halt_is_sticky():
    """Tests that once halted, a later recovery in capital does not un-halt trading."""
    risk_manager = RiskManager(MagicMock())
    risk_manager.set_starting_capital(Decimal("10000"))

    risk_manager.check_daily_loss(Decimal("9600"))  # breach -> halts
    assert risk_manager.halted is True

    result = risk_manager.check_daily_loss(Decimal("9999"))  # capital recovers, but halted stays True

    assert result is True
    assert risk_manager.halted is True
