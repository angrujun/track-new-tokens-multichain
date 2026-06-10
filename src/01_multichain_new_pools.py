"""Fetch the latest new pools across all 250+ networks supported by GeckoTerminal.

One call to /onchain/networks/new_pools returns the most recently created
pools across every chain, 20 per page. We resolve the sideloaded base_token
and network for each pool and write a CSV + JSON snapshot to output/.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from cg_client import get, index_included, resolve_relationship, print_mode_banner

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
PAGES = 2  # 20 pools/page → 40 newest pools across all chains


def fetch_multichain_new_pools(pages: int = PAGES) -> list[dict]:
    rows = []
    for page in range(1, pages + 1):
        payload = get(
            "/onchain/networks/new_pools",
            params={"include": "base_token,quote_token,network", "page": page},
        )
        included = index_included(payload)
        for pool in payload.get("data", []):
            attrs = pool["attributes"]
            base_token = resolve_relationship(pool, "base_token", included)
            network = resolve_relationship(pool, "network", included)
            rows.append({
                "network": (network or {}).get("attributes", {}).get("name", "unknown"),
                "network_id": (network or {}).get("id", "unknown"),
                "token_symbol": (base_token or {}).get("attributes", {}).get("symbol", "?"),
                "token_name": (base_token or {}).get("attributes", {}).get("name", "?"),
                "token_address": (base_token or {}).get("attributes", {}).get("address", ""),
                "pool_address": attrs["address"],
                "pool_created_at": attrs["pool_created_at"],
                "reserve_usd": float(attrs.get("reserve_in_usd") or 0),
                "volume_h24_usd": float(attrs.get("volume_usd", {}).get("h24") or 0),
                "fdv_usd": float(attrs.get("fdv_usd") or 0),
            })
    return rows


def write_outputs(rows: list[dict]) -> None:
    OUTPUT_DIR.joinpath("csv").mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.joinpath("json").mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = OUTPUT_DIR / "csv" / f"multichain_new_pools_{ts}.csv"
    json_path = OUTPUT_DIR / "json" / f"multichain_new_pools_{ts}.json"

    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(json.dumps(rows, indent=2))
    print(f"\nWrote {len(rows)} pools to:\n  {csv_path}\n  {json_path}")


def main() -> None:
    print_mode_banner()
    print(f"\nFetching new pools across all networks ({PAGES} pages = up to {PAGES * 20} pools)...\n")
    rows = fetch_multichain_new_pools()

    print(f"{'Network':<14} {'Symbol':<10} {'Pool age':<22} {'Reserve USD':>14} {'24h Vol USD':>14}")
    print("-" * 80)
    for row in rows[:10]:
        print(f"{row['network'][:13]:<14} {row['token_symbol'][:9]:<10} "
              f"{row['pool_created_at']:<22} {row['reserve_usd']:>14,.0f} {row['volume_h24_usd']:>14,.0f}")
    if len(rows) > 10:
        print(f"... and {len(rows) - 10} more")

    write_outputs(rows)


if __name__ == "__main__":
    main()
