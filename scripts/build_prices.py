"""Compile the latest day's snapshots into prices.latest.json + README tables.

Steps:
1. Find the newest data/snapshots/<date>/ dir
2. Load every <fetcher>.json (skip .error.json — they're handled by the PR body)
3. Resolve each PriceRecord against data/canonical-models.yaml (alias → canonical)
4. Write data/prices.latest.json (flat normalized list, with canonical resolved)
5. Render the README price table between <!-- prices:start --> markers in all 3 READMEs
6. Render docs/prices.md (full table: every model seen, canonical or not)
7. Append a summary line to data/prices.history.jsonl

Run after `python -m scripts.scrape`.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml
from rich.console import Console

from fetchers._common import strip_adjustment_fields

from ._paths import (
    CANONICAL_YAML,
    DOCS_LLMS_TXT,
    LLMS_TXT,
    PRICES_DOC,
    PRICES_HISTORY,
    PRICES_INDEX,
    PRICES_LATEST,
    PROVIDERS_YAML,
    READMES,
    SNAPSHOTS_DIR,
)

PAGES_ORIGIN = "https://howardpen9.github.io/awesome-ai-api-proxy"
GITHUB_RAW = "https://raw.githubusercontent.com/howardpen9/awesome-ai-api-proxy/main"

console = Console()

# Priority only. Every provider present in the snapshot is rendered;
# names not in this list are appended alphabetically.
PREFERRED_PROVIDER_ORDER = ["openrouter", "atlascloud", "relaydance", "uiuiapi", "bltcy"]
START_MARKER = "<!-- prices:start -->"
END_MARKER = "<!-- prices:end -->"


def _provider_column_order(matrix: dict) -> list[str]:
    seen = {k[2] for k in matrix}
    ordered = [p for p in PREFERRED_PROVIDER_ORDER if p in seen]
    ordered += sorted(seen - set(ordered))
    return ordered


def _load_provider_display_names() -> dict[str, str]:
    """Map provider_id -> the name already used in the price tables.

    Display names come from providers.yaml (`pricing.fetcher`). Two legacy
    headers are pinned so a regen does not rename columns that predate the
    yaml display name: OpenRouter stays "OpenRouter (ref)", bltcy stays "bltcy".
    """
    doc = yaml.safe_load(PROVIDERS_YAML.read_text(encoding="utf-8"))
    names: dict[str, str] = {}
    for _section, entries in doc.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            pricing = entry.get("pricing") or {}
            provider_id = pricing.get("fetcher") or _slug(entry.get("name", ""))
            if provider_id and entry.get("name"):
                names[provider_id] = entry["name"]
    names["openrouter"] = "OpenRouter (ref)"
    names["bltcy"] = "bltcy"
    return names


def _latest_snapshot_dir() -> Path:
    dirs = sorted(p for p in SNAPSHOTS_DIR.iterdir() if p.is_dir())
    if not dirs:
        raise RuntimeError(f"No snapshot dir under {SNAPSHOTS_DIR}; run scripts.scrape first.")
    return dirs[-1]


def _load_canonical() -> dict:
    return yaml.safe_load(CANONICAL_YAML.read_text(encoding="utf-8"))


def _build_alias_index(canonical_doc: dict) -> dict[str, dict]:
    """Map every alias (lowercased) → its canonical entry."""
    out: dict[str, dict] = {}
    for entry in canonical_doc.get("canonical_models", []):
        for alias in entry.get("aliases", []) or []:
            out[alias.lower()] = entry
        # Also auto-map the canonical name itself.
        out[entry["canonical"].lower()] = entry
    return out


def _load_snapshots(snapshot_dir: Path) -> list[dict]:
    """Flatten every fetcher's records, drop .error.json files."""
    flat: list[dict] = []
    for path in sorted(snapshot_dir.glob("*.json")):
        if path.name.endswith(".error.json"):
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        flat.extend(result.get("records", []))
    return flat


