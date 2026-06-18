import logging
import market_maker
import time
from polymarket_client import client
from py_clob_client.clob_types import BalanceAllowanceParams, AssetType


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

MAX_POSITION_PER_MARKET = 100 # Max position per market in USD
DAILY_LOSS_LIMIT = 0.05 # Stop trading for the day if loss exceeds this fraction of starting capital
REBALANCE_INTERVAL = 60 # Seconds between order refreshes


def get_balance(client) -> float:
    """Returns USDC collateral balance in dollars."""

    result = client.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL)
    )

    # Return balance as a raw integer string (6 decimal places for USDC)
    return int(result["balance"]) / 1e6


def cancel_all_orders(client, active_orders: dict):
    """Cancel all tracked open orders."""

    try:
        client.cancel_all()
        logging.info("All orders cancelled.")
    
    except Exception as e:
        logging.error(f"Failed to cancel all orders: {e}")

        # Falllback: cancel individually by tracked ID's
        for market_id, order_ids in active_orders.items():
            for oid in order_ids:
                try:
                    client.cancel(oid)
                except Exception as inner_e:
                    logging.error(f"Failed to cancel order {oid}: {inner_e}")


def run():
    starting_balance = get_balance(client) # Implement via API
    daily_floor = starting_balance * (1 - DAILY_LOSS_LIMIT)

    active_orders = {}

    while True:
        # Safety check
        current_balance = get_balance(client)
        if current_balance < daily_floor:
            logging.warning("Daily loss limit exceeded. Stopping trading.")
            cancel_all_orders(client, active_orders)
            break
            
        # Canel stale orders (prices may have moved)
        cancel_all_orders(client, active_orders)
        active_orders.clear()

        # Find fresh opportunities
        markets = market_maker.find_good_markets()[:10] # Top 10 candidates

        for market in markets:
            try:
                buy_response, sell_response = market_maker.place_mm_orders(
                    client, market,
                    capital_per_market=MAX_POSITION_PER_MARKET
                )

                active_orders[market["condition_id"]] = [
                    buy_response["orderID"], 
                    sell_response["orderID"]
                ]

                logging.info(
                    f"Quoting: {market['question'][:50]} | "
                    f"Spread: {market['spread']:.3f}"
                )
            
            except Exception as e:
                logging.error(f"Order failed: {e}")
        
        
        time.sleep(REBALANCE_INTERVAL)


run()
