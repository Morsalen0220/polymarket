# resolve_markets.py

from signal_repo import get_unresolved_trades
from market_resolver import fetch_market_by_id
from market_outcome import save_market_outcome


def resolve_markets():
    trades = get_unresolved_trades()

    for doc in trades:
        trade = doc.to_dict()

        market_id = trade.get("marketId")
        if not market_id:
            continue

        market = fetch_market_by_id(market_id)
        if not market:
            continue

        if market.get("status") != "CLOSED":
            continue

        outcome = market.get("outcome")
        if outcome not in ["YES", "NO"]:
            continue

        save_market_outcome(market_id, outcome)
