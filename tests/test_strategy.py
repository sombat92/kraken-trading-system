from decimal import Decimal
from src.kraken_trading_system.feed.order_book import OrderBook
from src.kraken_trading_system.strategy.market_maker import MMStrategy
from src.kraken_trading_system.strategy import market_maker
from unittest.mock import MagicMock
import pytest


def make_book(mid: Decimal) -> OrderBook:
    """Builds a lightweight mock OrderBook exposing only the `.mid` property
    that MMStrategy.compute_quotes reads from."""
    book = MagicMock(spec=OrderBook)
    book.mid = mid
    return book


# --- minimum spread ---
# EDGE = 0.0003, MIN_SPREAD = 0.0002 -> under the default config, 2 * EDGE (0.0006)
# is already above MIN_SPREAD (0.0002), so the un-widened spread should naturally
# satisfy the minimum for any mid/position combination.

@pytest.mark.parametrize(
    "mid, position",
    [
        (Decimal("100"), Decimal("0")),
        (Decimal("63219.5"), Decimal("0")),
        (Decimal("63219.5"), Decimal("50")),
        (Decimal("63219.5"), Decimal("-50")),
        (Decimal("1.2345"), Decimal("10")),
    ],
)
def test_compute_quotes_satisfies_minimum_spread(mid, position):
    """Tests that ask - bid is never smaller than MIN_SPREAD fraction of mid."""
    strategy = MMStrategy()
    book = make_book(mid)

    bid, ask = strategy.compute_quotes(book, position)

    min_spread_required = mid * Decimal(str(market_maker.config.MIN_SPREAD))
    assert ask - bid >= min_spread_required
    assert bid < ask


def test_compute_quotes_widens_spread_when_edge_is_too_small(monkeypatch):
    """Tests the widening branch directly: forces 2*EDGE below MIN_SPREAD so that
    compute_quotes must symmetrically widen bid/ask to exactly meet MIN_SPREAD."""
    monkeypatch.setattr(market_maker.config, "EDGE", 0.00001)  # 2*EDGE (0.002%) < MIN_SPREAD (0.02%)

    strategy = MMStrategy()
    mid = Decimal("100")
    book = make_book(mid)

    bid, ask = strategy.compute_quotes(book, Decimal("0"))

    min_spread_required = mid * Decimal(str(market_maker.config.MIN_SPREAD))
    assert ask - bid == min_spread_required
    # Widening is symmetric around the reservation price (mid, since position=0).
    assert mid - bid == ask - mid


# --- skew direction ---

@pytest.mark.parametrize(
    "mid",
    [Decimal("100"), Decimal("63219.5")],
)
def test_compute_quotes_skews_down_when_long(mid):
    """Tests that a positive (long) position shifts both bid and ask below the
    flat (zero-position) quotes, discouraging further buying."""
    strategy = MMStrategy()
    book = make_book(mid)

    flat_bid, flat_ask = strategy.compute_quotes(book, Decimal("0"))
    long_bid, long_ask = strategy.compute_quotes(book, Decimal("50"))

    assert long_bid < flat_bid
    assert long_ask < flat_ask


@pytest.mark.parametrize(
    "mid",
    [Decimal("100"), Decimal("63219.5")],
)
def test_compute_quotes_skews_up_when_short(mid):
    """Tests that a negative (short) position shifts both bid and ask above the
    flat (zero-position) quotes, discouraging further selling."""
    strategy = MMStrategy()
    book = make_book(mid)

    flat_bid, flat_ask = strategy.compute_quotes(book, Decimal("0"))
    short_bid, short_ask = strategy.compute_quotes(book, Decimal("-50"))

    assert short_bid > flat_bid
    assert short_ask > flat_ask


def test_compute_quotes_skew_is_proportional_to_skew_factor():
    """Tests that a larger skew_factor produces a larger displacement from the
    flat reservation price for the same position."""
    strategy = MMStrategy()
    book = make_book(Decimal("100"))
    position = Decimal("20")

    bid_default, ask_default = strategy.compute_quotes(book, position, skew_factor=Decimal("0.75"))
    bid_larger, ask_larger = strategy.compute_quotes(book, position, skew_factor=Decimal("1.5"))

    # A larger skew factor pushes reservation price (and thus both quotes) further down
    # for a long position.
    assert bid_larger < bid_default
    assert ask_larger < ask_default


def test_compute_quotes_exact_values_at_zero_position():
    """Tests exact bid/ask values at zero position against a hand-computed example,
    using the default config (EDGE=0.0003, MIN_SPREAD=0.0002)."""
    strategy = MMStrategy()
    mid = Decimal("100")
    book = make_book(mid)

    bid, ask = strategy.compute_quotes(book, Decimal("0"))

    # resv_price = mid = 100; edge = 100 * 0.0003 = 0.03
    assert bid == Decimal("99.97")
    assert ask == Decimal("100.03")


def test_compute_quotes_exact_values_with_long_position():
    """Tests exact bid/ask values with a nonzero long position against a
    hand-computed example."""
    strategy = MMStrategy()
    mid = Decimal("100")
    book = make_book(mid)

    bid, ask = strategy.compute_quotes(book, Decimal("100"))

    # resv_price = 100 - 100*0.75 = 25; edge = 100 * 0.0003 = 0.03
    assert bid == Decimal("24.97")
    assert ask == Decimal("25.03")
