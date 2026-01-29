# market_outcome.py

from datetime import datetime
from db import get_db

COLLECTION = "market_outcomes"


def save_market_outcome(market_id, outcome):
    """
    Save resolved market outcome
    """
    db = get_db()

    data = {
        "market_id": market_id,
        "outcome": outcome,
        "resolved_at": datetime.utcnow()
    }

    db.collection(COLLECTION).document(str(market_id)).set(data)


def fetch_market_outcome(market_id):
    """
    Fetch market outcome if exists
    """
    db = get_db()
    doc = db.collection(COLLECTION).document(str(market_id)).get()

    if not doc.exists:
        return None

    return doc.to_dict()
