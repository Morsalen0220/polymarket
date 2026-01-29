from ranking import get_top_50_traders

_top50_cache = set()

def refresh_top50():
    global _top50_cache
    _top50_cache = get_top_50_traders()

def is_elite_trader(address: str):
    return address.lower() in _top50_cache
