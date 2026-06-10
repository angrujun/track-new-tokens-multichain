# How to Track New Tokens on Solana, Base, BSC, and 250+ Chains

Companion code repository for the CoinGecko Learn article: *How to Track New Tokens on Solana, Base, BSC, and 250+ Chains*.

This repo walks through how to use the CoinGecko API (the on-chain endpoints under `/onchain/`, powered by GeckoTerminal) to discover newly launched tokens across 250+ networks — Solana, Base, BSC, Ethereum, Arbitrum, Sui, TON, and more.

The core path runs on the **free Demo plan**. The Megafilter variant (`src/04_megafilter.py`) requires a paid plan.

## What you'll build

| Script | What it does | Plan tier |
|---|---|---|
| `src/01_multichain_new_pools.py` | Fetch new pools across all 250+ chains in one call | Demo |
| `src/02_perchain_new_pools.py` | Scope new pools to Solana, Base, BSC individually | Demo |
| `src/03_quality_filter.py` | Filter for liquidity, GT Score, honeypot status, Solana mint/freeze authority | Demo |
| `src/04_megafilter.py` | One-call filtered discovery with FDV, age, tax %, safety checks | Paid (Lite Plan+) |
| `src/05_telegram_pipeline.py` | End-to-end alert pipeline with deduplication | Demo |

## Quick start

```bash
git clone https://github.com/angrujun/track-new-tokens-multichain.git
cd track-new-tokens-multichain
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your CoinGecko API key
python src/01_multichain_new_pools.py
```

Get a free Demo API key at https://www.coingecko.com/en/api/pricing.

## Run any single script

```bash
python src/01_multichain_new_pools.py
python src/02_perchain_new_pools.py solana
python src/02_perchain_new_pools.py base
python src/02_perchain_new_pools.py bsc
python src/03_quality_filter.py
python src/04_megafilter.py            # requires paid key
python src/05_telegram_pipeline.py
```

Outputs land in `output/csv/` and `output/json/`.

## Run the smoke test

```bash
python src/smoke_test.py
```

The smoke test calls each script with a small sample and prints PASS/FAIL per endpoint. Use it to verify your key works before drafting any article.

## Environment variables

`.env` keys (see `.env.example`):

```env
# Required — your CoinGecko API key
COINGECKO_API_KEY=CG-xxxxxxxxxxxxx

# pro | demo  — pro uses pro-api.coingecko.com, demo uses api.coingecko.com
CG_API_MODE=demo

# Optional — only needed for src/05_telegram_pipeline.py
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## Endpoints used

All endpoints are on the GeckoTerminal on-chain namespace, accessed via the CoinGecko API:

- `GET /onchain/networks` — list 250+ networks
- `GET /onchain/networks/new_pools` — new pools across all chains (past 48h)
- `GET /onchain/networks/{network}/new_pools` — new pools on one chain
- `GET /onchain/networks/{network}/tokens/{address}/info` — token metadata, GT Score, honeypot, Solana authorities
- `GET /onchain/pools/megafilter` — paid filtered discovery

Full endpoint reference: https://docs.coingecko.com/reference/onchain-introduction

## Disclaimer

This guide is for educational purposes only and is not financial advice. Brand-new tokens carry significant risk; always cross-check with independent on-chain verification before making any trading or listing decisions.
