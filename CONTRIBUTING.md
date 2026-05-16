# Contributing

Thanks for helping keep this list accurate. This is a **community-maintained**
catalogue — the original [mn-api/awesome-ai-proxy](https://github.com/mn-api/awesome-ai-proxy)
went stale; the goal here is to stay current.

繁中 / 简中贡献者：可以用中文开 issue / PR，维护者会处理。

## What we accept

- **New stations** with a working URL and an honest channel `type`.
- **Corrections** (price, status, ownership, payment methods).
- **Status changes** — especially marking a station `inactive` if it ran away
  ("跑路"). We keep dead entries with a dated note; we do not erase history.
- **Documented risk cases** for [`docs/risks.md`](docs/risks.md) — must have a
  date and a primary source link.

## What we reject

- Referral / affiliate links. Plain URLs only.
- Marketing copy, superlatives ("best", "#1", "cheapest") without a dated source.
- Stations with no reachable URL.
- Unsourced accusations against a specific operator.

## How to add or edit a provider

1. **Edit [`data/providers.yaml`](data/providers.yaml)** — the README tables are
   generated from it. Do **not** edit the README tables directly; they will be
   overwritten.
2. Follow the [field schema](data/schema.md). Required: `name`, `url`, `type`,
   `status`.
3. Mark anything you could not personally verify as `status: unverified` and say
   so in `notes`.
4. Bump `last_reviewed` in `providers.yaml` if you did a broad pass.
5. Open a Pull Request. Use a clear title, e.g.
   `add: ExampleAPI (mixed)` or `status: GPTGOD → inactive (ran away 2026-05)`.

Not comfortable with a PR? Open an issue with the
[provider template](.github/ISSUE_TEMPLATE/new-provider.md) and a maintainer
will add it.

## Review bar

A maintainer will check:

- URL resolves and is the official site (not a clone/phishing mirror).
- `type` is honest (a `reverse` station not mislabeled `official-relay`).
- `notes` is one factual sentence, no marketing.
- Claims are attributed where non-obvious.

## Maintenance cadence

- Monthly review pass (`last_reviewed` updated in `providers.yaml`).
- Issues triaged within ~1 week.
- Anyone can help: a PR that just verifies/refreshes existing entries is
  valuable and welcome.

## Conduct

Be factual and neutral. This catalogue documents a grey-area market for safety
and transparency. It is not a place to promote a station or attack one without
evidence.