def _load_submitted_prices() -> list[dict]:
    """Read each provider's pricing.submitted_prices and convert to PriceRecord-shaped dicts."""
    doc = yaml.safe_load(PROVIDERS_YAML.read_text(encoding="utf-8"))
    out: list[dict] = []
    for section, entries in doc.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            pricing = entry.get("pricing") or {}
            submitted = pricing.get("submitted_prices") or []
            for sp in submitted:
                # Build a slug from provider name. Use the fetcher id when present
                # so manual + fetched records share provider_id (column in table).
                provider_id = pricing.get("fetcher") or _slug(entry.get("name", ""))
                out.append({
                    "provider_id": provider_id,
                    "provider_name": entry.get("name", ""),
                    "raw_model_name": sp["canonical_model"],
                    "canonical_model": sp["canonical_model"],
                    "model_family": None,
                    "tier": None,
                    "channel_type": entry.get("type", "unknown"),
                    "unit": sp["unit"],
                    "price_usd": sp["price_usd"],
                    "source_url": sp.get("source_url", pricing.get("pricing_url", "")),
                    "captured_at": sp.get("captured_at", ""),
                    "confidence": "medium",
                    "method": "manual",
                    "notes": f"submitted by {sp.get('submitted_by','?')}, verified by {sp.get('verified_by','?')}",
                })
    return out


def _slug(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-")


def _iter_provider_entries(doc: dict):
    for _section, entries in doc.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict):
                yield entry


def inactive_fetcher_ids(doc: dict | None = None) -> set[str]:
    """Fetcher ids whose provider status is inactive.

    Current tables and prices.latest drop these even when the newest snapshot
    still contains rows. Historical snapshot files are left in place.
    """
    if doc is None:
        doc = yaml.safe_load(PROVIDERS_YAML.read_text(encoding="utf-8"))
    out: set[str] = set()
    for entry in _iter_provider_entries(doc):
        if entry.get("status") != "inactive":
            continue
        fetcher = (entry.get("pricing") or {}).get("fetcher")
        if fetcher:
            out.add(fetcher)
    return out


