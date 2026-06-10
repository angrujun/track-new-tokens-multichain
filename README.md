# How to Track New Tokens on Solana, Base, BSC, and 250+ Chains

Companion repository for the [CoinGecko Learn](https://www.coingecko.com/learn) tutorial *How to Track New Tokens on Solana, Base, BSC, and 250+ Chains*.

A small Python toolkit that uses the [CoinGecko API](https://www.coingecko.com/en/api) (specifically the on-chain endpoints under `/onchain/`, powered by GeckoTerminal) to discover newly launched tokens across **250+ blockchains** — Solana, Base, BSC, Ethereum, Arbitrum, Sui, TON, and more — from a single API.

## What's in the box

| Script | What it does | Plan |
|---|---|---|
| `src/01_multichain_new_pools.py` | New pools across all chains in one call | Free Demo |
| `src/02_perchain_new_pools.py` | New pools scoped to one chain (Solana, Base, BSC, etc.) | Free Demo |
| `src/03_quality_filter.py` | Filter for liquidity, GT Score, honeypot, Solana mint/freeze authority | Free Demo |
| `src/04_megafilter.py` | One-call filtered discovery with rich filters | Paid (Lite+) |
| `src/05_telegram_pipeline.py` | Alert pipeline with deduplication, Telegram-ready | Free Demo |
| `src/smoke_test.py` | Verify your key + endpoint access before drafting | Any plan |

The core build runs on the free [Demo plan](https://www.coingecko.com/en/api/pricing). The Megafilter script is the natural upgrade once you outgrow manual filtering.

## Quick start

```bash
git clone https://github.com/angrujun/track-new-tokens-multichain.git
cd track-new-tokens-multichain
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Open .env and paste your CoinGecko API key
python src/smoke_test.py
python src/01_multichain_new_pools.py
```

Get a free Demo API key at [coingecko.com/en/api/pricing](https://www.coingecko.com/en/api/pricing).

## Running individual scripts

```bash
python src/01_multichain_new_pools.py
python src/02_perchain_new_pools.py solana
python src/02_perchain_new_pools.py base
python src/02_perchain_new_pools.py bsc
python src/03_quality_filter.py
python src/04_megafilter.py            # requires a paid key — set CG_API_MODE=pro
python src/05_telegram_pipeline.py
```

CSV and JSON snapshots land in `output/csv/` and `output/json/`.

## Configuration

`.env` (see `.env.example` for the full template):

```env
COINGECKO_API_KEY=CG-xxxxxxxxxxxxx
CG_API_MODE=demo        # demo | pro

TELEGRAM_BOT_TOKEN=     # optional — used by 05_telegram_pipeline.py
TELEGRAM_CHAT_ID=
```

`CG_API_MODE=demo` uses `https://api.coingecko.com/api/v3` with the Demo header. `CG_API_MODE=pro` switches to `https://pro-api.coingecko.com/api/v3`.

## Endpoints used

All on the CoinGecko on-chain namespace (powered by GeckoTerminal):

- `GET /onchain/networks` — list 250+ supported networks
- `GET /onchain/networks/new_pools` — newest pools across all chains (past 48h)
- `GET /onchain/networks/{network}/new_pools` — newest pools on one chain
- `GET /onchain/networks/{network}/tokens/{address}/info` — token metadata, GT Score, honeypot status, Solana mint/freeze authority
- `GET /onchain/pools/megafilter` — paid one-call filter with FDV, age, tax %, and safety knobs

Full endpoint reference: [docs.coingecko.com/reference/onchain-introduction](https://docs.coingecko.com/reference/onchain-introduction)

## Disclaimer

This guide is for educational purposes only and is not financial advice. Brand-new tokens carry significant risk; cross-check with independent on-chain verification before any trading or listing decision.
