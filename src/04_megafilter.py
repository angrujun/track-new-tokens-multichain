"""Paid-plan alternative: one call to /onchain/pools/megafilter.

Megafilter does the work of 03_quality_filter.py in a single call, with a richer
parameter set (FDV range, tax %, GT score, honeypot check, age bounds, etc.).

Plan tier: CoinGecko API Lite Plan and above. Will return HTTP 401 / error 10005
on the Demo plan. Set CG_API_MODE=pro in .env to use this script.

Pricing: https://www.coingecko.com/en/api/pricing
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from cg_client import get, index_included, resolve_relationship, print_mode_banner, MODE

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def fetch_megafilter() -> list[dict]:
    payload = get(
        "/onchain/pools/megafilter",
        params={
            "include": "base_token,network",
            "pool_created_hour_max": 48,
            "reserve_in_usd_min": 5_000,
            "h24_volume_usd_min": 1_000,
            "checks": "no_honeypot,good_gt_score",
            "sort": "pool_created_at_desc",
            "page": 1,
        },
    )
    included = index_included(payload)
    rows = []
    for pool in payload.get("data", []):
        attrs = pool["attributes"]
        base_token = resolve_relationship(pool, "base_token", included)
        network = resolve_relationship(pool, "network", included)
        rows.append({
            "network": (network or {}).get("attributes", {}).get("name", "?"),
            "network_id": (network or {}).get("id", "?"),
            "token_symbol": (base_token or {}).get("attributes", {}).get("symbol", "?"),
            "token_address": (base_token or {}).get("attributes", {}).get("address", ""),
            "pool_created_at": attrs["pool_created_at"],
            "reserve_usd": float(attrs.get("reserve_in_usd") or 0),
            "volume_h24_usd": float(attrs.get("volume_usd", {}).get("h24") or 0),
            "fdv_usd": float(attrs.get("fdv_usd") or 0),
        })
    return rows


def main() -> None:
    print_mode_banner()
    if MODE != "pro":
        print("\nWARNING: Megafilter requires a paid plan (Lite or higher).")
        print("Set CG_API_MODE=pro in .env and use your Pro key.")
        print("Continuing anyway — the call will likely fail with 401 or 10005.\n")

    print("Fetching pools via Megafilter (created < 48h, reserve > $5k, vol > $1k, no_honeypot, good_gt_score)...\n")
    try:
        rows = fetch_megafilter()
    except Exception as e:
        print(f"\nMegafilter call failed: {e}")
        print("If you're on the Demo plan, this is expected.")
        sys.exit(1)

    print(f"{'Network':<14} {'Symbol':<10} {'Pool age':<22} {'Reserve':>14} {'24h Vol':>14}")
    print("-" * 80)
    for row in rows[:20]:
        print(f"{row['network'][:13]:<14} {row['token_symbol'][:9]:<10} "
              f"{row['pool_created_at']:<22} {row['reserve_usd']:>14,.0f} {row['volume_h24_usd']:>14,.0f}")

    OUTPUT_DIR.joinpath("csv").mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.joinpath("json").mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = OUTPUT_DIR / "csv" / f"megafilter_{ts}.csv"
    json_path = OUTPUT_DIR / "json" / f"megafilter_{ts}.json"
    if rows:
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        json_path.write_text(json.dumps(rows, indent=2))
        print(f"\nWrote {len(rows)} pools to {csv_path.name} / {json_path.name}")


if __name__ == "__main__":
    main()
