"""Probe a pricing endpoint and tell a contributor (human or AI agent) exactly
what to paste to add a fetcher.

Usage:
    python -m scripts.sniff_endpoint <pricing_api_url> [--id slug] [--name "Display Name"]

Detects three shapes today:
    1. new-api / one-api fork  -- {success, data: [{model_name, model_ratio, ...}], group_ratio}
    2. OpenRouter-style models -- {data: [{id, pricing: {prompt, completion, image}}]}
    3. OpenAI /v1/models       -- {data: [{id, ...}]} without pricing (cannot price; flag it)

For each known shape it prints (a) the YAML block to paste into providers.yaml,
(b) the 10-line fetcher snippet, and (c) the one-liner to test it. For unknown
shapes it dumps a redacted sample and tells the contributor what to do.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


# ---------------------------------------------------------------------------
# Shape detectors -- each returns a dict with everything the renderer needs,
# or None if the payload doesn't match.
# ---------------------------------------------------------------------------


def detect_new_api(payload: Any) -> dict | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None
    sample = data[0]
    if not isinstance(sample, dict):
        return None
    new_api_keys = {"model_name", "quota_type"}
    if not new_api_keys.issubset(sample.keys()):
        return None

    # Decide whether a flat "default" group exists or it's per-model channels.
    group_ratio = payload.get("group_ratio") or {}
    flat_default = "default" in group_ratio
    sample_enable = sample.get("enable_groups") or []
    has_default_in_enable = any(
        isinstance(g, str) and g == "default" for g in sample_enable
    )
    # If every group key looks model-specific (e.g. "default-yun-xxx") and
    # there's no plain "default" we treat it as per-model channels.
    looks_per_model = (
        not flat_default
        and not has_default_in_enable
        and len(group_ratio) > 10
    )

    return {
        "shape": "new-api",
        "model_count": len(data),
        "group_mode": "per_model" if looks_per_model else "default",
    }


def detect_openrouter(payload: Any) -> dict | None:
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None
    sample = data[0]
    if not isinstance(sample, dict):
        return None
    pricing = sample.get("pricing")
    if not isinstance(pricing, dict):
        return None
    if "prompt" not in pricing and "completion" not in pricing:
        return None
    return {
        "shape": "openrouter",
        "model_count": len(data),
    }


def detect_openai_models(payload: Any) -> dict | None:
    """OpenAI-compatible /v1/models -- listing only, no prices."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None
    sample = data[0]
    if not isinstance(sample, dict):
        return None
    if "id" in sample and "object" in sample and sample.get("object") == "model":
        return {"shape": "openai-models", "model_count": len(data)}
    return None


DETECTORS = [detect_new_api, detect_openrouter, detect_openai_models]


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def _print_panel(title: str, body: str, *, lang: str = "yaml") -> None:
    console.print(Panel(Syntax(body, lang, theme="ansi_dark"), title=title, border_style="cyan"))


def render_new_api(url: str, info: dict, slug: str, name: str, display_url: str) -> None:
    per_model = info["group_mode"] == "per_model"
    group_arg = "        group=None,\n" if per_model else ""
    note = (
        " (per-model channel groups — group=None uses each model's public ratio, not 1)"
        if per_model
        else " (flat 'default' group detected)"
    )

    console.print(
        f"\n[bold green]✓ Detected shape: new-api fork[/bold green]{note}"
    )
    console.print(f"  • {info['model_count']} models on the endpoint")
    console.print(
        "  • Reuses [cyan]fetchers/_new_api.py[/cyan] — no custom parsing needed.\n"
    )

    yaml_block = f"""# In data/providers.yaml under your provider entry:
    pricing:
      pricing_url: {display_url}
      api_url: {url}
      fetcher: {slug}
      pricing_currency: USD"""
    _print_panel("1. Paste into providers.yaml", yaml_block, lang="yaml")

    fetcher_src = f'''"""{name} — new-api fork. Thin wrapper over fetchers._new_api."""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "{slug}"
PROVIDER_NAME = "{name}"
SOURCE_URL = "{url}"
DISPLAY_URL = "{display_url}"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="mixed",  # or: official-relay | reverse | aggregator
{group_arg}    )
'''
    _print_panel(f"2. Create fetchers/{slug}.py", fetcher_src, lang="python")

    registry_line = f'    "{slug}": "fetchers.{slug}",'
    _print_panel(
        "3. Register in fetchers/__init__.py REGISTRY",
        registry_line,
        lang="python",
    )

    console.print(
        f"\n[bold]4. Verify:[/bold] [cyan]python -m scripts.scrape {slug}[/cyan]"
    )
    console.print(
        f"   then [cyan]python -m scripts.build_prices && python -m scripts.validate[/cyan]\n"
    )


