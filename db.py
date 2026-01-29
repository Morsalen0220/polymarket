# db.py

import os
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

# =========================
# FIREBASE INIT
# =========================
_db = None

def init_db():
    global _db
    if _db:
        return _db

    # Option 1: local serviceAccountKey.json
    if os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")

    # Option 2: env variable (Render / prod)
    else:
        firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        if not firebase_json:
            raise Exception("❌ Firebase credentials not found")

        cred = credentials.Certificate(json.loads(firebase_json))

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    _db = firestore.client()
    print("✅ Firebase Firestore connected")
    return _db


# =========================
# EXPORT DB HANDLE
# =========================
db = init_db()

# ==========================================================
# TRADE FUNCTIONS (LEGACY SAFE + PHASE-B COMPATIBLE)
# ==========================================================

def save_trade(trade: dict):
    """
    Legacy-compatible trade save.
    Accepts dict and stores directly.
    """
    trade["timestamp"] = trade.get("timestamp", int(time.time()))
    db.collection("trades").document(trade["tx_hash"]).set(trade)


# ==========================================================
# TRADER FUNCTIONS
# ==========================================================

def update_trader(trader_address, usd_size):
    trader_address = trader_address.lower()
    ref = db.collection("traders").document(trader_address)
    snap = ref.get()

    if snap.exists:
        data = snap.to_dict()
        ref.update({
            "total_trades": data.get("total_trades", 0) + 1,
            "total_usd": data.get("total_usd", 0) + usd_size,
            "last_seen": int(time.time())
        })
    else:
        ref.set({
            "trader": trader_address,
            "total_trades": 1,
            "total_usd": usd_size,
            "wins": 0,
            "losses": 0,
            "last_seen": int(time.time())
        })


def update_trader_stats(trader_address, result):
    """
    Phase-B win/loss updater
    """
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
        "losses": losses,
        "last_seen": int(time.time())
    })


def get_trader_stats(trader_address):
    trader_address = trader_address.lower()
    snap = db.collection("traders").document(trader_address).get()

    if not snap.exists:
        return None

    data = snap.to_dict()
    wins = data.get("wins", 0)
    losses = data.get("losses", 0)
    total = wins + losses

    win_rate = round((wins / total) * 100, 2) if total > 0 else None

    return {
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate
    }


def get_top_traders(limit=50):
    docs = (
        db.collection("traders")
        .order_by("total_usd", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [d.to_dict() for d in docs]
