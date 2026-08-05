# Kraken Spot Market Making Bot

An asynchronous Python market making bot for the **Kraken Spot Exchange**, implementing the complete pipeline from live market data to paper-traded execution and PnL tracking.

The project was built as a learning exercise in low-latency trading systems, exchange APIs, market microstructure, and quantitative trading architecture. Rather than focusing on profitability alone, the goal was to build a modular trading system that resembles the structure of production algorithmic trading software.



## Features

- Fully asynchronous architecture using `asyncio`
- Kraken Spot WebSocket v2 integration
- Level-2 order book reconstruction
- CRC32 checksum verification
- Decimal-precision arithmetic throughout
- Inventory-skewed market making strategy
- Automatic quote refresh
- Paper trading engine
- Risk management module
- PnL tracking with fee accounting
- Unit tested core components

# Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd kraken-trading-system
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

### 3. Install the project

Install the package in editable mode:

```bash
pip install -e .
```

This installs the project along with its dependencies while allowing source code changes to take effect immediately.

### 4. Create a `.env` file

Create a `.env` file in the project root containing your Kraken API credentials.

```text
KRAKEN_API_KEY=your_api_key
KRAKEN_API_SECRET=your_api_secret
```

These credentials are only required for live trading. Paper mode does not submit orders to Kraken, but the application may still use authenticated REST endpoints depending on configuration.

### 5. Run the bot

```bash
python main.py
```

The application will:

- connect to Kraken WebSocket v2
- reconstruct live order books
- begin quote generation
- execute either paper or live orders depending on configuration
- log fills and PnL

---

# Paper Trading vs Live Trading

The trading mode is controlled by a single configuration option in `config.py`.

To use paper trading:

```python
PAPER_MODE = True
```

To submit real orders to Kraken:

```python
PAPER_MODE = False
```

> **Warning**
>
> Setting `PAPER_MODE = False` enables live trading using your Kraken account. Ensure your API keys, position limits, order sizes, and risk parameters are configured correctly before running the bot.


---

# System Architecture

```text
                 Kraken WebSocket v2
                         │
                         ▼
              Order Book Reconstruction
         (L2 Book + CRC32 Validation)
                         │
                         ▼
              Market Making Strategy
         (Inventory Skew / Avellaneda-Stoikov)
                         │
                         ▼
                 Execution Engine
         (Limit Orders / Cancel & Replace)
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
  Paper Trading Engine            Kraken REST API
         │
         ▼
     PnL Tracker
```

The system is designed as a collection of independent modules with clear responsibilities, making individual components easy to test and extend.

---

# Repository Structure

```text
src/
└── kraken_trading_system/
    ├── config.py
    ├── feed/
    ├── strategy/
    ├── execution/
    ├── paper/
    ├── pnl/
    └── risk/

tests/
├── test_order_book.py
├── test_risk_manager.py
└── test_strategy.py

main.py
```

---

## WebSocket Feed

The trading system receives market data using Kraken's **WebSocket v2 API** through the `python-kraken-sdk`.

Features include:

- asynchronous networking
- simultaneous subscriptions
- automatic reconnect support
- depth-10 order book subscriptions
- routing updates by trading pair

Current trading pairs:

- BTC/USD
- XRP/USD

---

## Order Book

The order book performs full Level-2 reconstruction from Kraken snapshots and incremental updates.

### Implementation

The book stores

- bids inside a descending `SortedDict`
- asks inside an ascending `SortedDict`

using `Decimal` values to eliminate floating-point rounding issues.

Snapshots clear existing state, rebuild both sides and mark the book as ready.

Incremental updates modify price levels, remove zero-volume levels, maintain fixed depth and preserve sorted ordering.

The book exposes best bid, best ask, spread and midpoint through computed properties.

---

## CRC32 Validation

Kraken publishes a checksum with order book updates.

The implementation reconstructs Kraken's checksum string using the exchange's published decimal precision before calculating `zlib.crc32(...)`.

Checksums are verified every tenth update. If validation fails, the book is marked unavailable until a fresh snapshot is received.

---

## Strategy

The market maker implements a simplified Avellaneda-Stoikov inventory-based quoting model.

```python
reservation_price = mid - inventory_skew
inventory_skew = position * skew_factor

bid = reservation_price - edge
ask = reservation_price + edge
```

Long inventory shifts quotes downward while short inventory shifts quotes upward. A configurable minimum spread is always enforced.

---

## Execution Engine

Responsible for:

- placing limit orders
- cancelling stale orders
- refreshing quotes
- retrying failed submissions
- routing between live and paper execution

---

## Paper Trading Engine

Simulates fills without sending live orders.

Buy fills occur when:

```text
best ask ≤ bid price
```

Sell fills occur when:

```text
best bid ≥ ask price
```

Maintains balances, inventory, orders and fees.

---

## Risk Management

Current protections include:

- maximum position size
- daily loss circuit breaker (refreshed every 24h)
- per-instrument limits
- sticky trading halt

---

## PnL Tracking

Each fill records:

- timestamp
- symbol
- side
- execution price
- volume
- fees
- cumulative net PnL

---

# Configuration

Most parameters are centralised in `config.py`.

---

# Testing

30 unit tests cover:

- Order Book
- Strategy
- Risk Manager

All tests currently pass.

---

# Running

```bash
pip install -e .
python main.py
```

---

# Technologies

- Python
- asyncio
- python-kraken-sdk
- Kraken WebSocket API v2
- Kraken REST API
- sortedcontainers
- Decimal
- pytest

---

# Current Limitations

- optimistic paper fills
- no queue modelling
- no latency simulation
- no partial fills
- no slippage model
- no database
- no dashboard

---

# Economic Considerations

At standard Kraken maker fees, the current edge is insufficient to overcome transaction costs. The strategy is therefore expected to be unprofitable at default fee tiers and serves primarily as an educational implementation.

---

# Future Improvements

- Partial fills
- Queue estimation
- Dynamic volatility
- Adaptive spreads
- Multi-exchange support
- Historical backtesting
- Performance analytics
- Docker deployment

---

# Educational Objectives

This project was built to gain practical experience with asynchronous systems, exchange APIs, market microstructure, quantitative trading, execution algorithms, risk management, testing and modular software architecture.
