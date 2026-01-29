# winloss_processor.py

import time
from db import db
from trader_repo import update_trader_stats, get_trader_stats
from telegram import send_signal

TRADES_COL = "trades"


def process_winloss():
    """
    Normal Phase-B processor (auto mode)
    """
    print("🟢 Phase-B heartbeat: resolver + winloss ran")


# =========================
# 🔥 MANUAL DEBUG TEST
# =========================
def debug_force_win(tx_hash, result="WIN"):
    """
    Force a WIN / LOSS for a trade (DEBUG ONLY)
    """

    ref = db.collection(TRADES_COL).document(tx_hash)
    snap = ref.get()

    if not snap.exists:
        print("❌ Trade not found:", tx_hash)
        return

    trade = snap.to_dict()
    trader = trade["trader"]

    # ---- resolve USD size safely ----
    usd_size = trade.get("usdc_amount") or trade.get("usd_size") or 0

    # ---- mark resolved ----
    ref.update({
        "resolved": True,
        "result": result,
        "resolved_at": int(time.time())
    })

    # ---- update trader stats ----
    update_trader_stats(trader, result)
    stats = get_trader_stats(trader)

    print("🧪 DEBUG RESULT")
    print("Trader:", trader)
    print("Result:", result)
    print("Stats:", stats)

    # ---- send debug telegram ----
    send_signal(
        trade={
            "usd_size": usd_size,
            "side": trade.get("side", "UNKNOWN")
        },
        market={
            "question": "DEBUG MARKET (manual resolve)"
        },
        trader=trader,
        tx_hash=tx_hash,
        note="🧪 Manual debug win/loss test",
        trader_perf=stats
    )
