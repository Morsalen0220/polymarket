import requests

def get_market_context(token_id):
    try:
        r = requests.get(
            f"https://gamma-api.polymarket.com/tokens?token_id={token_id}",
            timeout=10
        ).json()

        m = r.get("market")
        if not m:
            return None

        price = float(r.get("price", 0))
        liquidity = float(m.get("openInterest", 0))

        return {
            "question": m.get("question", "Polymarket Market"),
            "price": price,
            "liquidity": liquidity,
            "top5pct_size": liquidity * 0.05
        }
    except:
        return None