def load_topup_rates(doc: dict | None = None) -> dict[str, dict]:
    """Map fetcher id → pricing.topup_rate, when that block is present."""
    if doc is None:
        doc = yaml.safe_load(PROVIDERS_YAML.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for entry in _iter_provider_entries(doc):
        pricing = entry.get("pricing") or {}
        fetcher = pricing.get("fetcher")
        rate = pricing.get("topup_rate")
        if fetcher and isinstance(rate, dict):
            checked = rate.get("checked")
            normalized = dict(rate)
            if checked is not None:
                normalized["checked"] = str(checked)
            out[fetcher] = normalized
    return out


def topup_multiplier(rate: dict | None) -> float | None:
    """payment-currency-per-quota-USD / site FX. None when either number is missing."""
    if not rate:
        return None
    amount = rate.get("amount")
    fx = rate.get("fx_per_usd")
    if not isinstance(amount, (int, float)) or not isinstance(fx, (int, float)):
        return None
    if amount <= 0 or fx <= 0:
        return None
    return float(amount) / float(fx)


def effective_price_usd(price_usd: float, rate: dict | None) -> float | None:
    """Cash USD of a quota-USD price. None when no checked top-up rate can convert it."""
    multiplier = topup_multiplier(rate)
    if multiplier is None:
        return None
    return round(float(price_usd) * multiplier, 6)


def records_for_current_build(
    records: list[dict],
    inactive_ids: set[str],
) -> tuple[list[dict], int]:
    """Drop inactive providers and unset-placeholder rows from the published build.

    Returns (kept records, excluded placeholder count).
    """
    kept: list[dict] = []
    excluded = 0
    for rec in records:
        if rec.get("provider_id") in inactive_ids:
            continue
        if rec.get("price_placeholder"):
            excluded += 1
            continue
        kept.append(rec)
    return kept, excluded


def annotate_effective(records: list[dict], rates: dict[str, dict]) -> None:
    for rec in records:
        eff = effective_price_usd(rec.get("price_usd") or 0, rates.get(rec.get("provider_id")))
        if eff is not None:
            rec["effective_price_usd"] = eff
        strip_adjustment_fields(rec)


def _topup_summary(rates: dict[str, dict]) -> dict[str, dict]:
    summary: dict[str, dict] = {}
    for pid, rate in sorted(rates.items()):
        multiplier = topup_multiplier(rate)
        if multiplier is None:
            continue
        summary[pid] = {
            "amount": rate.get("amount"),
            "currency": rate.get("currency"),
            "fx_per_usd": rate.get("fx_per_usd"),
            "multiplier": round(multiplier, 6),
            "source_url": rate.get("source_url"),
            "checked": rate.get("checked"),
        }
    return summary


def _resolve_canonical(records: list[dict], alias_index: dict[str, dict]) -> list[dict]:
    """Mutate each record with canonical_model / model_family / tier when alias matches."""
    for rec in records:
        raw = rec.get("raw_model_name", "")
        # Try full match, then strip the vendor prefix.
        candidates = [raw, raw.split("/", 1)[-1], raw.split(":", 1)[0]]
        for c in candidates:
            entry = alias_index.get(c.lower())
            if entry:
                rec["canonical_model"] = entry["canonical"]
                rec["model_family"] = entry.get("family")
                rec["tier"] = entry.get("tier")
                break
    return records


def _write_prices_latest(
    records: list[dict],
    snapshot_date: str,
    *,
    excluded_placeholder_count: int,
    topup_rates: dict[str, dict],
) -> None:
    PRICES_LATEST.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "snapshot_date": snapshot_date,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "record_count": len(records),
                "excluded_placeholder_count": excluded_placeholder_count,
                "topup_rates": topup_rates,
                "records": records,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_tabular_exports(records: list[dict], snapshot_date: str) -> tuple[Path, Path] | None:
    """Write CSV + Parquet alongside the JSON for analyst-friendly access.

    Skipped silently when pandas isn't installed (the [charts] extra).
    """
    try:
        import pandas as pd
    except ImportError:
        console.print("[yellow]pandas not installed — skipping CSV/Parquet export. "
                      "Install with `pip install -e .[charts]`[/yellow]")
        return None

    df = pd.DataFrame(records)
    # Add snapshot_date as a column so the CSV is self-describing.
    df.insert(0, "snapshot_date", snapshot_date)
    csv_path = PRICES_LATEST.with_suffix(".csv")
    parquet_path = PRICES_LATEST.with_suffix(".parquet")
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False, compression="snappy")
    return csv_path, parquet_path


def _append_history(records: list[dict], snapshot_date: str) -> None:
    provider_counts: dict[str, int] = defaultdict(int)
    canonical_seen: set[str] = set()
    for rec in records:
        provider_counts[rec["provider_id"]] += 1
        if rec.get("canonical_model"):
            canonical_seen.add(rec["canonical_model"])
    line = (
        json.dumps(
            {
                "snapshot_date": snapshot_date,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "record_count": len(records),
                "providers": dict(provider_counts),
                "canonical_models_seen": sorted(canonical_seen),
            },
            ensure_ascii=False,
        )
        + "\n"
    )
    with PRICES_HISTORY.open("a", encoding="utf-8") as f:
        f.write(line)


def _format_price(price: float) -> str:
    if price >= 10:
        return f"${price:.2f}"
    if price >= 1:
        return f"${price:.3f}"
    if price >= 0.01:
        return f"${price:.3f}"
    return f"${price:.4f}"


