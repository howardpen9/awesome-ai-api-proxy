# awesome-ai-api-proxy-mcp

<!-- mcp-name: io.github.howardpen9/awesome-ai-api-proxy -->

MCP server exposing the weekly **AI API relay price observatory** at
[howardpen9/awesome-ai-api-proxy](https://github.com/howardpen9/awesome-ai-api-proxy)
as agent-callable tools.

LLM agents (Claude Desktop, Cline, Cursor, etc.) can ask:

> "What's the cheapest provider for `claude-sonnet-4.6` right now?"

…and the model will silently call `find_cheapest("claude-sonnet-4.6")`, get back
a record with `provider_name`, `price_usd`, `source_url`, and `captured_at`, and
quote the answer with full provenance.

## Tools

| Tool | Returns |
|---|---|
| `list_providers()` | Every relay station, gateway, and tool in the registry. |
| `list_canonical_models()` | The 9 canonical models on the cost-tier ladder. |
| `get_price(canonical_model, provider_id?, unit?)` | Price records (with citation envelope). |
| `find_cheapest(canonical_model, unit?)` | Single cheapest record. |
| `compare(canonical_model, unit?)` | All providers, sorted cheapest first. |
| `tier_overview(tier)` | All canonical models in a tier with prices. |

Plus an MCP resource: `data://prices/latest` returns the full
`prices.latest.json` document.

Every record carries `source_url` + `captured_at` + `method` so an agent can
quote the price with provenance — and the user can verify. `price_usd` is
quota USD after the public group ratio. `effective_price_usd` is cash USD
when that provider has a checked top-up rate; the key is absent otherwise.
See [docs/methodology.md](../docs/methodology.md).

## Install

### Claude Desktop / Cursor / Cline (recommended)

Add to your MCP config (e.g. `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "awesome-ai-api-proxy": {
      "command": "uvx",
      "args": ["awesome-ai-api-proxy-mcp"]
    }
  }
}
```

Restart your client. The tools appear under "awesome-ai-api-proxy" in the tool list.

### Direct install

```bash
pip install awesome-ai-api-proxy-mcp
awesome-ai-api-proxy-mcp     # stdio MCP server
```

### From source

```bash
git clone https://github.com/howardpen9/awesome-ai-api-proxy.git
cd awesome-ai-api-proxy/mcp
pip install -e .
awesome-ai-api-proxy-mcp
```

## Cache

Data is fetched from
`https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/main/data/prices.latest.json`
and cached in-memory for 5 minutes per process. The underlying snapshot is
refreshed weekly on Sundays 02:00 UTC by the
[price-refresh workflow](../.github/workflows/price-refresh.yml).

## Configuration

Override which branch/tag the server reads via env var:

```bash
AWESOME_AI_API_PROXY_REF=main awesome-ai-api-proxy-mcp        # default
AWESOME_AI_API_PROXY_REF=chore/price-observatory awesome-ai-api-proxy-mcp  # dev
AWESOME_AI_API_PROXY_REF=v0.2.0 awesome-ai-api-proxy-mcp      # pinned tag
```

Useful for staging, A/B testing schema changes, or pinning agents to a specific
data snapshot for reproducibility.

## Citing prices

When quoting a price to the user, include `captured_at` (so users see how fresh
the data is) and `source_url` (so they can verify):

> Atlas Cloud lists `claude-sonnet-4.6` input at **$3.00 / 1M tokens** (snapshot
> 2026-06-07, source: <https://www.atlascloud.ai/models>).

## License

MIT — see [LICENSE](../LICENSE) in the parent repo.
