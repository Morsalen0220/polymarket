# market_outcome.py

from db import db

COLLECTION = "market_outcomes"


def save_market_outcome(market_id, outcome):
    """
    outcome: YES / NO
    """
    db.collection(COLLECTION).document(market_id).set({
        "marketId": market_id,
        "outcome": outcome
    })


def get_market_outcome(market_id):
    snap = db.collection(COLLECTION).document(market_id).get()
    if not snap.exists:
        return None
    return snap.to_dict().get("outcome")
