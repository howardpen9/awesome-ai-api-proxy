# Risks of AI API Relay Stations (中轉站風險案例庫)

AI API relay stations ("中轉站") solve real pain — payment and network barriers —
but the market is largely unregulated. This page documents **evidence-based risks**
so you can make an informed choice. Every claim links to a source where possible.

> This is a neutral reference, not an accusation against any specific provider.
> Numbers are from public research and reporting; verify before citing.

## TL;DR

| Risk | Evidence |
|---|---|
| Model substitution ("降智") | A study of 28 relays found **45.83% of API endpoints had model-identity mismatches**; up to 47% performance gap in medical-domain tasks. |
| Malicious operators | An audit of **428 relay stations** found **9 injecting malicious code** and **1 directly stealing funds**. |
| No legal entity | Of 17 surveyed top stations, **15 were run by individuals** with no registered company and no ICP filing. |
| Supply-chain blast radius | A LiteLLM dependency vulnerability reportedly affected **40,000+ developer environments**. |
| Exit scams ("跑路") | Common pattern: silently downgrade to a cheaper model, then disappear before users notice. |
| Data exposure | Every request — code, business docs, customer data — passes through an unaccountable third party. |

## 1. Model substitution / "降智" (silent downgrade)

The most common complaint. You pay for GPT-4-class output; the station quietly
routes to a cheaper or quantized model. Because responses still "look fine,"
detection is hard until quality-sensitive tasks fail.

- A research paper testing **28 relay stations** reported **45.83% of API
  endpoints returned a model whose identity did not match the one requested**.
- In medical-domain evaluation, the performance gap between the claimed model
  and the actually-served model reached **up to 47%**.

**Mitigation:** run periodic canary prompts with known-hard questions; compare
token-level behavior against the official API; prefer `official-relay` type.

## 2. Malicious operators

A security audit covering **428 relay stations** found:

- **9 stations** injected malicious code into responses or SDK snippets.
- **1 station** directly stole funds (charged top-ups, delivered nothing).

The relay sits in the middle of your request path, so a hostile operator can
modify prompts, exfiltrate data, or tamper with returned code.

**Mitigation:** never paste secrets/credentials through a relay; treat
relay-returned code as untrusted input; review before executing.

## 3. No accountable legal entity

A survey of 17 top-tier stations found **15 operated by individuals** — no
registered company, no ICP filing, no recourse if they vanish. "Enterprise"
branding does not imply a legal entity behind it.

**Mitigation:** check for a registered company / ICP filing; prefer stations
with invoices and a support SLA for anything beyond hobby use.

## 4. Supply-chain blast radius

Gateways and their dependencies are themselves attack surface. A LiteLLM
dependency vulnerability reportedly reached **40,000+ developer environments** —
relay risk can propagate upstream into your toolchain.

**Mitigation:** pin gateway versions; isolate keys; least-privilege API tokens.

## 5. Exit scams (跑路)

The textbook playbook:

1. Launch with aggressive pricing (1/10 – 1/50 of official).
2. Attract prepaid top-ups (relays are almost always prepaid).
3. Silently degrade quality to cut costs.
4. Disappear with outstanding balances before refunds.

**Mitigation:** top up small amounts; never prepay large balances; treat
extremely cheap stations as disposable.

## 6. Data exposure

Every call — your prompts, code, business documents, possibly customer data —
transits a third party you cannot audit. For regulated data this may be a
compliance violation regardless of the operator's intent.

**Mitigation:** classify data before sending; route sensitive workloads through
official APIs or self-hosted `gateway-oss`.

---

## Sources

- 虎嗅 — AI 中轉站灰色產業鏈曝光: <https://www.huxiu.com/article/4856845.html>
- ChainCatcher — AI 中轉站月入百萬: <https://www.chaincatcher.com/zh-tw/article/2260462>
- V2EX — 中轉站可被用來劫持你的 Agent: <https://www.v2ex.com/t/1211298>

> Found a documented incident with a primary source? Open a PR adding it here
> with a date and link. See [CONTRIBUTING.md](../CONTRIBUTING.md).
