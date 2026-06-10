"""Fetch new pools scoped to a single network (Solana, Base, BSC, etc.).

Usage:
    python src/02_perchain_new_pools.py solana
    python src/02_perchain_new_pools.py base
    python src/02_perchain_new_pools.py bsc
    python src/02_perchain_new_pools.py eth

GeckoTerminal network IDs are NOT the same as CoinGecko asset platform IDs:
    Solana    → 'solana'   (not 'solana')           ← same
    Base      → 'base'     (not 'base')             ← same
    BSC       → 'bsc'      (not 'binance-smart-chain')
    Ethereum  → 'eth'      (not 'ethereum')

Call /onchain/networks to list every supported ID.
"""
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from cg_client import get, index_included, resolve_relationship, print_mode_banner

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
DEFAULT_NETWORK = "solana"


def fetch_perchain_new_pools(network: str, pages: int = 1) -> list[dict]:
    rows = []
    for page in range(1, pages + 1):
        payload = get(
            f"/onchain/networks/{network}/new_pools",
            params={"include": "base_token,quote_token", "page": page},
        )
        included = index_included(payload)
        for pool in payload.get("data", []):
            attrs = pool["attributes"]
            base_token = resolve_relationship(pool, "base_token", included)
            rows.append({
                "network_id": network,
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


def main() -> None:
    network = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_NETWORK
    print_mode_banner()
    print(f"\nFetching new pools on network '{network}'...\n")

    rows = fetch_perchain_new_pools(network)
    if not rows:
        print(f"No pools returned. Is '{network}' a valid network id? Run /onchain/networks to list ids.")
        return

    print(f"{'Symbol':<10} {'Token name':<24} {'Pool age':<22} {'Reserve USD':>14} {'24h Vol USD':>14}")
    print("-" * 90)
    for row in rows[:15]:
        print(f"{row['token_symbol'][:9]:<10} {row['token_name'][:23]:<24} "
              f"{row['pool_created_at']:<22} {row['reserve_usd']:>14,.0f} {row['volume_h24_usd']:>14,.0f}")

    OUTPUT_DIR.joinpath("csv").mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.joinpath("json").mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = OUTPUT_DIR / "csv" / f"{network}_new_pools_{ts}.csv"
    json_path = OUTPUT_DIR / "json" / f"{network}_new_pools_{ts}.json"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(rows, indent=2))
    print(f"\nWrote {len(rows)} pools to {csv_path.name} / {json_path.name}")


if __name__ == "__main__":
    main()
