# market_resolver.py

import requests

POLYMARKET_API = "https://api.polymarket.com"


# =========================
# PHASE-A (token → market)
# =========================
def resolve_market_by_token(token_id):
    try:
        r = requests.get(
            f"{POLYMARKET_API}/markets?token_id={token_id}",
            timeout=10
        )
        if r.status_code != 200:
            return None

        data = r.json()
        if not data:
            return None

        m = data[0]
        return {
            "id": m.get("id"),
            "question": m.get("question"),
            "asset": m.get("asset", "UNKNOWN"),
            "active": m.get("active", False),
            "side": None
        }

    except Exception as e:
        print("⚠️ resolve_market_by_token:", e)
        return None


# =========================
# PHASE-B (marketId → outcome)
# =========================
def fetch_market_by_id(market_id):
    try:
        r = requests.get(
            f"{POLYMARKET_API}/markets/{market_id}",
            timeout=10
        )
        if r.status_code != 200:
            return None

        m = r.json()

        outcome = None
        if m.get("resolved"):
            outcome = "YES" if m.get("outcome") == "YES" else "NO"

        return {
            "id": market_id,
            "status": "CLOSED" if m.get("resolved") else "OPEN",
            "outcome": outcome
        }

    except Exception as e:
        print("⚠️ fetch_market_by_id:", e)
        return None
