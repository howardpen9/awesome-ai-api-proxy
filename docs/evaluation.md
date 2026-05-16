# How to Evaluate an AI API Relay Station

A practical framework for choosing a relay ("中轉站") without getting burned.
Read alongside [risks.md](risks.md).

## 1. Identify the channel type first

This single dimension predicts most of the quality/risk tradeoff.

| Type | Quality | Price | Stability | ToS risk |
|---|---|---|---|---|
| `official-relay` | Highest (pure) | Highest | High | Low |
| `mixed` | Good | Medium | Medium | Medium |
| `aggregator` | Varies by route | Medium | Medium | Medium |
| `reverse` | Unpredictable | Lowest | Lowest | High |
| `gateway-oss` | Your keys = official | Cost + infra | You own it | Low |

Rule of thumb: **the cheaper it is, the more likely it is `reverse` or
silently degraded.** A price that's 1/50 of official is a signal, not a deal.

## 2. The trust checklist

Score a station before topping up real money:

- [ ] **Channel type stated honestly** (官轉/混合/逆向). Vague = bad sign.
- [ ] **Legal entity / ICP filing** exists (not just an "enterprise" banner).
- [ ] **Small top-up allowed** (you can test with $5, not forced into $100+).
- [ ] **Model identity verifiable** (run a canary; see below).
- [ ] **Latency acceptable** from your region.
- [ ] **Operating history** > 6 months with no mass "跑路" reports.
- [ ] **Refund / support channel** that actually answers.
- [ ] **Privacy stance** documented (logging, retention).

5+ checked → usable for non-sensitive work.
< 3 checked → treat as disposable, hobby only.

## 3. The canary test (detect 降智 / model substitution)

Relays can silently swap the model. Catch it:

1. Keep 3–5 **known-hard prompts** with stable expected behavior (a tricky
   reasoning question, a long-context recall task, a format-strict output).
2. Run them against the **official API** and record the baseline.
3. Run the same prompts against the relay.
4. Compare: refusal style, token patterns, reasoning depth, format adherence.
5. Re-run weekly — degradation often appears *after* you've topped up.

A station that passes on day 1 and fails on day 30 is the classic exit-scam
curve. Automate this if you depend on the station.

## 4. Red flags (walk away)

- Price dramatically below every other station (1/50 of official).
- No statement of channel type, or "all official" with no proof.
- Forced large prepaid top-up, no small test tier.
- Telegram-only support, anonymous operator, no entity.
- Pressure tactics ("limited-time", "price going up tonight").
- Asks you to disable TLS verification or use a custom CA.

## 5. Match the station to the workload

| Workload | Recommendation |
|---|---|
| Hobby / experiments | Cheap relay is fine; assume it may vanish. |
| Production app | `official-relay` with entity + SLA, or official API directly. |
| Sensitive / regulated data | Official API or self-hosted `gateway-oss`. Never `reverse`. |
| High volume, cost-sensitive | Compare `mixed`/`aggregator`; canary continuously. |
| Multi-vendor consolidation | Global `aggregator` (e.g. OpenRouter) if payment allows. |

## 6. Regional note

Relay demand correlates with **blocking + payment friction**, not geography.
China has the deepest ecosystem because both pains peak there, but the same
need appears wherever official access is blocked or unpayable (see the main
README's "Why this exists globally" section). Pick based on your constraints,
not on where a station is hosted.
