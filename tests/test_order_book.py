from decimal import Decimal
from src.kraken_trading_system.feed.order_book import OrderBook
from unittest.mock import MagicMock
import pytest

example_snapshots = [
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63219.0, 'qty': 0.5},
                        {'price': 63218.5, 'qty': 0.32},
                        {'price': 63218.0, 'qty': 1.1},
                        {'price': 63217.5, 'qty': 0.05},
                        {'price': 63217.0, 'qty': 0.74},
                        {'price': 63216.5, 'qty': 0.2},
                        {'price': 63216.0, 'qty': 0.15},
                        {'price': 63215.5, 'qty': 0.6},
                        {'price': 63215.0, 'qty': 0.9},
                        {'price': 63214.5, 'qty': 0.25}],
               'asks': [{'price': 63220.0, 'qty': 0.4},
                        {'price': 63220.5, 'qty': 0.12},
                        {'price': 63221.0, 'qty': 0.33},
                        {'price': 63221.5, 'qty': 0.55},
                        {'price': 63222.0, 'qty': 0.08},
                        {'price': 63222.5, 'qty': 0.7},
                        {'price': 63223.0, 'qty': 0.19},
                        {'price': 63223.5, 'qty': 0.44},
                        {'price': 63224.0, 'qty': 0.61},
                        {'price': 63224.5, 'qty': 0.27}],
               'checksum': 3423697554,
               'timestamp': '2026-07-28T01:06:25.888939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63219.2, 'qty': 0.10779193}],
               'asks': [{'price': 63219.8, 'qty': 0.00039544}],
               'checksum': 3263455635,
               'timestamp': '2026-07-28T01:06:26.238939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63216.0, 'qty': 0.0}],
               'asks': [],
               'checksum': 2118643252,
               'timestamp': '2026-07-28T01:06:26.588939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [],
               'asks': [{'price': 63221.0, 'qty': 0.31}],
               'checksum': 1479941903,
               'timestamp': '2026-07-28T01:06:26.938939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63219.4, 'qty': 0.055}],
               'asks': [],
               'checksum': 106179958,
               'timestamp': '2026-07-28T01:06:27.288939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [],
               'asks': [{'price': 63219.8, 'qty': 0.0}],
               'checksum': 1267678015,
               'timestamp': '2026-07-28T01:06:27.638939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63214.5, 'qty': 0.44}],
               'asks': [{'price': 63224.5, 'qty': 0.09}],
               'checksum': 1278928677,
               'timestamp': '2026-07-28T01:06:27.988939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63215.0, 'qty': 0.0}],
               'asks': [{'price': 63220.5, 'qty': 0.05}],
               'checksum': 484291950,
               'timestamp': '2026-07-28T01:06:28.338939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63219.5, 'qty': 0.7531}],
               'asks': [],
               'checksum': 1795118388,
               'timestamp': '2026-07-28T01:06:28.688939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [],
               'asks': [{'price': 63221.5, 'qty': 0.0}, {'price': 63219.9, 'qty': 0.125}],
               'checksum': 180302469,
               'timestamp': '2026-07-28T01:06:29.038939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63219.5, 'qty': 0.65}],
               'asks': [],
               'checksum': 2313483606,
               'timestamp': '2026-07-28T01:06:29.388939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [],
               'asks': [{'price': 63219.7, 'qty': 0.022}],
               'checksum': 643070858,
               'timestamp': '2026-07-28T01:06:29.738939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63214.5, 'qty': 0.0}, {'price': 63217.8, 'qty': 0.31}],
               'asks': [],
               'checksum': 3270977771,
               'timestamp': '2026-07-28T01:06:30.088939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [],
               'asks': [{'price': 63223.5, 'qty': 0.0}, {'price': 63220.2, 'qty': 0.06}],
               'checksum': 1617189050,
               'timestamp': '2026-07-28T01:06:30.438939Z'}]},
    {'channel': 'book',
     'type': 'update',
     'data': [{'symbol': 'BTC/USD',
               'bids': [{'price': 63219.6, 'qty': 0.11}],
               'asks': [{'price': 63219.7, 'qty': 0.033}],
               'checksum': 415111859,
               'timestamp': '2026-07-28T01:06:30.788939Z'}]},
]


def make_book(snapshot: dict) -> OrderBook:
    pair = snapshot["data"][0]["symbol"]
    book = OrderBook(pair, 1, 8, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    return book


@pytest.mark.parametrize("snapshot", [example_snapshots[0]])
def test_best_bid(snapshot: dict):
    """Tests best bid."""
    book = make_book(snapshot)
    book.apply_snapshot(snapshot)
    assert book.best_bid == Decimal("63219")


@pytest.mark.parametrize("snapshot", [example_snapshots[0]])
def test_best_ask(snapshot: dict):
    """Tests best ask."""
    book = make_book(snapshot)
    book.apply_snapshot(snapshot)
    assert book.best_ask == Decimal("63220")


@pytest.mark.parametrize("snapshot", [example_snapshots[0]])
def test_spread(snapshot: dict):
    """Tests spread."""
    book = make_book(snapshot)
    book.apply_snapshot(snapshot)
    assert book.spread == Decimal("1")


@pytest.mark.parametrize("snapshot", [example_snapshots[0]])
def test_mid(snapshot: dict):
    """Tests mid."""
    book = make_book(snapshot)
    book.apply_snapshot(snapshot)
    assert book.mid == Decimal("63219.5")


@pytest.mark.parametrize("snapshots", [example_snapshots])
def test_compute_checksum(snapshots: list[dict]):
    """Tests checksum generation method."""
    book = OrderBook("BTC/USD", 1, 8, MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    book.apply_snapshot(snapshots[0])
    for i in range(1, len(snapshots)):
        book.apply_update(snapshots[i])

    assert book.compute_checksum() == 415111859