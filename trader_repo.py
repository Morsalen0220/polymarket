# trader_repo.py

from db import get_db


# =========================
# UPDATE TRADER ON TRADE
# =========================
def update_trader_trade(trader_address, usd_size):
    """
    Called when a new trade is detected
    """
    db = get_db()
    trader_address = trader_address.lower()

    ref = db.collection("traders").document(trader_address)
    snap = ref.get()

    if snap.exists:
        data = snap.to_dict()
        ref.update({
            "total_trades": data.get("total_trades", 0) + 1,
            "total_usd": data.get("total_usd", 0) + usd_size,
            "last_seen": data.get("last_seen")
        })
    else:
        ref.set({
            "trader": trader_address,
            "total_trades": 1,
            "total_usd": usd_size,
            "wins": 0,
            "losses": 0,
            "last_seen": None
        })


# =========================
# UPDATE TRADER STATS
# =========================
def update_trader_stats(trader_address, result):
    """
    Phase-B win/loss updater
    """
    db = get_db()
    trader_address = trader_address.lower()

    ref = db.collection("traders").document(trader_address)
    snap = ref.get()

    if not snap.exists:
        return

    data = snap.to_dict()
    wins = data.get("wins", 0)
    losses = data.get("losses", 0)

    if result == "WIN":
        wins += 1
    elif result == "LOSS":
        losses += 1

    ref.update({
        "wins": wins,
        "losses": losses
    })


# =========================
# GET TRADER STATS
# =========================
def get_trader_stats(trader_address):
    db = get_db()
    trader_address = trader_address.lower()

    snap = db.collection("traders").document(trader_address).get()
    if not snap.exists:
        return None

    data = snap.to_dict()
    wins = data.get("wins", 0)
    losses = data.get("losses", 0)
    total = wins + losses

    win_rate = round((wins / total) * 100, 2) if total > 0 else None

    # simple confidence score
    confidence = round(min(100, (total * 20) + (win_rate or 0) * 0.4), 2) if win_rate is not None else 0

    return {
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_trades": data.get("total_trades", 0),
        "total_usd": data.get("total_usd", 0),
        "confidence": confidence
    }
