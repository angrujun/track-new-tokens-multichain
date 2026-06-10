"""Paid-plan alternative to quality_filter.py.

One call to /onchain/pools/megafilter returns pre-filtered new pools with FDV,
age, tax %, GT Score, and honeypot checks bundled server-side. Requires the
CoinGecko API Lite plan or above.
"""
from cg_client import get, index_included


def fetch_megafilter():
    """Return new pools across every chain, pre-filtered server-side."""
    payload = get("/onchain/pools/megafilter", params={
        "include": "base_token,network",
        "pool_created_hour_max": 48,       # past 48 hours only
        "reserve_in_usd_min": 5_000,       # liquidity floor
        "h24_volume_usd_min": 1_000,       # activity floor
        "checks": "no_honeypot,good_gt_score",
        "sort": "pool_created_at_desc",
    })
    included = index_included(payload)
    results = []
    for pool in payload["data"]:
        attrs = pool["attributes"]
        base_id = pool["relationships"]["base_token"]["data"]["id"]
        net_id = pool["relationships"]["network"]["data"]["id"]
        results.append({
            "network": included[net_id]["attributes"]["name"],
            "symbol": included[base_id]["attributes"].get("symbol"),
            "reserve_usd": float(attrs.get("reserve_in_usd") or 0),
            "volume_24h": float(attrs.get("volume_usd", {}).get("h24") or 0),
            "created_at": attrs["pool_created_at"],
        })
    return results


if __name__ == "__main__":
    for pool in fetch_megafilter():
        print(pool)
