# China/SEA relay prices vs OTPI per MTok: regional price discovery

> **Read this first.**
> - **Regional price discovery only.** This describes publicly posted prices. It is not a resale offer, a recommendation, or an endorsement of any relay.
> - **The lab-level "relay-implied index" is an estimate, not an observed price.** It is OTPI × the median relay/OpenRouter price ratio for that lab's models.
> - **Small sample:** 5 relays in total, 1–3 relays per model.
> - **Group discounts are not applied.** Relay prices use the default/listed group ratio, so some may overstate what users actually pay.
> - **Top-up FX adjustment covers only the Alipay/WeChat path** (new-api `/api/status.price`, CNY per 1 USD of quota). Card/Stripe rates and bonus tiers are ignored.
> - **No canary verification.** Nothing was test-called; we did not confirm that any relay serves the model it names.

**What this is.** This is a regional price discovery exercise. It asks what per-token prices are posted by API relay operators (中轉站) that serve mainland-China and Southeast-Asia developers, mostly through Alipay or WeChat top-ups. It then compares those prices with Ornn's Token Price Index (OTPI) and with OpenRouter's posted per-model prices. It describes observed public prices. It does not endorse, recommend, or evaluate any relay, it says nothing about resale, and it does not verify that a relay actually serves the model it names.

**Sources and timestamps.**
- **OTPI:** `GET https://api.ornnai.com/api/otpi` on the free, no-key tier (`access: public-3mo`). Fetched 2026-10-23T10:27:17Z (18:27 UTC+8). Settlement date 2026-10-21, computed 2026-10-22T12:01Z. Only `anthropic`, `openai`, `google` and `deepseek` are public. `minimax`, `qwen`, `moonshotai`, `z-ai`, `xiaomi`, `mistralai` and `meta-llama` returned HTTP 401 ("requires an API key"). `/api/model-frontier`, which has per-model `pIn`/`pOut`, and `/api/workload` also returned 401.
- **Relay prices and the OpenRouter reference:** `data/prices.latest.json` from `howardpen9/awesome-ai-api-proxy` main at commit 50bfda9, snapshot 2026-10-22, generated 2026-10-22T08:57Z.
- **Top-up rates and group ratios:** each relay's public new-api `/api/status` and `/api/pricing`, fetched 2026-10-23 at about 10:28Z.
- **FX:** USD/CNY 6.6882 from open.er-api.com (last updated 2026-10-23T00:02Z).

All raw responses are in `raw/`, each with its fetch time.

**Matching rules.** OTPI is a lab-level, volume-weighted blended USD/MTok. The free tier does not split it into input and output, and it gives no per-model values. That is why `otpi_in` and `otpi_out` are empty. Per-model rows compare relay prices against OpenRouter's posted price for the same model (`spread_in_pct` / `spread_out_pct`).

Models are matched only by exact, case-insensitive name after removing the vendor prefix. For example, `anthropic/claude-opus-5` matches `claude-opus-5`. Variants such as `-thinking` or dated snapshots are not merged. Only `per_1m_input_tokens` and `per_1m_output_tokens` are used. Per-request, per-image, per-second and cache-read units are excluded.

The relay set is uiuiapi, relaydance, teamorouter, wappkit and unorouter. bltcy is excluded because its own `/api/status` announcement (2026-04-24) says top-ups stopped and the API was shut down on 2026-05-01, but its pricing endpoint still answers. QuickSilver Pro and Atlas Cloud are excluded as card-only global aggregators. Prices of exactly $75/M input from new-api relays are excluded as the placeholder `model_ratio` 37.5, which is the default for unpriced models.

The lab-level "relay-implied index" is OTPI × the median of (relay median ÷ reference) across that lab's matched models, with input and output pooled. It assumes the relay discount applies evenly to OTPI's token mix. It is a derived figure, not an observed price.

**Caveats.**
1. **Small samples.** Coverage is thin: n = 1–3 relays per model, and a median of 2 is just the midpoint.
2. **Group discounts.** new-api relays price by `model_ratio × $2 × group_ratio`. The snapshot uses the `default` group (uiuiapi, relaydance), a fixed pool group (wappkit `Codex-Pro(救急)`, 0.3×, an account-pool channel), or 1.0 (unorouter). UnoRouter's live `/api/pricing` lists per-model channel groups at 0.009–0.98× for most matched models, so its recorded prices are probably list prices that overstate what users pay. Those rows are flagged.
3. **Currency.** Many relays label quota in USD but sell it in CNY. The "top-up adjusted" view multiplies listed prices by `/api/status.price` (CNY per 1 USD of quota) ÷ FX. That is 3.37/6.69 ≈ 0.50 for uiuiapi and 6.8/6.69 ≈ 1.02 for relaydance and wappkit. UnoRouter (card, USD display) and TeamoRouter (no status endpoint) are left at 1.0. Card (Stripe) top-up rates differ, and bonus tiers are ignored.
4. **No verification of quality.** Low prices can reflect pooled consumer subscriptions, reverse-engineered channels, or substituted models. Nothing here was canary-tested. TeamoRouter, Wappkit and UnoRouter are operator-submitted and unverified.

Files: `otpi_vs_relays.csv/.json` (per model, with per-relay detail and caveat flags in the JSON), `otpi_lab_level.csv`, `chart.png/.svg`, `x-preview.png` (16:9 lab-level summary), and `build.py` + `chart.py` + `x_preview.py` to reproduce (see `README.md`).
