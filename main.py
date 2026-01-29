# =========================
# LOGGING (VERY TOP)
# =========================
import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s"
)

logging.getLogger("web3").setLevel(logging.ERROR)
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("firebase_admin").setLevel(logging.ERROR)

# =========================
# IMPORTS
# =========================
import os
import time
import asyncio
from web3 import Web3
from dotenv import load_dotenv

from clob_decoder import decode_block_polymarket_trades
from tx_decoder import decode_polymarket_tx
from market_resolver import resolve_market_by_token
from telegram import send_signal

from signal_repo import save_trade
from trader_repo import get_trader_stats, update_trader_trade
from resolve_markets import resolve_markets
from winloss_processor import process_winloss

# =========================
# THRESHOLDS
# =========================
IGNORE_THRESHOLD = 2000
INFERENCE_THRESHOLD = 10000
POLL_DELAY = 4   # free-plan safe

# =========================
# ENV + WEB3
# =========================
load_dotenv()

ALCHEMY_URL = os.getenv("ALCHEMY_URL")
if not ALCHEMY_URL:
    raise RuntimeError("ALCHEMY_URL missing")

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
assert w3.is_connected(), "Polygon RPC not connected"

USDC_ADDRESS = Web3.to_checksum_address(
    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
)

# =========================
# ONE-TIME STARTUP LOG
# =========================
logging.warning("🚀 POLYMARKET WHALE BOT STARTED (SILENT MODE)")

last_scanned_block = w3.eth.block_number - 2

# =========================
# PHASE-B (SILENT)
# =========================
async def phase_b_loop():
    while True:
        try:
            resolve_markets()
            process_winloss()
        except Exception as e:
            logging.error(f"Phase-B error: {e}")

        await asyncio.sleep(3600)  # every 1 hour

# =========================
# MAIN WHALE LOOP (SILENT)
# =========================
async def whale_loop():
    global last_scanned_block

    while True:
        try:
            block = w3.eth.block_number - 1

            if block <= last_scanned_block:
                await asyncio.sleep(POLL_DELAY)
                continue

            logs = w3.eth.get_logs({
                "fromBlock": block,
                "toBlock": block,
                "address": USDC_ADDRESS
            })

            trades = decode_block_polymarket_trades(logs)

            for trade in trades:
                tx_hash = trade["tx_hash"]
                trader = trade["trader"]
                usd_size = trade["usd_size"]

                if usd_size < IGNORE_THRESHOLD:
                    continue

                # ---- silent whale ----
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

                # ---- signal path ----
                tx_info = decode_polymarket_tx(w3, tx_hash)
                trader_perf = get_trader_stats(trader)

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
                        market={"question": "Market Hidden", "price": 0},
                        trader=trader,
                        tx_hash=tx_hash,
                        note="CLOB / hidden market",
                        trader_perf=trader_perf
                    )
                    continue

                token_id = tx_info["token_id"]
                side = tx_info["side"]
                market = resolve_market_by_token(token_id)

                save_trade(
                    tx_hash=tx_hash,
                    trader=trader,
                    usdc_amount=usd_size,
                    block_number=block,
                    timestamp=int(time.time()),
                    market_id=market["id"] if market else None,
                    token_id=token_id,
                    side=side,
                    is_fallback=not bool(market)
                )

                update_trader_trade(trader, usd_size)

                if market:
                    send_signal(
                        trade={"side": side, "usd_size": usd_size},
                        market={"question": market["question"], "price": 0},
                        trader=trader,
                        tx_hash=tx_hash,
                        note="LIVE",
                        trader_perf=trader_perf
                    )

            last_scanned_block = block
            await asyncio.sleep(POLL_DELAY)

        except Exception as e:
            logging.error(f"Whale loop error: {e}")
            await asyncio.sleep(5)

# =========================
# ENTRYPOINT
# =========================
async def main():
    asyncio.create_task(phase_b_loop())
    await whale_loop()

if __name__ == "__main__":
    asyncio.run(main())
