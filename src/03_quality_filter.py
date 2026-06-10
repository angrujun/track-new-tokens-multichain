"""Quality filter for new tokens.

Pipeline:
  1. Pull multi-chain new pools (Demo plan).
  2. Filter pools with reserve_in_usd > MIN_LIQUIDITY and volume_h24 > MIN_VOLUME.
  3. For each surviving token, call /onchain/networks/{network}/tokens/{address}/info
     to attach: gt_score, is_honeypot, and (Solana only) mint_authority + freeze_authority.
  4. Rank by gt_score descending, write CSV/JSON.

This is the manual approach. For one-call filtered discovery with more knobs,
see src/04_megafilter.py (paid plan).
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from cg_client import get, index_included, resolve_relationship, print_mode_banner

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
MIN_LIQUIDITY_USD = 5_000
MIN_VOLUME_H24_USD = 1_000
PAGES = 2


def fetch_candidates(pages: int) -> list[dict]:
    candidates = []
    for page in range(1, pages + 1):
        payload = get(
            "/onchain/networks/new_pools",
            params={"include": "base_token,network", "page": page},
        )
        included = index_included(payload)
        for pool in payload.get("data", []):
            attrs = pool["attributes"]
            reserve = float(attrs.get("reserve_in_usd") or 0)
            volume = float(attrs.get("volume_usd", {}).get("h24") or 0)
            if reserve < MIN_LIQUIDITY_USD or volume < MIN_VOLUME_H24_USD:
                continue
            base_token = resolve_relationship(pool, "base_token", included)
            network = resolve_relationship(pool, "network", included)
            if not base_token or not network:
                continue
            candidates.append({
                "network_id": network["id"],
                "network_name": network["attributes"]["name"],
                "token_symbol": base_token["attributes"].get("symbol", "?"),
                "token_address": base_token["attributes"]["address"],
                "reserve_usd": reserve,
                "volume_h24_usd": volume,
                "pool_created_at": attrs["pool_created_at"],
            })
    return candidates


def enrich_with_token_info(candidates: list[dict]) -> list[dict]:
    enriched = []
    for c in candidates:
        try:
            payload = get(
                f"/onchain/networks/{c['network_id']}/tokens/{c['token_address']}/info"
            )
            attrs = payload.get("data", {}).get("attributes", {}) or {}
        except Exception as e:
            print(f"  [skip] {c['token_symbol']} on {c['network_id']}: {e}")
            continue

        c["gt_score"] = attrs.get("gt_score")
        c["is_honeypot"] = attrs.get("is_honeypot")
        if c["network_id"] == "solana":
            c["mint_authority"] = attrs.get("mint_authority")
            c["freeze_authority"] = attrs.get("freeze_authority")
        else:
            c["mint_authority"] = None
            c["freeze_authority"] = None
        enriched.append(c)
    return enriched


def is_safe(row: dict) -> bool:
    """Soft safety check. Tighten thresholds for production use."""
    if row.get("is_honeypot") is True:
        return False
    score = row.get("gt_score") or 0
    if score < 30:  # very low GT Score = thin metadata, sparse trading history
        return False
    if row["network_id"] == "solana":
        # Solana: mint/freeze authority being non-null = token is still mintable/freezable.
        # Acceptable for many memecoins; flag for the reader to decide.
        pass
    return True


def main() -> None:
    print_mode_banner()
    print(f"\nFetching candidates (min liquidity ${MIN_LIQUIDITY_USD:,}, min h24 volume ${MIN_VOLUME_H24_USD:,})...\n")
    candidates = fetch_candidates(PAGES)
    print(f"  {len(candidates)} pools survived liquidity/volume filter")

    print("\nEnriching with token info (gt_score, honeypot, Solana authorities)...")
    enriched = enrich_with_token_info(candidates)
    print(f"  {len(enriched)} tokens enriched")

    enriched.sort(key=lambda r: (r.get("gt_score") or 0), reverse=True)
    safe = [r for r in enriched if is_safe(r)]

    print(f"\n{'Network':<14} {'Symbol':<10} {'GT':>4} {'Honey':>6} {'MintAuth':<10} {'FreezeAuth':<11} {'Reserve':>12}")
    print("-" * 95)
    for r in enriched[:20]:
        gt = r.get("gt_score")
        gt_str = f"{gt:>4.0f}" if isinstance(gt, (int, float)) else "  - "
        mint = "yes" if r.get("mint_authority") else "no"
        freeze = "yes" if r.get("freeze_authority") else "no"
        honey = "yes" if r.get("is_honeypot") is True else "no"
        print(f"{r['network_name'][:13]:<14} {r['token_symbol'][:9]:<10} {gt_str} "
              f"{honey:>6} {mint:<10} {freeze:<11} {r['reserve_usd']:>12,.0f}")

    print(f"\n{len(safe)}/{len(enriched)} tokens passed the soft safety check.")

    OUTPUT_DIR.joinpath("csv").mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.joinpath("json").mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = OUTPUT_DIR / "csv" / f"quality_filtered_{ts}.csv"
    json_path = OUTPUT_DIR / "json" / f"quality_filtered_{ts}.json"
    if enriched:
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(enriched[0].keys()))
            writer.writeheader()
            writer.writerows(enriched)
        json_path.write_text(json.dumps(enriched, indent=2))
        print(f"\nWrote {csv_path.name} / {json_path.name}")


if __name__ == "__main__":
    main()
