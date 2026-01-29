import requests

CLOB_URL = "https://clob.polymarket.com/markets"

def infer_market_from_context():
    """
    Returns inferred market dict or None
    """
    try:
        r = requests.get(CLOB_URL, timeout=10)
        markets = r.json()
        markets = markets if isinstance(markets, list) else markets.get("data", [])

        # Prefer high-liquidity BTC / ETH markets
        priority_keywords = ["bitcoin", "btc", "ethereum", "eth"]

        for m in markets:
            q = (m.get("question") or "").lower()
            if any(k in q for k in priority_keywords):
                if m.get("active") and float(m.get("liquidity", 0)) > 500000:
                    return {
                        "question": m["question"],
                        "asset": "BTC" if "btc" in q or "bitcoin" in q else "ETH",
                        "confidence": "HIGH"
                    }
        return None
    except Exception:
        return None
