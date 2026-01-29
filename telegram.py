# telegram.py

import os
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise Exception("❌ Telegram credentials missing")


def send_signal(trade, market, trader, tx_hash, note="", trader_perf=None):
    """
    Sends whale alert to Telegram (HTML-safe, tx hash sanitized)
    """

    trader_short = trader[:6] + "..." + trader[-4:]

    # 🔥 CRITICAL FIX
    clean_hash = tx_hash.strip()
    encoded_hash = urllib.parse.quote(clean_hash)
    tx_url = f"https://polygonscan.com/tx/{encoded_hash}"

    # -------------------------
    # Trader performance block
    # -------------------------
    if trader_perf and trader_perf.get("win_rate") is not None:
        perf_text = (
            "🟢 <b>Trader Performance</b>\n"
            f"Win rate: {int(trader_perf['win_rate'])}%\n"
            f"Trades: {trader_perf['total_trades']}\n"
            f"Confidence: <b>{int(trader_perf['confidence'])}/100</b>"
        )
    else:
        perf_text = (
            "⚪ <b>Trader Performance</b>\n"
            "Unranked / New"
        )

    message = (
        "🐋 <b>POLYMARKET WHALE ALERT</b>\n\n"
        f"💰 <b>Size:</b> ${trade['usd_size']}\n"
        f"📊 <b>Side:</b> {trade['side']}\n"
        f"🧠 <b>Market:</b> {market['question']}\n\n"
        f"👤 <b>Trader:</b> <code>{trader_short}</code>\n"
        f"{perf_text}\n\n"
        f"📝 {note}\n"
        f"🔗 <a href=\"{tx_url}\">View Tx</a>"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    r = requests.post(url, json=payload, timeout=10)
    if r.status_code != 200:
        print("⚠️ Telegram send failed:", r.text)
