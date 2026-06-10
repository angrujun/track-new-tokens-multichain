# Schema Lock (Internal — strip before v2 publish)

Endpoint shapes and constraints verified against the official `coingecko` skill
on 2026-06-10. Use this as the source of truth while iterating on v1.

## Endpoints used

### `GET /onchain/networks` — Demo plan
- Returns paginated list of network IDs
- `data[].id` = network ID (used as `{network}` path param everywhere else)
- `data[].attributes.coingecko_asset_platform_id` = mapping to CoinGecko coin platform IDs

### `GET /onchain/networks/new_pools` — Demo plan
- Returns up to 20 newest pools across all networks per page
- Iterate `?page=2`, `?page=3`, ... for deeper history (past 48h)
- `include=base_token,quote_token,network` sideloads under top-level `included[]`

### `GET /onchain/networks/{network}/new_pools` — Demo plan
- Same shape as multi-chain but scoped to one network
- 20 pools per page, past 48h window

### `GET /onchain/networks/{network}/tokens/{address}/info` — Demo plan
- Token metadata: `gt_score` (0-100), `is_honeypot` (bool|str)
- Solana-specific: `mint_authority`, `freeze_authority` (string|null)
- `holders.distribution_percentage` (Beta, supported on Solana + major EVM + Sui/TON/Ronin)

### `GET /onchain/pools/megafilter` — Paid (Lite Plan and above)
- Single-call filtered discovery
- Critical params used: `pool_created_hour_max`, `reserve_in_usd_min`, `h24_volume_usd_min`, `checks`, `sort`
- `checks` values: `no_honeypot`, `good_gt_score`, `on_coingecko`, `has_social`

## Nullable field caveats

- `market_cap_usd` is frequently `null` for brand-new tokens. Use `fdv_usd` as fallback.
- `gt_score` can be `null` if too new — treat as 0 for ranking purposes.
- `is_honeypot` returns boolean OR string (e.g., "unknown") — code must handle both.
- Solana `mint_authority` / `freeze_authority` are only present on Solana network responses.

## Shape gotchas

- `included[]` lives at top level of payload, not nested in each `data` item.
- `data[].id` for pools follows `{network_id}_{pool_address}` format (with underscore).
- All numeric values come back as strings — cast to float before arithmetic.
- Max 20 pools per page across every pool-list endpoint.

## Plan tier disclosure rules (must appear in article)

- Megafilter → "CoinGecko API Lite Plan and above"
- WebSocket → "CoinGecko API Analyst Plan and above" (NOT just "paid plan")
- All other endpoints in this repo → "free Demo plan"

## Tested against

- Demo key: 30 calls/min limit, sufficient for prototyping
- Pro key: full access, used for Megafilter verification
