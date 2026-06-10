"""Fetch newest pools scoped to a single chain.

Usage: python fetch_chain_pools.py solana  (or base, bsc, eth, etc.)
"""
import sys
from cg_client import get, index_included


def fetch_chain_pools(network, pages=1):
    """Return the newest pools created on a single network."""
    results = []
    for page in range(1, pages + 1):
        payload = get(f"/onchain/networks/{network}/new_pools", params={
            "include": "base_token",
            "page": page,
        })
        included = index_included(payload)
        for pool in payload["data"]:
            attrs = pool["attributes"]
            base_id = pool["relationships"]["base_token"]["data"]["id"]
            base = included[base_id]["attributes"]
            results.append({
                "network_id": network,
                "symbol": base.get("symbol"),
                "address": base["address"],
                "reserve_usd": float(attrs.get("reserve_in_usd") or 0),
                "volume_24h": float(attrs.get("volume_usd", {}).get("h24") or 0),
            })
    return results


if __name__ == "__main__":
    network = sys.argv[1] if len(sys.argv) > 1 else "solana"
    for pool in fetch_chain_pools(network)[:10]:
        print(pool)
