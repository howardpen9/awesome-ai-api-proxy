# How a published price is computed

`price_usd` in [`data/prices.latest.json`](../data/prices.latest.json) is **quota USD**: what the relay's pricing endpoint bills for the chosen public group, in the relay's own dollar-of-quota unit. It is not always the cash a buyer wires. Two extra adjustments are recorded beside it, and one class of row is left out of the published build.

Historical snapshot files under `data/snapshots/` keep every row the fetcher returned, including placeholders. `scripts/build_prices.py` is what drops placeholders and inactive providers from the current tables.

## new-api group ratio

Legacy per-token prices on a new-api / one-api fork are:

```
input  USD / 1M = model_ratio × $2 × group_ratio
output USD / 1M = model_ratio × completion_ratio × $2 × group_ratio
```

`$2` is the fork's base (`NEW_API_BASE_USD_PER_1M`). `list_price_usd` is that product **before** `group_ratio`. `price_usd` includes it.

Which ratio, per model (`choose_pricing_group`):

1. An explicit group on the fetcher (UiUiAPI, Relaydance, Wappkit's `Codex-Pro(救急)`), if the model enables it. Models outside that group are skipped.
2. Otherwise the model's only enabled group (BetterToken's per-vendor groups).
3. Otherwise a group named exactly `default`, when this model enables it. Vip / SVIP ratios are not substituted for default. On UiUiAPI those groups cost *more* than default (quality tiers, not a discount).
4. Otherwise the **cheapest positive** enabled ratio. Ratio `0` is a free pool, not the paid price. The group name is stored in `pricing_group`. When another enabled group is more expensive, `group_ratio_max` is set too.

UnoRouter has no flat `default` key. Passing `group=None` used to force ratio `1`, so the published number was the list price. A channel at `0.447` is now `price_usd = list × 0.447`. The whole `group_ratio` object from the endpoint is stored once on that day's snapshot, not copied onto every row.

A ratio of `1` is written when that is the ratio the endpoint published for the chosen group. It is not a stand-in for "we did not look".

## Billing expressions vs the $75 placeholder

new-api's unset legacy ratio is **37.5**, which is **$75 / 1M** at group ratio 1. Relays leave that default on models they have not priced in the legacy fields. Some of those models carry a `billing_expr` that is the price the gateway actually bills, in USD per 1M:

```
len <= 271999 ? tier("≤ 271999", p * 2.5 + c * 15 + cr * 0.25) : tier("> 271999", p * 5 + c * 22.5 + cr * 0.5)
```

`p` is input, `c` is output, `cr` is cache-read, `fixed(n)` is a per-call price. The fetcher reads the **first** `tier(...)` only (the short-context branch) and multiplies by the group ratio. The full expression is kept on `billing_expr`, and the tier label on `price_tier`. Long-context prices stay in that string; they are not a second table row, because the README matrix keeps one cell per model.

UiUiAPI `gpt-5.4` is this case: legacy ratio 37.5 would publish **$75**, and the expression's short-context input is **$2.50** before top-up.

A row is `price_placeholder: true` when the legacy ratio is 37.5 **and** no billing expression could be parsed. The build drops those rows from `prices.latest.json`, the README ladder, the charts, and `docs/prices.md`. They remain in the raw snapshot. A real model whose configured legacy price is exactly $75/1M with no expression would be dropped too; that collision is the new-api default, and the cluster on UiUiAPI is hundreds of models wide.

## Top-up rate → effective USD

Quota USD is not cash when the relay sells $1 of quota for some other amount. The optional `pricing.topup_rate` block in [`providers.yaml`](../data/providers.yaml) is copied from that relay's public `/api/status`:

| YAML field | Status field | Meaning |
|---|---|---|
| `amount` | `price` | Local currency charged for $1 of quota |
| `fx_per_usd` | `usd_exchange_rate` | How many of those currency units the site calls $1 |
| `currency` | — | ISO code. `CNY` only where the relay takes CNY payment and the FX figure is a CNY-per-USD quote. The status symbol is often the unset `¤`, so the code is not read off a `¥` glyph. |
| `source_url`, `checked` | — | Where it was read, and the date. Required. |

```
effective_price_usd = price_usd × amount / fx_per_usd
```

Rounded to 6 decimal places. If `fx_per_usd` is missing or not positive, `effective_price_usd` is left off the row. No market FX rate is filled in. Providers without a block (OpenRouter, Atlas Cloud, QuickSilver Pro, TeamoRouter, and anyone not re-checked) have no effective column.

Checked 2026-10-24 from each site's `/api/status`:

| Provider | amount | fx_per_usd | multiplier |
|---|---|---|---|
| UiUiAPI | 3.37 CNY | 6.79 | 0.496 |
| Relaydance | 6.8 CNY | 6.8 | 1 |
| Wappkit | 6.8 CNY | 6.8 | 1 |
| UnoRouter | 1 USD | 1 | 1 |
| BetterToken | 1 USD | 1 | 1 |

UiUiAPI `gpt-5.4` short-context input is $2.50 quota USD in the default group, and about **$1.24 effective USD** after the 3.37/6.79 top-up. The README ladder stays in quota USD so a relay with no checked rate is not ranked against one that has one. The effective figure is `effective_price_usd` on the JSON row and the Effective column in [`prices.md`](prices.md).

`find_cheapest` compares `price_usd` for the same reason.

## Inactive providers

`scripts/scrape.py` does not fetch a provider with `status: inactive`. `build_prices.py` also drops that fetcher's rows from the current JSON and tables, so a snapshot taken before the status change does not keep showing a dead station as a price you can buy. Snapshot files already on disk stay, as history.

bltcy's own shutdown notice and the `status: inactive` edit are [PR #157](https://github.com/howardpen9/awesome-ai-api-proxy/pull/157). This repo's scrape skip and the build filter are the general mechanism. Until that status change is on `main`, a full scrape still includes bltcy, because it is still `active` here.