def _build_tier_tables(
    records: list[dict],
    canonical_doc: dict,
    snapshot_date: str,
    *,
    excluded_placeholder_count: int,
    topup_rates: dict[str, dict],
) -> str:
    """Render markdown tables grouped by tier, sorted cheapest-by-OpenRouter first."""
    canonical_models = canonical_doc.get("canonical_models", [])
    # Index: (canonical, unit, provider_id) -> (price, method)
    matrix: dict[tuple[str, str, str], tuple[float, str]] = {}
    for rec in records:
        cm = rec.get("canonical_model")
        if not cm:
            continue
        key = (cm, rec["unit"], rec["provider_id"])
        method = rec.get("method", "json-api")
        # Prefer fetched (json-api) over manual when both exist for the same cell.
        prev = matrix.get(key)
        if prev is None or (prev[1] == "manual" and method != "manual"):
            matrix[key] = (rec["price_usd"], method)

    providers_in_use = _provider_column_order(matrix)
    provider_names = _load_provider_display_names()
    has_manual = any(m == "manual" for (_, m) in matrix.values())

    def render_row(model: dict, unit: str) -> str:
        cells = [f"`{model['canonical']}`"]
        or_entry = matrix.get((model["canonical"], unit, "openrouter"))
        or_price = or_entry[0] if or_entry else None
        for pid in providers_in_use:
            entry = matrix.get((model["canonical"], unit, pid))
            if entry is None:
                cells.append("—")
                continue
            price, method = entry
            cell = _format_price(price)
            if pid != "openrouter" and or_price and price < or_price * 0.5:
                cell += " ⚠"
            if method == "manual":
                cell += " †"
            cells.append(cell)
        return "| " + " | ".join(cells) + " |"

    def row_sort_key(model: dict, unit: str) -> float:
        entry = matrix.get((model["canonical"], unit, "openrouter"))
        if entry is not None:
            return entry[0]
        # Fallback: cheapest available across providers
        prices = [v[0] for (cm, u, _pid), v in matrix.items() if cm == model["canonical"] and u == unit]
        return min(prices) if prices else float("inf")

    def render_tier_table(tier: int, unit: str, header_suffix: str) -> str:
        models_in_tier = [
            m for m in canonical_models
            if m.get("tier") == tier
            and any(k[0] == m["canonical"] and k[1] == unit for k in matrix)
        ]
        # Sort cheapest-by-OpenRouter first within each tier.
        models_in_tier.sort(key=lambda m: row_sort_key(m, unit))
        rows = [render_row(model, unit) for model in models_in_tier]
        if not rows:
            return ""
        header = (
            "| Model | "
            + " | ".join(provider_names.get(p, p) for p in providers_in_use)
            + " |"
        )
        align = "|---" * (1 + len(providers_in_use)) + "|"
        title = {
            1: "### Tier 1 — cheapest viable (routine, batch summaries)",
            2: "### Tier 2 — daily driver (agent, coding)",
            3: "### Tier 3 — top frontier (hardest problems)",
            4: "### Tier 4 — multimodal (different units, can't compare to text)",
        }[tier]
        return (
            f"{title} — {header_suffix}\n\n"
            + header
            + "\n"
            + align
            + "\n"
            + "\n".join(rows)
            + "\n"
        )

    chunks = []
    for tier in (1, 2, 3):
        chunk = render_tier_table(tier, "per_1m_input_tokens", "USD per 1M input tokens")
        if chunk:
            chunks.append(chunk)
    # Tier 4: render per-unit rows individually because each multimodal model has its own unit.
    tier4_models = [m for m in canonical_models if m.get("tier") == 4]
    if tier4_models:
        rows = []
        for model in tier4_models:
            cm = model["canonical"]
            units_seen = sorted({k[1] for k in matrix if k[0] == cm})
            for unit in units_seen:
                pretty_unit = {
                    "per_second": "USD per second",
                    "per_image": "USD per image",
                    "per_request": "USD per request",
                    "per_1m_input_tokens": "USD per 1M input tokens",
                    "per_1m_output_tokens": "USD per 1M output tokens",
                    "per_1m_input_cache_read_tokens": "USD per 1M cache-read tokens",
                }.get(unit, unit)
                cells = [f"`{cm}`", pretty_unit]
                for pid in providers_in_use:
                    entry = matrix.get((cm, unit, pid))
                    if entry is None:
                        cells.append("—")
                    else:
                        price, method = entry
                        cell = _format_price(price)
                        if method == "manual":
                            cell += " †"
                        cells.append(cell)
                rows.append("| " + " | ".join(cells) + " |")
        if rows:
            header = (
                "| Model | Unit | "
                + " | ".join(provider_names.get(p, p) for p in providers_in_use)
                + " |"
            )
            align = "|---" * (2 + len(providers_in_use)) + "|"
            chunks.append(
                "### Tier 4 — multimodal (different units, can't compare to text)\n\n"
                + header
                + "\n"
                + align
                + "\n"
                + "\n".join(rows)
                + "\n"
            )

    snapshot_count = len(records)
    manual_note = (
        " † = community-submitted, verified by maintainer (see issue template)."
        if has_manual else ""
    )
    topup_bits = []
    for pid, rate in topup_rates.items():
        if pid not in providers_in_use:
            continue
        label = provider_names.get(pid, pid)
        topup_bits.append(
            f"{label} ×{rate['multiplier']:.3f} "
            f"({rate['amount']} {rate['currency']} per $1 quota, "
            f"site FX {rate['fx_per_usd']}, checked {rate['checked']})"
        )
    topup_note = (
        " Top-up effective USD (`effective_price_usd` = quota USD × multiplier): "
        + "; ".join(topup_bits) + "."
        if topup_bits else ""
    )
    placeholder_note = (
        f" Excluded {excluded_placeholder_count} unset placeholder prices "
        f"(new-api model_ratio 37.5 with no billing expression)."
        if excluded_placeholder_count else ""
    )
    intro = (
        f"_Snapshot date: **{snapshot_date}**. {snapshot_count} price records across "
        f"{len(providers_in_use)} providers. **Reference column** is OpenRouter "
        f"(officially-authorized, ~5% markup). Rows sorted cheapest-by-OpenRouter first. "
        f"Figures are quota USD after the public group ratio "
        f"(default group, else the cheapest positive group — see "
        f"[methodology](docs/methodology.md)). "
        f"⚠ = relay quotes <50% of OpenRouter — verify with "
        f"[canary prompts](docs/canary-prompts.md) before trusting."
        f"{topup_note}{placeholder_note}{manual_note}_\n\n"
        f"#### Six indicator models, {len(providers_in_use)} providers, one snapshot\n\n"
        f"**Absolute prices — tier ladder (input)** · ▼ marks the cheapest provider per model\n\n"
        f"![Tier-ladder input pricing](assets/charts/tier-ladder-input.svg)\n\n"
        f"**Price spread per model (input)** · how much variance exists between providers\n\n"
        f"![Spread range input](assets/charts/spread-range-input.svg)\n\n"
        f"**Savings vs OpenRouter (input)** · how much cheaper (or pricier) each relay is\n\n"
        f"![Savings vs OpenRouter input](assets/charts/savings-vs-ref-input.svg)\n\n"
        f"_Output-token equivalents and the full-matrix heatmap: "
        f"[`assets/charts/`](assets/charts/) "
        f"([tier-ladder-output](assets/charts/tier-ladder-output.svg), "
        f"[spread-range-output](assets/charts/spread-range-output.svg), "
        f"[savings-vs-ref-output](assets/charts/savings-vs-ref-output.svg), "
        f"[spread-heatmap-input](assets/charts/spread-heatmap-input.svg)). "
        f"Interactive dashboard: <https://howardpen9.github.io/awesome-ai-api-proxy/>._\n\n"
    )
    outro = (
        "\n_Full per-model breakdown (including non-canonical models): "
        "[`docs/prices.md`](docs/prices.md). "
        "Raw snapshots: [`data/snapshots/`](data/snapshots/). "
        "Machine-readable: [`data/prices.latest.json`](data/prices.latest.json)._\n"
    )
    return intro + "\n".join(chunks) + outro


