"""End-to-end alert pipeline.

What it does:
  1. Run the quality-filtered new-token discovery (from 03_quality_filter logic).
  2. Dedupe against a persisted seen_tokens set ({network}_{address}).
  3. For each truly new entry, format a message and POST to Telegram (if configured).

Designed to be run on a cron/timer (e.g. every 30 seconds in production).

If TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID are not set in .env, the script runs in
DRY mode and prints alerts to stdout instead.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

# Reuse 03_quality_filter helpers
sys.path.insert(0, str(Path(__file__).resolve().parent))
_quality = __import__("03_quality_filter")  # 03_… isn't a valid module name to import normally

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")
SEEN_PATH = REPO_ROOT / "seen_tokens.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def load_seen() -> set[str]:
    if SEEN_PATH.exists():
        try:
            return set(json.loads(SEEN_PATH.read_text()))
        except Exception:
            return set()
    return set()


def save_seen(seen: set[str]) -> None:
    SEEN_PATH.write_text(json.dumps(sorted(seen)))


def key(row: dict) -> str:
    return f"{row['network_id']}_{row['token_address']}"


def format_alert(row: dict) -> str:
    gt = row.get("gt_score")
    gt_str = f"{gt:.0f}" if isinstance(gt, (int, float)) else "—"
    lines = [
        f"🆕 New token on {row['network_name']}",
        f"Symbol: {row['token_symbol']}",
        f"Address: {row['token_address']}",
        f"Reserve: ${row['reserve_usd']:,.0f}   24h Vol: ${row['volume_h24_usd']:,.0f}",
        f"GT Score: {gt_str}   Honeypot: {row.get('is_honeypot', '?')}",
    ]
    if row["network_id"] == "solana":
        lines.append(
            f"Mint authority: {'yes' if row.get('mint_authority') else 'no'}   "
            f"Freeze authority: {'yes' if row.get('freeze_authority') else 'no'}"
        )
    return "\n".join(lines)


def send_telegram(text: str) -> None:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print("[DRY] " + text + "\n")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    if not r.ok:
        print(f"  Telegram error {r.status_code}: {r.text}")


def main() -> None:
    _quality.print_mode_banner()
    print("\nRunning quality-filtered discovery pipeline...\n")

    candidates = _quality.fetch_candidates(_quality.PAGES)
    enriched = _quality.enrich_with_token_info(candidates)
    safe = [r for r in enriched if _quality.is_safe(r)]
    print(f"  {len(safe)} tokens passed quality + safety checks")

    seen = load_seen()
    new_entries = [r for r in safe if key(r) not in seen]
    print(f"  {len(new_entries)} of these are new since last run ({len(seen)} in seen-set)\n")

    for row in new_entries:
        send_telegram(format_alert(row))
        seen.add(key(row))

    save_seen(seen)
    print(f"\nDone. seen_tokens.json now has {len(seen)} entries.")


if __name__ == "__main__":
    main()
