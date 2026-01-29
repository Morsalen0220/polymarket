# signal_repo.py

from db import db
from datetime import datetime

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
    trade = {
        "txHash": tx_hash,
        "trader": trader.lower(),
        "usdcAmount": usdc_amount,
        "blockNumber": block_number,
        "timestamp": timestamp,
        "marketId": market_id,
        "tokenId": token_id,
        "side": side,
        "isFallback": is_fallback,
        "resolved": False,
        "outcome": None,
        "createdAt": datetime.utcnow(),
    }

    db.collection(COLLECTION).document(tx_hash).set(trade)


def get_unresolved_trades():
    return (
        db.collection(COLLECTION)
        .where("resolved", "==", False)
        .stream()
    )


def mark_trade_resolved(tx_hash, outcome, result):
    db.collection(COLLECTION).document(tx_hash).update(
        {
            "resolved": True,
            "outcome": outcome,
            "result": result,
            "resolvedAt": datetime.utcnow(),
        }
    )
