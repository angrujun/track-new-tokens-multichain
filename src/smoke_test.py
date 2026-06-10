"""Smoke test. Runs each on-chain endpoint once and reports PASS / FAIL.

Run this before drafting an article or building a pipeline to confirm your key
works against every endpoint used in the rest of this repo.
"""
import sys
from cg_client import get, MODE


def check(name, fn):
    try:
        result = fn()
        ok = bool(result)
        print(f"  [{'PASS' if ok else 'EMPTY'}] {name}")
        return ok
    except Exception as e:
        print(f"  [FAIL] {name}  →  {type(e).__name__}: {e}")
        return False


def main():
    print(f"CoinGecko API mode: {MODE.upper()}\n")
    print("Running smoke tests...\n")

    passed = 0
    total = 0

    checks = [
        ("GET /onchain/networks",                           lambda: get("/onchain/networks")["data"]),
        ("GET /onchain/networks/new_pools (multi-chain)",   lambda: get("/onchain/networks/new_pools", params={"page": 1})["data"]),
        ("GET /onchain/networks/solana/new_pools",          lambda: get("/onchain/networks/solana/new_pools", params={"page": 1})["data"]),
        ("GET /onchain/networks/base/new_pools",            lambda: get("/onchain/networks/base/new_pools", params={"page": 1})["data"]),
        ("GET /onchain/networks/bsc/new_pools",             lambda: get("/onchain/networks/bsc/new_pools", params={"page": 1})["data"]),
        ("GET /onchain/tokens/info_recently_updated",       lambda: get("/onchain/tokens/info_recently_updated")["data"]),
    ]
    for name, fn in checks:
        total += 1
        if check(name, fn):
            passed += 1

    # Megafilter is paid-only. Expect a SKIP on Demo.
    total += 1
    try:
        get("/onchain/pools/megafilter", params={"pool_created_hour_max": 48})
        print(f"  [PASS] GET /onchain/pools/megafilter (paid)")
        passed += 1
    except Exception as e:
        if MODE == "demo":
            print(f"  [SKIP] GET /onchain/pools/megafilter  →  Demo plan does not have access (expected)")
        else:
            print(f"  [FAIL] GET /onchain/pools/megafilter  →  {e}")

    print(f"\n{passed}/{total} checks passed.")
    sys.exit(0 if passed >= total - 1 else 1)


if __name__ == "__main__":
    main()