def _update_readme(readme_path: Path, body: str) -> bool:
    if not readme_path.exists():
        return False
    text = readme_path.read_text(encoding="utf-8")
    if START_MARKER not in text or END_MARKER not in text:
        return False
    start = text.index(START_MARKER) + len(START_MARKER)
    end = text.index(END_MARKER)
    new_text = text[:start] + "\n" + body + "\n" + text[end:]
    readme_path.write_text(new_text, encoding="utf-8")
    return True


def _cell_money(value: object) -> str:
    if not isinstance(value, (int, float)):
        return "—"
    return _format_price(float(value))


def _build_full_doc(
    records: list[dict],
    snapshot_date: str,
    *,
    excluded_placeholder_count: int,
    topup_rates: dict[str, dict],
) -> str:
    """docs/prices.md — every published model, sorted by provider then model."""
    by_provider: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_provider[rec["provider_id"]].append(rec)

    lines = [
        "# Full price snapshot",
        "",
        f"_Generated from `data/snapshots/{snapshot_date}/` by `scripts/build_prices.py`._  ",
        f"_Snapshot date: **{snapshot_date}**. Machine-readable source: [`data/prices.latest.json`](../data/prices.latest.json)._",
        "",
        "For the curated tier-ladder comparison, see the README. This page is the full dump of published prices. "
        "Unset placeholder rows (new-api `model_ratio` 37.5 with no billing expression) are excluded. "
        "How group ratios, billing expressions, and top-up rates are applied: "
        "[`methodology.md`](methodology.md).",
        "",
    ]
    if excluded_placeholder_count:
        lines.append(f"Excluded placeholder prices: **{excluded_placeholder_count}**.")
        lines.append("")
    if topup_rates:
        lines.append("Top-up multipliers (quota USD → effective USD), from `providers.yaml` `topup_rate`:")
        lines.append("")
        for pid, rate in topup_rates.items():
            lines.append(
                f"- `{pid}`: ×{rate['multiplier']:.3f} "
                f"({rate['amount']} {rate['currency']} per $1 of quota, "
                f"site FX {rate['fx_per_usd']}, checked {rate['checked']}, "
                f"<{rate['source_url']}>)"
            )
        lines.append("")
    for pid in sorted(by_provider):
        recs = by_provider[pid]
        provider_name = recs[0]["provider_name"]
        source = recs[0]["source_url"]
        lines.append(f"## {provider_name} — `{pid}`")
        lines.append("")
        lines.append(f"Source: <{source}> · Records: {len(recs)}")
        lines.append("")
        lines.append(
            "| Model | Canonical | Unit | Price (USD) | List (USD) | Group | Ratio | Effective (USD) |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for rec in sorted(recs, key=lambda r: (r["raw_model_name"], r["unit"])):
            ratio = rec.get("group_ratio")
            ratio_cell = f"{ratio:g}" if isinstance(ratio, (int, float)) else "—"
            group = rec.get("pricing_group") or "—"
            lines.append(
                "| `{model}` | {canon} | {unit} | {price} | {list_price} | {group} | {ratio} | {effective} |".format(
                    model=rec["raw_model_name"],
                    canon=f"`{rec['canonical_model']}`" if rec.get("canonical_model") else "—",
                    unit=rec["unit"],
                    price=_format_price(rec["price_usd"]),
                    list_price=_cell_money(rec.get("list_price_usd")),
                    group=group.replace("|", "\\|"),
                    ratio=ratio_cell,
                    effective=_cell_money(rec.get("effective_price_usd")),
                )
            )
        lines.append("")
    return "\n".join(lines)


def _publish_pages_index(
    records: list[dict],
    snapshot_date: str,
    *,
    excluded_placeholder_count: int,
) -> None:
    """GitHub Pages serves docs/. Root llms.txt is not on that host."""
    if LLMS_TXT.exists():
        DOCS_LLMS_TXT.write_text(LLMS_TXT.read_text(encoding="utf-8"), encoding="utf-8")
    index = {
        "name": "awesome-ai-api-proxy",
        "description": "Weekly AI API relay and LLM gateway price observatory.",
        "snapshot_date": snapshot_date,
        "record_count": len(records),
        "excluded_placeholder_count": excluded_placeholder_count,
        "prices": {
            "github_raw": f"{GITHUB_RAW}/data/prices.latest.json",
            "github_blob": "https://github.com/howardpen9/awesome-ai-api-proxy/blob/main/data/prices.latest.json",
        },
        "llms_txt": f"{PAGES_ORIGIN}/llms.txt",
        "methodology": f"{GITHUB_RAW}/docs/methodology.md",
        "providers": f"{GITHUB_RAW}/data/providers.yaml",
        "mcp": {
            "package": "awesome-ai-api-proxy-mcp",
            "registry_name": "io.github.howardpen9/awesome-ai-api-proxy",
            "server_json": f"{GITHUB_RAW}/mcp/server.json",
        },
    }
    PRICES_INDEX.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    snapshot_dir = _latest_snapshot_dir()
    snapshot_date = snapshot_dir.name
    console.rule(f"[bold]Building prices from {snapshot_dir}")

    canonical_doc = _load_canonical()
    alias_index = _build_alias_index(canonical_doc)
    console.print(f"canonical aliases indexed: {len(alias_index)}")

    records = _load_snapshots(snapshot_dir)
    submitted = _load_submitted_prices()
    console.print(f"records loaded: {len(records)} fetched + {len(submitted)} submitted")
    if not records and not submitted:
        console.print("[red]No records to compile.[/red]")
        return 1

    records = _resolve_canonical(records, alias_index)
    # submitted records already carry canonical_model; just resolve tier/family by lookup
    for sp in submitted:
        entry = alias_index.get((sp.get("canonical_model") or "").lower())
        if entry:
            sp["model_family"] = entry.get("family")
            sp["tier"] = entry.get("tier")
    records = records + submitted
    inactive_ids = inactive_fetcher_ids()
    records, excluded_placeholders = records_for_current_build(records, inactive_ids)
    if inactive_ids:
        console.print(f"inactive fetchers omitted from current prices: {sorted(inactive_ids)}")
    if excluded_placeholders:
        console.print(f"excluded placeholder prices: {excluded_placeholders}")
    rates = load_topup_rates()
    annotate_effective(records, rates)
    topup_rates = _topup_summary(rates)
    matched = sum(1 for r in records if r.get("canonical_model"))
    console.print(f"records resolved to a canonical model: {matched}/{len(records)}")

    _write_prices_latest(
        records,
        snapshot_date,
        excluded_placeholder_count=excluded_placeholders,
        topup_rates=topup_rates,
    )
    console.print(f"[green]wrote[/green] {PRICES_LATEST.relative_to(SNAPSHOTS_DIR.parent.parent)}")

    tabular = _write_tabular_exports(records, snapshot_date)
    if tabular:
        csv_path, parquet_path = tabular
        console.print(f"[green]wrote[/green] {csv_path.relative_to(SNAPSHOTS_DIR.parent.parent)}")
        console.print(f"[green]wrote[/green] {parquet_path.relative_to(SNAPSHOTS_DIR.parent.parent)}")

    _append_history(records, snapshot_date)
    console.print(f"[green]appended[/green] {PRICES_HISTORY.relative_to(SNAPSHOTS_DIR.parent.parent)}")

    table_md = _build_tier_tables(
        records,
        canonical_doc,
        snapshot_date,
        excluded_placeholder_count=excluded_placeholders,
        topup_rates=topup_rates,
    )
    updated = []
    for readme in READMES:
        if _update_readme(readme, table_md):
            updated.append(readme.name)
    console.print(f"[green]updated[/green] READMEs with markers: {updated or '(none — add markers first)'}")

    PRICES_DOC.parent.mkdir(parents=True, exist_ok=True)
    PRICES_DOC.write_text(
        _build_full_doc(
            records,
            snapshot_date,
            excluded_placeholder_count=excluded_placeholders,
            topup_rates=topup_rates,
        )
        + "\n",
        encoding="utf-8",
    )
    console.print(f"[green]wrote[/green] {PRICES_DOC.relative_to(SNAPSHOTS_DIR.parent.parent)}")
    _publish_pages_index(
        records,
        snapshot_date,
        excluded_placeholder_count=excluded_placeholders,
    )
    console.print(f"[green]wrote[/green] {DOCS_LLMS_TXT.relative_to(SNAPSHOTS_DIR.parent.parent)}")
    console.print(f"[green]wrote[/green] {PRICES_INDEX.relative_to(SNAPSHOTS_DIR.parent.parent)}")

    console.rule()
    console.print("[bold green]Done.[/bold green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
