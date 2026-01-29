def should_send_signal(trade, market, score):
    return (
        trade["usd_size"] >= market["top5pct_size"] and
        score >= 70 and
        market["liquidity"] >= 100_000 and
        (market["price"] < 0.42 or market["price"] > 0.58) and
        not trade["is_hedge"]
    )
# filters.py

def is_valid_trade(trade: dict) -> bool:
    """
    Basic sanity filter.
    Future versions can add:
    - duplicate detection
    - router blacklist
    - dust spam
    """

    # minimum structure check
    if not trade:
        return False

    if "tx_hash" not in trade:
        return False

    if "usd_size" not in trade:
        return False

    # allow everything for now
    return True
