# signal_repo.py

from datetime import datetime
from db import get_db

COLLECTION = "trades"


def save_trade(
    tx_hash,
    trader,
    usdc_amount,
    block_number,
    timestamp,
    market_id=None,
    token_id=None,
    side="UNKNOWN",
    is_fallback=False,
):
    """
    Save a trade to Firestore (Phase-A + Phase-B compatible)
    """
    db = get_db()

    trade = {
        "tx_hash": tx_hash,
        "trader": trader.lower(),
        "usdc_amount": usdc_amount,
        "block_number": block_number,
        "timestamp": timestamp,
        "market_id": market_id,
        "token_id": token_id,
        "side": side,
        "is_fallback": is_fallback,
        "resolved": False,
        "outcome": None,
        "created_at": datetime.utcnow(),
    }

    db.collection(COLLECTION).document(tx_hash).set(trade)


def get_unresolved_trades():
    db = get_db()
    return (
        db.collection(COLLECTION)
        .where("resolved", "==", False)
        .stream()
    )


def mark_trade_resolved(tx_hash, outcome, result):
    db = get_db()
    db.collection(COLLECTION).document(tx_hash).update(
        {
            "resolved": True,
            "outcome": outcome,
            "result": result,
            "resolved_at": datetime.utcnow(),
        }
    )