def render_openrouter(url: str, info: dict, slug: str, name: str, display_url: str) -> None:
    console.print(
        f"\n[bold green]✓ Detected shape: OpenRouter-style /v1/models with pricing[/bold green]"
    )
    console.print(f"  • {info['model_count']} models with embedded pricing.\n")
    console.print(
        "[yellow]No shared wrapper exists yet for this shape[/yellow] — closest "
        "reference is [cyan]fetchers/openrouter.py[/cyan]. Copy that, rename the constants, "
        "and adjust the pricing key paths if they differ.\n"
    )

    yaml_block = f"""    pricing:
      pricing_url: {display_url}
      api_url: {url}
      fetcher: {slug}
      pricing_currency: USD"""
    _print_panel("Paste into providers.yaml", yaml_block, lang="yaml")
    console.print(
        f"Then copy [cyan]fetchers/openrouter.py[/cyan] → "
        f"[cyan]fetchers/{slug}.py[/cyan], change PROVIDER_ID/NAME/SOURCE_URL, "
        f"and add to REGISTRY.\n"
    )


def render_openai_models(url: str, info: dict, slug: str, name: str, display_url: str) -> None:
    console.print(
        f"\n[bold yellow]△ Detected shape: OpenAI-compatible /v1/models[/bold yellow]"
    )
    console.print(
        f"  • {info['model_count']} models listed, but [bold]no pricing fields[/bold].\n"
    )
    console.print(
        "This endpoint only returns model IDs. Look for a separate pricing page on the "
        "site (often [cyan]/pricing[/cyan] or [cyan]/api/pricing[/cyan]) and re-run the "
        "sniffer against that URL. If no JSON pricing exists, fall back to the "
        "[bold]submitted_prices[/bold] flow in [cyan]data/schema.md[/cyan].\n"
    )


def render_unknown(url: str, payload: Any) -> None:
    console.print(
        f"\n[bold red]✗ Could not auto-detect the pricing shape.[/bold red]\n"
    )
    sample = json.dumps(payload, indent=2, ensure_ascii=False)[:1200]
    _print_panel("First 1200 chars of response (review by hand):", sample, lang="json")
    console.print(
        "Next steps for a contributor:\n"
        "  1. Skim the response — is it a list of models with prices? a wrapper?\n"
        "  2. If prices look extractable, write a custom fetcher modelled on "
        "[cyan]fetchers/openrouter.py[/cyan]. Every PriceRecord must carry "
        "[cyan]source_url[/cyan], [cyan]captured_at[/cyan], [cyan]method[/cyan].\n"
        "  3. If prices aren't in JSON, use the [cyan]submitted_prices[/cyan] flow "
        "(see [cyan]data/schema.md[/cyan]) — paste a table from the pricing page.\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(
        description="Sniff a pricing endpoint and emit a ready-to-paste fetcher recipe."
    )
    p.add_argument("url", help="pricing API URL to probe")
    p.add_argument("--id", default="example", help="provider slug for fetcher filename")
    p.add_argument("--name", default="Example", help="provider display name")
    p.add_argument(
        "--display-url",
        default=None,
        help="user-facing pricing page (defaults to the API URL host)",
    )
    args = p.parse_args()

    display_url = args.display_url or args.url

    console.print(f"\n[bold]Probing[/bold] {args.url} …")
    try:
        with httpx.Client(timeout=20, follow_redirects=True) as c:
            r = c.get(
                args.url,
                headers={"Accept": "application/json", "User-Agent": "awesome-ai-api-proxy/sniff"},
            )
            r.raise_for_status()
    except httpx.HTTPError as e:
        console.print(f"[red]HTTP error:[/red] {e}")
        return 2

    try:
        payload = r.json()
    except json.JSONDecodeError:
        console.print(
            "[red]Response is not JSON.[/red] If this is the marketing pricing page rather "
            "than the JSON endpoint, find the underlying API call (open DevTools → Network → "
            "filter JSON) and rerun against that URL."
        )
        return 2

    for detector in DETECTORS:
        info = detector(payload)
        if not info:
            continue
        if info["shape"] == "new-api":
            render_new_api(args.url, info, args.id, args.name, display_url)
        elif info["shape"] == "openrouter":
            render_openrouter(args.url, info, args.id, args.name, display_url)
        elif info["shape"] == "openai-models":
            render_openai_models(args.url, info, args.id, args.name, display_url)
        return 0

    render_unknown(args.url, payload)
    return 1


if __name__ == "__main__":
    sys.exit(main())
