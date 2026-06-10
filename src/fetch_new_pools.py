"""Fetch newest pools across every chain in one call."""
from cg_client import get, index_included


def fetch_new_pools(pages=2):
    """Return a list of newest pools across all 250+ chains."""
    results = []
    for page in range(1, pages + 1):
        # `include` sideloads the base token and network so we get all info in one call
        payload = get("/onchain/networks/new_pools", params={
            "include": "base_token,network",
            "page": page,
        })
        included = index_included(payload)
        for pool in payload["data"]:
            attrs = pool["attributes"]
            base_id = pool["relationships"]["base_token"]["data"]["id"]
            net_id = pool["relationships"]["network"]["data"]["id"]
            base = included[base_id]["attributes"]
            results.append({
                "network": included[net_id]["attributes"]["name"],
                "network_id": net_id,
                "symbol": base.get("symbol"),
                "address": base["address"],
                "reserve_usd": float(attrs.get("reserve_in_usd") or 0),
                "volume_24h": float(attrs.get("volume_usd", {}).get("h24") or 0),
            })
    return results


if __name__ == "__main__":
    for pool in fetch_new_pools()[:10]:
        print(f"{pool['network']:<14} {pool['symbol']:<10} "
              f"reserve ${pool['reserve_usd']:>10,.0f}  "
              f"24h vol ${pool['volume_24h']:>10,.0f}")
