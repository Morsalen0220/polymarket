# main.py

import logging

logging.getLogger().setLevel(logging.WARNING)
logging.getLogger("web3").setLevel(logging.ERROR)
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)


import os
import time
import asyncio
from web3 import Web3
from dotenv import load_dotenv

from clob_decoder import decode_block_polymarket_trades
from tx_decoder import decode_polymarket_tx
from market_resolver import resolve_market_by_token
from market_inference import infer_market_from_context
from telegram import send_signal

from signal_repo import save_trade
from trader_repo import get_trader_stats, update_trader_trade

from resolve_markets import resolve_markets
from winloss_processor import process_winloss

# =========================
# THRESHOLDS (OPTION A)
# =========================
IGNORE_THRESHOLD = 2000        # < $2k → ignore
INFERENCE_THRESHOLD = 10000    # ≥ $10k → inference + Telegram
POLL_DELAY = 1

# =========================
# ENV + WEB3
# =========================
load_dotenv()

ALCHEMY_URL = os.getenv("ALCHEMY_URL")
if not ALCHEMY_URL:
    raise Exception("❌ ALCHEMY_URL missing in .env")

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
assert w3.is_connected(), "❌ Polygon RPC connection failed"

USDC_ADDRESS = Web3.to_checksum_address(
    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
)

print("\n🚀 POLYMARKET WHALE SIGNAL BOT (OPTION A — SAFE & PRO)")
print("⏳ Monitoring Polygon blocks...\n")

last_scanned_block = w3.eth.block_number - 2

# =========================
# PHASE-B BACKGROUND LOOP
# =========================
async def phase_b_loop():
    while True:
        try:
            resolve_markets()
            process_winloss()
            print("🟢 Phase-B heartbeat: resolver + winloss ran")
        except Exception as e:
            print("⚠️ Phase-B error:", e)

        await asyncio.sleep(3600)  # every 1 hour


# =========================
# MAIN WHALE LOOP
# =========================
async def whale_loop():
    global last_scanned_block

    while True:
        try:
            latest_block = w3.eth.block_number
            block = latest_block - 1

            if block <= last_scanned_block:
                await asyncio.sleep(POLL_DELAY)
                continue

            print(f"\n🔍 Scanning block {block}")

            logs = w3.eth.get_logs({
                "fromBlock": block,
                "toBlock": block,
                "address": USDC_ADDRESS
            })

            trades = decode_block_polymarket_trades(logs)
            print(f"🔎 Polymarket-related TXs: {len(trades)}")

            for trade in trades:
                tx_hash = trade["tx_hash"]
                trader = trade["trader"]
                usd_size = trade["usd_size"]

                print(f"\n➡️ TX {tx_hash} | ${usd_size}")

                # -------------------------
                # IGNORE SMALL
                # -------------------------
                if usd_size < IGNORE_THRESHOLD:
                    continue

                # -------------------------
                # SILENT WHALE
                # -------------------------
                if usd_size < INFERENCE_THRESHOLD:
                    save_trade(
                        tx_hash=tx_hash,
                        trader=trader,
                        usdc_amount=usd_size,
                        block_number=block,
                        timestamp=int(time.time()),
                        side="UNKNOWN",
                        is_fallback=True
                    )
                    update_trader_trade(trader, usd_size)
                    continue

                # -------------------------
                # ≥ $10k → SIGNAL PATH
                # -------------------------
                tx_info = decode_polymarket_tx(w3, tx_hash)

                trader_perf = get_trader_stats(trader)

                # ===== DECODE FAILED → INFERENCE =====
                if not tx_info:
                    save_trade(
                        tx_hash=tx_hash,
                        trader=trader,
                        usdc_amount=usd_size,
                        block_number=block,
                        timestamp=int(time.time()),
                        side="UNKNOWN",
                        is_fallback=True
                    )

                    send_signal(
                        trade={"side": "UNKNOWN", "usd_size": usd_size},
                        market={"question": "Market Hidden / Inference", "price": 0},
                        trader=trader,
                        tx_hash=tx_hash,
                        note="Executed via CLOB (market hidden)",
                        trader_perf=trader_perf
                    )
                    continue

                # ===== DECODE SUCCESS =====
                token_id = tx_info["token_id"]
                side = tx_info["side"]

                market = resolve_market_by_token(token_id)

                # ---- MARKET RESOLVE FAIL ----
                if not market:
                    save_trade(
                        tx_hash=tx_hash,
                        trader=trader,
                        usdc_amount=usd_size,
                        block_number=block,
                        timestamp=int(time.time()),
                        side=side,
                        is_fallback=True
                    )

                    send_signal(
                        trade={"side": side, "usd_size": usd_size},
                        market={"question": "Market Hidden", "price": 0},
                        trader=trader,
                        tx_hash=tx_hash,
                        note="Market metadata unavailable",
                        trader_perf=trader_perf
                    )
                    continue

                # ---- FULL VERIFIED ----
                save_trade(
                    tx_hash=tx_hash,
                    trader=trader,
                    usdc_amount=usd_size,
                    block_number=block,
                    timestamp=int(time.time()),
                    market_id=market["id"],
                    token_id=token_id,
                    side=side,
                    is_fallback=False
                )

                update_trader_trade(trader, usd_size)

                send_signal(
                    trade={"side": side, "usd_size": usd_size},
                    market={"question": market["question"], "price": 0},
                    trader=trader,
                    tx_hash=tx_hash,
                    note=f"📌 Market: {'LIVE' if market['active'] else 'CLOSED'}",
                    trader_perf=trader_perf
                )

            last_scanned_block = block
            await asyncio.sleep(POLL_DELAY)

        except Exception as e:
            print("⚠️ Whale loop error:", e)
            await asyncio.sleep(3)


# =========================
# ENTRYPOINT
# =========================
async def main():
    asyncio.create_task(phase_b_loop())
    await whale_loop()

from winloss_processor import debug_force_win

#debug_force_win(
   # tx_hash="38d88e2d08344169b5ee4d7d03b8cb20fcf6c1e3f0e0ebcf4d21c7fe043b4384",
   # result="WIN"  
#)

#exit() 


if __name__ == "__main__":
    asyncio.run(main())
# ===== DEBUG MANUAL TEST =====
# Uncomment ONLY for testing, then comment again

# from winloss_processor import debug_force_win
# 
#
    #debug_force_win(
      #  tx_hash="PUT_ONE_REAL_TX_HASH_HERE",
        #  result="WIN"  # or "LOSS"
        #   )
