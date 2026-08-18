# Agent-first contribution guide

> **For AI agents (Claude Code, Cursor, Codex, Aider, OpenClaw, …) and humans
> driving them.** This repo is machine-maintained. Hand-editing README tables
> or pasting marketing copy will be closed by CI / maintainers.

**Canonical sources (always read these before editing):**

| Doc | URL |
|---|---|
| This playbook | `docs/agent-contribute.md` |
| Field schema | [`data/schema.md`](../data/schema.md) |
| Human CONTRIBUTING | [`CONTRIBUTING.md`](../CONTRIBUTING.md) |
| Provider catalog (edit target) | [`data/providers.yaml`](../data/providers.yaml) |
| llms.txt entrypoint | [`llms.txt`](../llms.txt) |

---

## Decision tree (do this first)

```
Want prices in the weekly snapshot?
  ├─ Public JSON pricing API exists → Path A (fetcher)
  └─ No public API / screenshot only → Path B (issue: submit-prices)

Want a new station listed (no prices yet)?
  ├─ You are the operator / affiliated → Path C (issue only, not PR)
  └─ Independent third party → Path D (PR: providers.yaml only)

Want to fix a dead link / ran-away / typo?
  └─ Path D (PR: providers.yaml only)
```

**Never:** edit generated README tables between
`<!-- providers:*:start -->` … `<!-- providers:*:end -->`.
CI rejects hand-edits. Tables are built by
`python -m scripts.build_provider_tables`.

---

## Hard rules (CI fails the PR)

1. **Only edit** `data/providers.yaml` (and fetcher files if Path A).
2. **URL** must be plain `https://` — no `utm_*`, `ref=`, `campaignid`, affiliate params.
3. **`status: active` is maintainer-only.** New entries use `status: unverified`.
4. **Self / operator submissions** must include:
   ```yaml
   status: unverified
   verified_by: community
   risk_flags: [operator_submitted]
   ```
5. **`notes`**: one factual sentence per language, ≤ 360 chars. No superlatives
   (`#1`, `the best`, 强烈推荐, 不降智, …).
6. **No duplicate** `name` or same host+path URL already in the file.
7. Run before opening the PR:
   ```bash
   python -m scripts.validate
   ```

---

## Path C — Operator / affiliated (preferred: Issue, not PR)

Open a GitHub Issue with the **required form** (blank issues are auto-closed):

https://github.com/howardpen9/awesome-ai-api-proxy/issues/new?template=new-provider.yml

Every field is required. Maintainer converts to YAML. Do **not** open a PR claiming
`status: active` or `type: official-relay` without independent evidence.

---

## Path D — Third-party catalog PR (agent recipe)

### 0. Setup

```bash
git clone https://github.com/howardpen9/awesome-ai-api-proxy.git
cd awesome-ai-api-proxy
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 1. Check it is not already listed

```bash
rg -n -i 'example\.com|ExampleName' data/providers.yaml
```

### 2. Append a minimal entry

Pick the correct section: `china_relays` | `global_gateways` |
`self_hosted_alternatives` | `comparison_tools`.

```yaml
  - name: ExampleAPI
    url: https://example.com
    type: mixed          # official-relay | mixed | reverse | aggregator | gateway-oss | observability | comparison | list
    status: unverified   # NEVER active unless you are the maintainer
    payment: [alipay, wechat]   # optional
    models: [openai, anthropic, gemini]
    last_verified: null
    verified_by: community
    entity_registered: unknown
    supports_stream: unknown
    supports_tools: unknown
    # risk_flags: [operator_submitted]   # REQUIRED if self-submitted
    notes:
      en: "One factual sentence. No marketing."
```

### 3. Validate

```bash
python -m scripts.validate
# exit 0 required
```

Optional local README regen (maintainer will also run this):

```bash
python -m scripts.build_provider_tables
```

### 4. Open PR

- **Title:** `add: ExampleAPI (mixed)` or `status: Foo → inactive (ran away YYYY-MM-DD)`
- **Body:** use `.github/PULL_REQUEST_TEMPLATE.md`; fill Source / verification
- **Files:** only `data/providers.yaml` (+ fetcher files if Path A)

---

## Path A — Price fetcher (agent recipe)

```bash
python -m scripts.sniff_endpoint <pricing_api_url> \
  --id <slug> --name "<Display Name>" --display-url <human_pricing_page>
```

Paste the printed YAML block + `fetchers/<slug>.py` + REGISTRY line, then:

```bash
python -m scripts.scrape <slug>
python -m scripts.build_prices
python -m scripts.validate
```

Details: [CONTRIBUTING.md § Adding a price fetcher](../CONTRIBUTING.md#adding-a-price-fetcher).

---

## Path B — Manual prices (no JSON API)

https://github.com/howardpen9/awesome-ai-api-proxy/issues/new?template=submit-prices.yml

Include a markdown price table + screenshot of the live pricing page.

---

## Minimal YAML example (copy-paste)

```yaml
  - name: ExampleRelay
    url: https://example-relay.example
    type: aggregator
    status: unverified
    payment: [card]
    models: [openai, anthropic]
    last_verified: null
    verified_by: community
    entity_registered: unknown
    supports_stream: unknown
    supports_tools: unknown
    risk_flags: [operator_submitted]   # delete this line if truly third-party
    notes:
      en: "OpenAI-compatible gateway; prepaid balance; community-listed."
```

---

## Why your previous PR was closed

Common failures we auto-close:

| Failure | Fix |
|---|---|
| Edited `README.md` tables | Edit `data/providers.yaml` only |
| UTM / affiliate URL | Strip query string to plain HTTPS homepage |
| `status: active` without maintainer verify | Use `unverified` |
| Operator self-PR without `operator_submitted` | Add flag, or open Issue (Path C) |
| Marketing `notes` / superlatives | One factual sentence |
| Duplicate of open PR / existing entry | Search yaml first |
| Encoding corruption / bulk rewrite of unrelated names | Touch only your new block |
| Blank / free-form issue | Use the `new-provider.yml` form — required fields, or it is auto-closed |

Re-open by following Path C or D above. Schema CI will tell you the exact field if something is still wrong.

---

## Maintainer close comment (copy-paste)

See [`.github/CLOSE_OUT_OF_SPEC.md`](../.github/CLOSE_OUT_OF_SPEC.md).
