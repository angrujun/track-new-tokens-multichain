"""Smoke test — runs each endpoint once and reports PASS / FAIL.

Use this to verify your API key works before running the full pipeline.
Designed to consume minimal credits (single page per endpoint, single token info call).
"""
import sys
import traceback

from cg_client import get, MODE, print_mode_banner


def check(name: str, fn) -> bool:
    try:
        result = fn()
        ok = bool(result)
        print(f"  [{'PASS' if ok else 'EMPTY'}] {name}")
        return ok
    except Exception as e:
        print(f"  [FAIL] {name}  →  {type(e).__name__}: {e}")
        return False


def main() -> None:
    print_mode_banner()
    print("\nRunning smoke tests against the CoinGecko on-chain API...\n")

    passed = 0
    total = 0

    total += 1
    if check("GET /onchain/networks (list 250+ networks)",
             lambda: get("/onchain/networks")["data"]):
        passed += 1

    total += 1
    if check("GET /onchain/networks/new_pools (multi-chain)",
             lambda: get("/onchain/networks/new_pools", params={"page": 1})["data"]):
        passed += 1

    for net in ("solana", "base", "bsc"):
        total += 1
        if check(f"GET /onchain/networks/{net}/new_pools",
                 lambda n=net: get(f"/onchain/networks/{n}/new_pools", params={"page": 1})["data"]):
            passed += 1

    total += 1
    if check("GET /onchain/tokens/info_recently_updated",
             lambda: get("/onchain/tokens/info_recently_updated")["data"]):
        passed += 1

    # Megafilter: paid only — expect failure on Demo, success on Pro
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
    sys.exit(0 if passed >= total - 1 else 1)  # allow Megafilter skip on Demo


if __name__ == "__main__":
    main()
