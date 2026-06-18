#from pytest import mark
import requests
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY, SELL

def find_good_markets(min_volume=5000, min_prob=0.1, max_prob=0.9, min_spread=0.005, max_spread=0.02):
    """Fetch active markets from Gamma API, filter for good MM candidates."""
    response = requests.get(
        "https://gamma-api.polymarket.com/markets",    
        params={"active": True, "closed": False, "limit": 200}
    )
    markets = response.json()

    candidates = []
    volumes = []
    spreads = []
    mids = []
    for m in markets:
        volume = float(m.get("volume24hr", 0))
        best_bid = float(m.get("bestBid", 0))
        best_ask = float(m.get("bestAsk", 1))
        spread = best_ask - best_bid
        mid = (best_bid + best_ask) / 2

        volumes.append(volume)
        spreads.append(spread)
        mids.append(mid)

        if volume >= min_volume and min_spread <= spread <= max_spread and min_prob < mid < max_prob:
            candidates.append({
                "question": m["question"],
                "condition_id": m["conditionId"],
                "yes_token": m["clobTokenIds"][0],
                "no_token": m["clobTokenIds"][1],
                "spread": spread,
                "mid": mid,
                "volume": volume
            })

        
    # Sort by spread (wider = more profit potential)
    return sorted(candidates, key=lambda x: x["spread"], reverse=True)


def place_mm_orders(client, market, capital_per_market=50, edge=0.01):
    """
    Place limit orders on both sides of the market.
    edge: how much inside the spread to place orders (0.01 = 1% inside the spread)
    """

    mid = market["mid"]

    # Quote slightly inside the current spread to be best price
    our_bid = round(mid - edge, 3) # Buy YES slightly below mid
    our_ask = round(mid + edge, 3) # Sell YES slightly above mid

    # Size: use a fraction of capital per side
    size = round(capital_per_market / our_ask, 1)

    # Place BUY limit order (we buy YES cheap)
    buy_order = OrderArgs(
        token_id=market["yes_token"],
        price=our_bid,
        size=size,
        side=BUY
    )

    # Place SELL limit order (we sell YES expensive)
    sell_order = OrderArgs(
        token_id=market["yes_token"],
        price=our_ask,
        size=size,
        side=SELL
    )

    response_buy = client.create_and_post_order(buy_order)
    response_sell = client.create_and_post_order(sell_order)

    return response_buy, response_sell


markets = find_good_markets()
print("Done finding markets.")
for m in markets[:5]:
    print(f"{m['question'][:60]}")
    print(f"Spread: {m['spread']:.3f} | Mid: {m['mid']:.2f} | Vol: ${m['volume']:,.0f}\n")