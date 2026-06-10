"""Scheduled alert pipeline.

Run on a cron job (every 30 to 60 seconds). Pulls quality-filtered new tokens,
dedupes against a persisted set, and posts only the new ones to Telegram.
If TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID aren't set, prints to stdout instead.
"""
import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from quality_filter import fetch_candidates, enrich_with_token_info, is_safe

load_dotenv()
SEEN_PATH = Path(__file__).resolve().parent.parent / "seen_tokens.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def load_seen():
    """Read the persisted dedupe set so reruns don't re-alert on the same tokens."""
    if SEEN_PATH.exists():
        return set(json.loads(SEEN_PATH.read_text()))
    return set()


def save_seen(seen):
    SEEN_PATH.write_text(json.dumps(sorted(seen)))


def token_key(row):
    """A token is uniquely identified by its network plus contract address."""
    return f"{row['network_id']}_{row['address']}"


def format_alert(row):
    return (
        f"New token on {row['network']}\n"
        f"Symbol: {row['symbol']}\n"
        f"Address: {row['address']}\n"
        f"Reserve: ${row['reserve_usd']:,.0f}\n"
        f"GT Score: {row.get('gt_score', '-')}"
    )


def send_telegram(text):
    """Post to Telegram. Dry mode (stdout) if credentials aren't set."""
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print(text + "\n")
        return
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
        timeout=10,
    )


if __name__ == "__main__":
    candidates = fetch_candidates()
    enrich_with_token_info(candidates)
    safe = [r for r in candidates if is_safe(r)]

    seen = load_seen()
    new_tokens = [r for r in safe if token_key(r) not in seen]
    for row in new_tokens:
        send_telegram(format_alert(row))
        seen.add(token_key(row))
    save_seen(seen)

    print(f"\nProcessed {len(safe)} tokens, {len(new_tokens)} new this run.")
