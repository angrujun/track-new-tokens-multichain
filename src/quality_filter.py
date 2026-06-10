"""Filter new tokens for quality.

Step 1: pull new pools and keep only ones above liquidity and volume thresholds.
Step 2: enrich each survivor with GT Score, honeypot status, and Solana authority fields.
Step 3: drop anything flagged as honeypot or scoring under 30.
"""
from cg_client import get, index_included

MIN_LIQUIDITY_USD = 5_000
MIN_VOLUME_24H_USD = 1_000


def fetch_candidates(pages=2):
    """Pull new pools and keep only ones above the liquidity and volume floors."""
    candidates = []
    for page in range(1, pages + 1):
        payload = get("/onchain/networks/new_pools", params={
            "include": "base_token,network",
            "page": page,
        })
        included = index_included(payload)
        for pool in payload["data"]:
            attrs = pool["attributes"]
            reserve = float(attrs.get("reserve_in_usd") or 0)
            volume = float(attrs.get("volume_usd", {}).get("h24") or 0)
            if reserve < MIN_LIQUIDITY_USD or volume < MIN_VOLUME_24H_USD:
                continue
            base_id = pool["relationships"]["base_token"]["data"]["id"]
            net_id = pool["relationships"]["network"]["data"]["id"]
            base = included[base_id]["attributes"]
            candidates.append({
                "network_id": net_id,
                "network": included[net_id]["attributes"]["name"],
                "symbol": base.get("symbol"),
                "address": base["address"],
                "reserve_usd": reserve,
                "volume_24h": volume,
            })
    return candidates


def enrich_with_token_info(candidates):
    """Attach GT Score, honeypot status, and (on Solana) authority fields to each candidate."""
    for c in candidates:
        info = get(f"/onchain/networks/{c['network_id']}/tokens/{c['address']}/info")
        attrs = info.get("data", {}).get("attributes", {}) or {}
        c["gt_score"] = attrs.get("gt_score")
        c["is_honeypot"] = attrs.get("is_honeypot")
        # On Solana, a non-null mint or freeze authority means the deployer can still
        # mint new tokens or freeze user balances. Treat as a major risk signal.
        if c["network_id"] == "solana":
            c["mint_authority"] = attrs.get("mint_authority")
            c["freeze_authority"] = attrs.get("freeze_authority")
    return candidates


def is_safe(row):
    """Reject honeypots and anything scoring below 30."""
    if row.get("is_honeypot") is True:
        return False
    return (row.get("gt_score") or 0) >= 30


if __name__ == "__main__":
    candidates = fetch_candidates()
    enriched = enrich_with_token_info(candidates)
    safe = [r for r in enriched if is_safe(r)]
    for row in sorted(safe, key=lambda r: r.get("gt_score") or 0, reverse=True):
        print(row)
