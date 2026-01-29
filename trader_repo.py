# trader_repo.py

import time
import math
from db import db

COLLECTION = "traders"


def _ref(address):
    return db.collection(COLLECTION).document(address.lower())


# =========================
# UPDATE TRADE VOLUME
# =========================
def update_trader_trade(trader_address, usd_size):
    ref = _ref(trader_address)
    snap = ref.get()

    if snap.exists:
        d = snap.to_dict()
        ref.update({
            "total_trades": d.get("total_trades", 0) + 1,
            "total_usd": d.get("total_usd", 0) + usd_size,
            "last_seen": int(time.time())
        })
    else:
        ref.set({
            "trader": trader_address.lower(),
            "total_trades": 1,
            "total_usd": usd_size,
            "wins": 0,
            "losses": 0,
            "last_seen": int(time.time())
        })


# =========================
# PHASE-B: WIN / LOSS
# =========================
def update_trader_stats(trader_address, result):
    if result not in ("WIN", "LOSS"):
        return

    ref = _ref(trader_address)
    snap = ref.get()
    if not snap.exists:
        return

    d = snap.to_dict()
    wins = d.get("wins", 0)
    losses = d.get("losses", 0)

    if result == "WIN":
        wins += 1
    else:
        losses += 1

    ref.update({
        "wins": wins,
        "losses": losses,
        "last_seen": int(time.time())
    })


# =========================
# READ + CONFIDENCE SCORE
# =========================
def get_trader_stats(trader_address):
    snap = _ref(trader_address).get()
    if not snap.exists:
        return None

    d = snap.to_dict()
    wins = d.get("wins", 0)
    losses = d.get("losses", 0)
    total_trades = d.get("total_trades", 0)

    total = wins + losses
    win_rate = round((wins / total) * 100, 2) if total > 0 else None

    # ---- CONFIDENCE SCORE ----
    if win_rate is not None:
        confidence = win_rate * math.log10(total_trades + 1)
        confidence = min(100, round(confidence, 1))
    else:
        confidence = None

    return {
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "total_trades": total_trades,
        "total_usd": d.get("total_usd", 0),
        "confidence": confidence
    }
