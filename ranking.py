from db import get_top_traders

def get_trader_rank(trader_address):
    """
    Returns:
    {
      rank: int | None,
      tier: str
    }
    """
    top_traders = get_top_traders(limit=50)

    for idx, t in enumerate(top_traders):
        if t.get("trader") == trader_address:
            rank = idx + 1

            if rank <= 5:
                tier = "ELITE 🏆"
            elif rank <= 20:
                tier = "STRONG 💪"
            else:
                tier = "ACTIVE 🐋"

            return {
                "rank": rank,
                "tier": tier
            }

    return {
        "rank": None,
        "tier": "NEW 🧪"
    }
