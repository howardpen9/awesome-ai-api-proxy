# Awesome AI API Proxy [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> A curated, **actively maintained** list of AI API relay / proxy stations
> ("中轉站"), global LLM gateways, and the tools to evaluate them — with an
> evidence-based look at why this market exists and where it's risky.

**Languages:** English · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md)

Last reviewed: **2026-05-16** · Maintained by [@howardpen9](https://github.com/howardpen9) ·
Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Contents

- [What is an AI API relay?](#what-is-an-ai-api-relay)
- [Why this exists (globally)](#why-this-exists-globally)
- [China / Asia relay stations](#china--asia-relay-stations)
- [Global gateways & aggregators](#global-gateways--aggregators)
- [Comparison & monitoring tools](#comparison--monitoring-tools)
- [How to choose one safely](#how-to-choose-one-safely)
- [Risks (read this)](#risks-read-this)
- [Market context](#market-context)
- [Contributing](#contributing)

---

## What is an AI API relay?

An **AI API relay** (Chinese: *API 中轉站*; also "AI API proxy" / "relay
station") is a middleman endpoint. Instead of calling OpenAI, Anthropic,
Google, etc. directly, you point your `base_url` at the relay and use its key.
The relay forwards the request upstream and returns the result — usually with
**full OpenAI API compatibility**, so existing code needs almost no changes.

One key → dozens to hundreds of models across vendors.

This differs from a **mirror site** (镜像站), which is a proxied *chat web UI*
for end users. A relay is for **developers and applications**.

## Why this exists (globally)

Relays are not a China-only phenomenon. They are the product of two
constraints — **access blocking** and **payment friction** — wherever those
appear:

| Region | Access barrier | Payment barrier |
|---|---|---|
| China | Cross-border latency; some APIs blocked | Needs foreign card; relays take Alipay/WeChat |
| Russia / Belarus / Iran | OpenAI hard-blocks (even VPN detected) | Sanctioned cards (e.g. Iran Shetab) rejected |
| APAC incl. Taiwan | Generally reachable | Card rejection, quota limits, billing friction |
| Sanctioned / restricted markets | Account denial | No accepted payment rail |

The same need produces different ecosystems: Russia leans on IP proxies and
state alternatives (e.g. GigaChat); China evolved a full **relay retail
industry**. The global, "clean" version of this is the authorized aggregator
(see OpenRouter below) — proof that *unified LLM access* is a real, growing
market, not a workaround niche.

## China / Asia relay stations

> Status: `active` = independently reachable · `unverified` = community-sourced,
> not independently confirmed. Prices change constantly — verify on-site.
> Generated from [`data/providers.yaml`](data/providers.yaml).

| Station | Type | Payment | Status | Notes |
|---|---|---|---|---|
| [云雾 API (YUNWU)](https://yunwu.ai) | mixed | Alipay/WeChat | active | Marketed on speed/stability; widely cited top-tier station. |
| [柏拉图 AI (bltcy)](https://api.bltcy.ai) | mixed | Alipay/WeChat | active | Azure-backed channel; positions as lowest-price. |
| [No.1-API](https://api.rcouyi.com) | aggregator | Alipay/WeChat | active | One-stop aggregation + relay platform. |
| [UiUiAPI](https://uiuiapi.com) | official-relay | Alipay/WeChat | active | Claims official channels + official multipliers; ~49% cheaper (claimed), 300+ models. |
| [DMXAPI](https://dmxapi.cn) | mixed | Alipay/WeChat | unverified | Community-listed; homepage not independently verified. |
| [MKEAI](https://mkeai.com) | mixed | Alipay/WeChat | unverified | Community-forum + relay hybrid; pushes DeepSeek. |
| [GPTGOD](https://gptgod.online) | reverse | Alipay | unverified | Reverse-engineered; cheap, stability not guaranteed. |
| [CloseAI](https://www.closeai-asia.com) | official-relay | Alipay/WeChat/Invoice | active | Self-describes as largest enterprise-grade relay in Asia. |

> **Inclusion ≠ endorsement.** Listing documents the market. Always run the
> [evaluation checklist](docs/evaluation.md) before sending money or data.

## Global gateways & aggregators

| Service | Type | Payment | Notes |
|---|---|---|---|
| [OpenRouter](https://openrouter.ai) | aggregator | Card/Crypto | Official-authorized routing, ~5% markup; 400+ models, 60+ providers. ARR reportedly ~$5M (2025-05) → ~$50M (early 2026). |
| [LiteLLM](https://litellm.ai) | gateway-oss | — | Open-source gateway (100+ providers) + enterprise tier. Self-hosted, bring your own keys. |
| [Helicone](https://helicone.ai) | observability | — | LLM observability gateway; logging/cost analytics. |
| [AIMLAPI](https://aimlapi.com) | aggregator | Card/Crypto | 400+ models, prepaid from $20; crypto support implies payment-friction workaround. |

## Comparison & monitoring tools

| Tool | Notes |
|---|---|
| [中轉站競技場 (AI API PK)](https://www.aiapipk.com) | Price wall across OpenAI / Reverse / Claude / DeepSeek for ~40 stations. |
| [awesome-ai-proxy (mn-api)](https://github.com/mn-api/awesome-ai-proxy) | The original list (~31 stations). **Unmaintained as of 2026** — this repo aims to continue the effort. |

## How to choose one safely

See **[docs/evaluation.md](docs/evaluation.md)** for the full framework. Short version:

1. **Identify the channel type** — `official-relay` > `mixed` > `aggregator` > `reverse`.
2. **Run a canary test** — known-hard prompts, official vs relay, weekly. Detects silent model downgrade ("降智").
3. **Top up small** — relays are prepaid; never prepay large balances.
4. **Match workload** — sensitive/regulated data → official API or self-hosted `gateway-oss`, never `reverse`.

## Risks (read this)

The market is largely unregulated. From public research:

- A study of **28 relays** found **45.83% of endpoints served a model that
  didn't match the one requested** (up to 47% performance gap on medical tasks).
- An audit of **428 stations** found **9 injecting malicious code** and **1
  stealing funds outright**.
- Of 17 top stations surveyed, **15 had no registered company**.

Full breakdown with sources and mitigations: **[docs/risks.md](docs/risks.md)**.

## Market context

- The original community list ([mn-api/awesome-ai-proxy](https://github.com/mn-api/awesome-ai-proxy))
  catalogued ~31 stations before going stale; aggregators like aiapipk.com
  track ~40 — and these are the visible tip only.
- The "clean" global analogue, OpenRouter, reportedly grew ARR ~10x in under a
  year (≈$5M → ≈$50M), routing trillions of tokens monthly — strong evidence
  that *unified, multi-vendor LLM access* is a durable market, not a hack.
- Conclusion: relay stations are a **global response to blocking + payment
  friction**. China's ecosystem is the deepest because both pains peak there.

## Contributing

This list is **actively maintained** and community-driven. Add or correct a
station, flag one that ran away, or contribute a documented risk case:

- Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [field schema](data/schema.md).
- Edit [`data/providers.yaml`](data/providers.yaml) — not the README tables directly.
- Open an issue with the [provider template](.github/ISSUE_TEMPLATE) for additions.

We do **not** accept referral links or marketing copy. Factual, dated,
source-backed entries only.

## License

[![CC0](https://licensebuttons.net/p/zero/1.0/80x15.png)](LICENSE) —
To the extent possible under law, contributors have waived all copyright and
related rights to this work ([CC0 1.0](LICENSE)).

## Disclaimer

This repository is an informational catalogue. It is **not** an endorsement of
any service. Many relays operate in legal grey areas and may violate upstream
providers' Terms of Service. Using a relay can expose your prompts, code, and
data to an unaccountable third party. Evaluate risk yourself and comply with
all applicable laws and contracts.
