# providers.yaml — Field Schema

Every provider entry uses these fields. Keep entries factual and verifiable.
Unverifiable claims must be marked with `(claimed)` or `status: unverified`.

| Field | Required | Description |
|---|---|---|
| `name` | yes | Display name. Include the Chinese name in parentheses if it has one. |
| `url` | yes | Official homepage. HTTPS only. |
| `type` | yes | One of: `official-relay`, `mixed`, `reverse`, `aggregator`, `gateway-oss`, `observability`, `comparison`, `list`. |
| `status` | yes | `active` (independently reachable), `unverified` (community-sourced, not confirmed), `inactive` (dead / ran away). |
| `payment` | no | Array: `alipay`, `wechat`, `card`, `crypto`, `enterprise-invoice`. |
| `models` | no | Array of upstream families: `openai`, `anthropic`, `gemini`, `deepseek`, etc. |
| `model_count` | no | Integer. Provider's claimed number of models. |
| `provider_count` | no | Integer. Number of upstream vendors. |
| `discount_vs_official` | no | String. e.g. `"~49% cheaper (claimed)"`. |
| `last_verified` | no | `YYYY-MM-DD` the maintainer last visited the site or ran a canary. Use `null` when not independently confirmed. |
| `verified_by` | no | `maintainer`, `community`, or `third-party-report`. Identifies who supplied `last_verified`. |
| `entity_registered` | no | `true`, `false`, or `unknown`. Is a registered company / ICP filing publicly visible. |
| `supports_stream` | no | `true`, `false`, or `unknown`. SSE / streaming responses available. |
| `supports_tools` | no | `true`, `false`, or `unknown`. Function-calling / tools API compatibility. |
| `notes` | no | One factual sentence, no marketing. **May be a string OR a dict `{en, zh-TW, zh-CN}` for bilingual entries.** Missing translations fall back to `en`. Required key when dict: `en`. |
| `risk_flags` | no | Array. Visible safety concerns surfaced as ⚠ in the README Trust column. See enum below. |
| `pricing` | no | Block. See below — present when this provider has an automated fetcher. |

## `risk_flags` enum (schema v5)

Each flag rendered as `⚠ <short-label>` in the Trust column of provider tables.
Multiple flags concatenated. Keep this list short on purpose — only signals a
user needs to see before sending money.

| Flag | Meaning | Visible label (en) |
|---|---|---|
| `operator_submitted` | The entry was self-submitted by the relay's operator (transparency disclosure, not auto-disqualifying) | `operator-self` |
| `no_entity` | No publicly visible company / ICP filing / TOS / contact | `no-entity` |
| `reverse_channel` | Uses a reverse-engineered vendor web client (high ToS risk, may silently downgrade) | `reverse` |
| `prices_too_cheap` | Prices >50% below OpenRouter without maintainer canary (usually means reverse / mixed) | `cheap-trap` |
| `ran_away` | Exit-scammed: operator took prepaid balances and disappeared. Use with `status: inactive` | `ran-away` |

Status emoji rendered as a prefix to each Station/Service cell:

- 🟢 `active` + `verified_by: maintainer` — independently canary-tested
- 🟡 `active` + non-maintainer verification, OR `unverified` — community-listed, not maintainer-confirmed
- 🔴 `inactive` — dead / ran away (kept as history)

## `pricing` block (optional, schema v3)

Add to a provider entry when its prices can be fetched automatically by
`scripts/scrape.py`. Snapshots land in `data/snapshots/<YYYY-MM-DD>/<fetcher>.json`
weekly via the `price-refresh` workflow.

| Field | Required | Description |
|---|---|---|
| `pricing_url` | yes | The human-readable pricing page (what users see). |
| `api_url` | no | The JSON endpoint the fetcher calls. Omit when fetcher uses HTML/DOM. |
| `fetcher` | conditionally | Fetcher ID — must match `fetchers/<id>.py`'s `PROVIDER_ID`. Required unless `submitted_prices` is the only price source. |
| `pricing_currency` | yes | ISO 4217. We normalize to `USD` in `data/prices.latest.json`. |
| `last_priced` | no | `YYYY-MM-DD` of the most recent successful scrape. Written by `scripts/build_prices.py`. |
| `submitted_prices` | no | List of community-submitted price records, manually verified by the maintainer. See below. |

## `submitted_prices` (schema v4)

For providers without a public JSON pricing API (e.g. Yunwu, CloseAI) the relay
operator or community members can submit prices via the
[`submit-prices` issue form](../.github/ISSUE_TEMPLATE/submit-prices.yml).
Howard reviews these weekly via `python -m scripts.review_submissions` and on
accept appends entries here.

```yaml
pricing:
  pricing_url: https://example.com/pricing
  submitted_prices:
    - canonical_model: claude-sonnet-4.6
      unit: per_1m_input_tokens
      price_usd: 1.50
      source_url: https://example.com/pricing
      screenshot_url: https://github.com/howardpen9/awesome-ai-api-proxy/issues/42#issuecomment-123
      captured_at: "2026-06-07"
      submitted_by: "@operator-handle"
      submitted_by_role: operator      # operator | community
      verified_at: "2026-06-08"
      verified_by: maintainer
```

`fetcher` and `submitted_prices` can coexist on the same provider — the
auto-scraper covers what it can, manual submissions fill gaps. Build step
merges both into `data/prices.latest.json` but tags them differently
(`method: json-api` vs `method: manual`, `confidence: high` vs `medium`).

## `type` definitions

- **official-relay** — Forwards requests using official vendor keys. Most trustworthy; output matches the real model.
- **mixed** — Blends official keys with other channels (e.g. Azure, partner quotas).
- **reverse** — Reverse-engineered from a vendor's web client. Cheapest, least stable, highest ToS risk.
- **aggregator** — Routes across multiple upstream relays/providers behind one key.
- **gateway-oss** — Self-hostable open-source gateway (you bring your own keys).
- **observability** — Gateway focused on logging, analytics, cost tracking.
- **comparison** — A tool that compares stations, not a station itself.
- **list** — A directory/awesome-list resource.

## Trust ordering (rough)

```
official-relay  >  mixed  >  aggregator  >  reverse
```

`gateway-oss` is orthogonal: you hold the keys, so trust depends on you, not the operator.

## Editorial rules

1. No referral links. Plain **HTTPS** URLs only — no `utm_*`, `ref=`, `campaignid`, `gclid`, etc. Enforced by `scripts/validate.py`.
2. No marketing / superlative phrasing in `notes` (`#1`, `the best …`, 强烈推荐, 不降智, …). One factual sentence per language, ≤ 360 characters.
3. `status: active` requires `verified_by: maintainer` and a `last_verified` date. Community / operator submissions use `status: unverified`.
4. `risk_flags: [operator_submitted]` implies `status: unverified` (never `active`).
5. Do not hand-edit README provider tables — they are generated from this file. CI rejects hand-edits of those marker blocks.
6. A station that has run away (`跑路`) → set `status: inactive`, keep the entry, add a dated note. We do not delete history.
7. **Two pricing schemas coexist (schema v3+):**
   - Providers with `pricing.fetcher` → objective, dated, snapshot-backed absolute prices live in `data/snapshots/` + `data/prices.latest.json`. The README's price table is generated from these. No `(claimed)` tag.
   - Providers without `pricing.fetcher` → continue using `discount_vs_official: "... (claimed)"` for narrative context. Prices decay fast so they remain marked `(claimed)`.
8. Every record in `data/prices.latest.json` carries `source_url` + `captured_at` + `method`. This is the citation envelope LLM agents quote — don't drop those fields when adding a fetcher.
