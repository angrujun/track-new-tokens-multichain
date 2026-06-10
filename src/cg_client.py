"""Shared CoinGecko on-chain client.

Resolves base URL + auth header from CG_API_MODE (pro | demo), provides
a thin GET wrapper with timeout + simple retry, and a helper to resolve
sideloaded `included` entries by id.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

API_KEY = os.getenv("COINGECKO_API_KEY", "").strip()
MODE = os.getenv("CG_API_MODE", "demo").strip().lower()

if MODE == "pro":
    BASE_URL = "https://pro-api.coingecko.com/api/v3"
    AUTH_HEADER = "x-cg-pro-api-key"
elif MODE == "demo":
    BASE_URL = "https://api.coingecko.com/api/v3"
    AUTH_HEADER = "x-cg-demo-api-key"
else:
    raise SystemExit(f"CG_API_MODE must be 'pro' or 'demo', got: {MODE!r}")

HEADERS = {"accept": "application/json"}
if API_KEY:
    HEADERS[AUTH_HEADER] = API_KEY


def get(path: str, params: dict | None = None, retries: int = 2, timeout: int = 20) -> dict:
    """GET against the CoinGecko on-chain API. `path` should start with /onchain/..."""
    url = f"{BASE_URL}{path}"
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
            if r.status_code == 429:
                wait = 2 ** attempt
                print(f"  [rate limit] sleeping {wait}s...")
                time.sleep(wait)
                last_err = RuntimeError(f"rate limited after {attempt + 1} attempts")
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            last_err = e
            if attempt < retries:
                time.sleep(1 + attempt)
                continue
            raise
    raise last_err if last_err else RuntimeError(f"unknown failure on {url}")


def index_included(payload: dict) -> dict:
    """Build an id → attributes lookup from the `included` array."""
    return {item["id"]: item for item in payload.get("included", [])}


def resolve_relationship(pool: dict, rel: str, index: dict) -> dict | None:
    """Return the included item referenced by pool.relationships[rel]."""
    ref = pool.get("relationships", {}).get(rel, {}).get("data")
    if not ref:
        return None
    return index.get(ref["id"])


def print_mode_banner() -> None:
    """Print a small startup banner so the reader sees which key is active."""
    key_preview = (API_KEY[:6] + "..." + API_KEY[-4:]) if API_KEY else "(none)"
    print(f"CoinGecko API mode: {MODE.upper()}  |  key: {key_preview}  |  base: {BASE_URL}")
