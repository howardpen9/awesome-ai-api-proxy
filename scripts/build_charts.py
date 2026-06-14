"""Generate SVG charts from data/prices.latest.json.

Output goes to assets/charts/*.svg. Charts are embedded in the README between
the price-table markers so readers see the cost spread at a glance.

Run after `python -m scripts.build_prices`. Idempotent — overwrites existing SVGs.

Design intent (v1.6):
    * Show every provider we have data for, not a hand-picked 3.
    * Curate ~6 *indicator* canonical models that span tiers 1-3 and that most
      providers actually carry. This is the headline comparison.
    * Per chart, tell ONE story:
        - tier-ladder       -> absolute $ per 1M tokens, log scale
        - spread-range      -> min-to-max spread per model, with the cheapest
                               provider labelled (so users see who wins)
        - savings-vs-ref    -> % cheaper/expensive vs OpenRouter (the "clean"
                               reference). The marketing story for relays.
        - spread-heatmap    -> full matrix view for the curious
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # No display needed; SVG output only.
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.colors import LogNorm
from rich.console import Console

from ._paths import CANONICAL_YAML, PRICES_LATEST, REPO_ROOT

console = Console()

CHARTS_DIR = REPO_ROOT / "assets" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Provider palette + display order. OpenRouter sits left as the reference;
# global gateways next; Chinese-market relays after. Edit here when a new
# fetcher lands -- everything else derives.
# ---------------------------------------------------------------------------

PROVIDERS = [
    ("openrouter",   "OpenRouter (ref)", "#7c3aed"),
    ("xai_official", "xAI (official)",   "#64748b"),
    ("atlascloud",   "Atlas Cloud",      "#0ea5e9"),
    ("unorouter",    "UnoRouter",        "#f59e0b"),
    ("relaydance",   "Relaydance",       "#10b981"),
    ("uiuiapi",      "UiUiAPI",          "#ec4899"),
    ("bltcy",        "bltcy",            "#ef4444"),
]
PROVIDER_COLORS = {pid: color for pid, _, color in PROVIDERS}
PROVIDER_LABELS = {pid: label for pid, label, _ in PROVIDERS}
PROVIDER_ORDER = [pid for pid, _, _ in PROVIDERS]
REFERENCE_PID = "openrouter"


# ---------------------------------------------------------------------------
# Indicator models. Hand-picked to span tiers and to have multi-provider
# coverage. Order = left-to-right on the x axis (cheap -> expensive).
# ---------------------------------------------------------------------------

INDICATOR_MODELS = [
    "deepseek-v3",        # T1
    "deepseek-r1",        # T1 reasoning
    "gemini-3-flash",     # T2
    "gpt-5.4",            # T2
    "claude-sonnet-4.6",  # T2
    "grok-4.3",           # T3
]


def _load() -> tuple[dict, list[dict]]:
    prices = json.loads(PRICES_LATEST.read_text(encoding="utf-8"))
    canonical = yaml.safe_load(CANONICAL_YAML.read_text(encoding="utf-8")).get(
        "canonical_models", []
    )
    return prices, canonical


def _matrix(records: list[dict], unit: str) -> dict[tuple[str, str], float]:
    """Index price by (canonical_model, provider_id) for one unit."""
    out: dict[tuple[str, str], float] = {}
    for rec in records:
        cm = rec.get("canonical_model")
        if not cm or rec.get("unit") != unit:
            continue
        out.setdefault((cm, rec["provider_id"]), rec["price_usd"])
    return out


def _fmt(price: float) -> str:
    if price >= 100:
        return f"${price:.0f}"
    if price >= 1:
        return f"${price:.2f}"
    return f"${price:.3f}"


def _stamp(ax, prices_doc: dict) -> None:
    snapshot_date = prices_doc.get("snapshot_date", "")
    record_count = len(prices_doc.get("records", []))
    ax.text(
        1.0, -0.16,
        f"snapshot {snapshot_date}  ·  {record_count} records across {len(PROVIDERS)} providers  ·  "
        "awesome-ai-api-proxy",
        ha="right", va="top",
        transform=ax.transAxes,
        fontsize=7.5, color="#999",
    )


# ---------------------------------------------------------------------------
# Chart 1: tier-ladder — absolute $ per 1M tokens, grouped bars by provider
# ---------------------------------------------------------------------------


def chart_tier_ladder(prices_doc: dict, canonical: list[dict], unit: str, kind: str) -> Path:
    records = prices_doc["records"]
    matrix = _matrix(records, unit)

    models = [m for m in canonical if m["canonical"] in INDICATOR_MODELS]
    models.sort(key=lambda m: INDICATOR_MODELS.index(m["canonical"]))
    providers = [p for p in PROVIDER_ORDER if any(k[1] == p for k in matrix)]
    if not models or not providers:
        console.print(f"[yellow]no data for unit={unit}; skip[/yellow]")
        return CHARTS_DIR / f"tier-ladder-{kind}.svg"

    fig, ax = plt.subplots(figsize=(14, 6), dpi=110)
    n_models = len(models)
    n_providers = len(providers)
    bar_width = 0.82 / n_providers
    x = np.arange(n_models)

    for i, pid in enumerate(providers):
        heights = [matrix.get((m["canonical"], pid)) for m in models]
        plot_heights = [h if h is not None else 0 for h in heights]
        offset = (i - (n_providers - 1) / 2) * bar_width
        bars = ax.bar(
            x + offset,
            plot_heights,
            bar_width,
            label=PROVIDER_LABELS.get(pid, pid),
            color=PROVIDER_COLORS.get(pid, "#888"),
            edgecolor="white",
            linewidth=0.5,
        )
        for bar, h in zip(bars, heights):
            if h is None:
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.06,
                _fmt(h),
                ha="center", va="bottom",
                fontsize=6.8, color="#555",
                rotation=0,
            )

    # Highlight the cheapest provider for each model with a small star marker.
    for j, m in enumerate(models):
        observations = [(p, matrix.get((m["canonical"], p))) for p in providers]
        observations = [(p, v) for p, v in observations if v is not None]
        if not observations:
            continue
        cheapest_pid, cheapest_v = min(observations, key=lambda t: t[1])
        cheapest_i = providers.index(cheapest_pid)
        offset = (cheapest_i - (n_providers - 1) / 2) * bar_width
        ax.scatter(
            j + offset, cheapest_v * 1.45,
            marker="v", color="#16a34a", s=42, zorder=5,
            edgecolors="white", linewidths=0.8,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        [m["canonical"] for m in models],
        rotation=20, ha="right", fontsize=10,
    )
    ax.set_yscale("log")
    ax.set_ylabel(
        f"USD per 1M {kind} tokens (log scale)", fontsize=10,
    )
    ax.set_title(
        f"Cost-tier ladder — {kind} pricing across {len(providers)} providers"
        f"  ·  ▼ = cheapest per model",
        fontsize=11.5, pad=14,
    )
    ax.legend(
        loc="upper left", fontsize=8.5, frameon=False, ncol=3,
        bbox_to_anchor=(0, 1.0),
    )
    ax.grid(axis="y", linestyle=":", linewidth=0.5, color="#ccc")
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    _stamp(ax, prices_doc)
    plt.tight_layout()

    out = CHARTS_DIR / f"tier-ladder-{kind}.svg"
    plt.savefig(out, format="svg", bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Chart 2: spread-range — min/max horizontal bar per model
# ---------------------------------------------------------------------------


def chart_spread_range(prices_doc: dict, canonical: list[dict], unit: str, kind: str) -> Path:
    records = prices_doc["records"]
    matrix = _matrix(records, unit)

    models = [m for m in canonical if m["canonical"] in INDICATOR_MODELS]
    models.sort(key=lambda m: INDICATOR_MODELS.index(m["canonical"]))
    if not models:
        return CHARTS_DIR / f"spread-range-{kind}.svg"

    fig, ax = plt.subplots(figsize=(12, 5.6), dpi=110)

    y_positions = np.arange(len(models))
    for j, m in enumerate(models):
        obs = [
            (p, matrix.get((m["canonical"], p)))
            for p in PROVIDER_ORDER
            if matrix.get((m["canonical"], p)) is not None
        ]
        if not obs:
            continue
        cheapest_pid, cheapest_v = min(obs, key=lambda t: t[1])
        priciest_pid, priciest_v = max(obs, key=lambda t: t[1])
        spread = priciest_v / cheapest_v if cheapest_v > 0 else 1

        # The grey range line.
        ax.hlines(
            y=j, xmin=cheapest_v, xmax=priciest_v,
            color="#d1d5db", linewidth=3, zorder=1,
        )
        # Per-provider dots on the range.
        for pid, v in obs:
            ax.scatter(
                v, j,
                s=110,
                color=PROVIDER_COLORS.get(pid, "#888"),
                edgecolors="white",
                linewidths=1.2,
                zorder=3,
                label=PROVIDER_LABELS.get(pid, pid),
            )
        # Cheapest label sits ABOVE the dot (y-0.28); priciest sits BELOW (y+0.28)
        # so they never collide even when the spread is tiny.
        ax.text(
            cheapest_v, j - 0.28,
            f"{_fmt(cheapest_v)} · {PROVIDER_LABELS.get(cheapest_pid, cheapest_pid)}",
            ha="center", va="bottom",
            fontsize=8, color=PROVIDER_COLORS.get(cheapest_pid, "#333"),
            fontweight="bold",
        )
        if priciest_pid != cheapest_pid:
            ax.text(
                priciest_v, j + 0.28,
                f"{_fmt(priciest_v)} · {PROVIDER_LABELS.get(priciest_pid, priciest_pid)}",
                ha="center", va="top",
                fontsize=8, color=PROVIDER_COLORS.get(priciest_pid, "#333"),
            )
            # Spread multiplier sits to the right of the priciest dot.
            ax.text(
                priciest_v * 1.22, j,
                f"{spread:.1f}× spread",
                ha="left", va="center",
                fontsize=7.8, color="#6b7280",
            )

    ax.set_xscale("log")
    ax.set_yticks(y_positions)
    ax.set_yticklabels([m["canonical"] for m in models], fontsize=10)
    ax.set_ylim(len(models) - 0.5, -0.5)
    ax.set_xlabel(f"USD per 1M {kind} tokens (log)", fontsize=10)
    ax.set_title(
        f"Price spread per model — cheapest vs priciest provider, {kind} pricing\n"
        f"colored labels = which provider sits at each end of the range",
        fontsize=11, pad=12,
    )
    # No legend — the bold colored labels on each row identify the providers.
    ax.grid(axis="x", linestyle=":", linewidth=0.5, color="#ccc")
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(left=False)
    _stamp(ax, prices_doc)
    plt.tight_layout()

    out = CHARTS_DIR / f"spread-range-{kind}.svg"
    plt.savefig(out, format="svg", bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Chart 3: savings-vs-ref — % cheaper/more-expensive vs OpenRouter
# ---------------------------------------------------------------------------


def chart_savings_vs_ref(prices_doc: dict, canonical: list[dict], unit: str, kind: str) -> Path:
    """Delta heatmap: rows=indicator models, cols=non-ref providers, color=%
    cheaper (green) or more expensive (red) vs OpenRouter. Empty cells are "—".

    A heatmap suits this dataset because most providers match OpenRouter at the
    premium tier ($0 delta), so a bar chart wastes 60% of its area on zero-length
    bars. The grid stays compact and reads at a glance.
    """
    records = prices_doc["records"]
    matrix = _matrix(records, unit)

    models = [m for m in canonical if m["canonical"] in INDICATOR_MODELS]
    models.sort(key=lambda m: INDICATOR_MODELS.index(m["canonical"]))
    providers = [p for p in PROVIDER_ORDER if p != REFERENCE_PID and any(k[1] == p for k in matrix)]
    if not models or not providers:
        return CHARTS_DIR / f"savings-vs-ref-{kind}.svg"

    n_models = len(models)
    n_providers = len(providers)

    grid = np.full((n_models, n_providers), np.nan)
    for i, m in enumerate(models):
        ref = matrix.get((m["canonical"], REFERENCE_PID))
        if ref is None or ref <= 0:
            continue
        for j, pid in enumerate(providers):
            v = matrix.get((m["canonical"], pid))
            if v is not None:
                grid[i, j] = (ref - v) / ref * 100

    fig, ax = plt.subplots(figsize=(9.5, max(3.5, 0.55 * n_models + 2.0)), dpi=110)

    # Diverging colormap: red = more expensive than OpenRouter, green = cheaper.
    # Cap at ±100% for color saturation so a -899% outlier doesn't crush the
    # contrast in the ±50% range we actually care about.
    cmap = plt.cm.RdYlGn
    cmap.set_bad(color="#f3f4f6")
    masked = np.ma.masked_invalid(grid)
    im = ax.imshow(
        masked,
        aspect="auto",
        cmap=cmap,
        vmin=-100, vmax=100,
    )

    for i in range(n_models):
        for j in range(n_providers):
            v = grid[i, j]
            if np.isnan(v):
                ax.text(j, i, "—", ha="center", va="center", fontsize=11, color="#9ca3af")
            elif abs(v) < 5:
                ax.text(j, i, "≈0%", ha="center", va="center", fontsize=9, color="#374151")
            else:
                # Format big negatives compactly (e.g. -900%) so they fit.
                if v <= -1000:
                    txt = "≤-1000%"
                elif abs(v) >= 100:
                    txt = f"{v:+.0f}%"
                else:
                    txt = f"{v:+.0f}%"
                color = "white" if abs(v) > 60 else "#1f2937"
                ax.text(j, i, txt, ha="center", va="center", fontsize=9.5, color=color, fontweight="bold")

    ax.set_xticks(np.arange(n_providers))
    ax.set_xticklabels(
        [PROVIDER_LABELS.get(p, p) for p in providers],
        fontsize=9.5, rotation=20, ha="right",
    )
    ax.set_yticks(np.arange(n_models))
    ax.set_yticklabels([m["canonical"] for m in models], fontsize=10)
    ax.set_title(
        f"Price delta vs OpenRouter — {kind} pricing\n"
        f"green = cheaper than OpenRouter · red = more expensive · ≈0% = at parity · — = no data",
        fontsize=10.5, pad=12,
    )

    cbar = plt.colorbar(im, ax=ax, shrink=0.55, pad=0.02)
    cbar.set_label("% cheaper than OpenRouter (clamped ±100)", fontsize=8.5)
    cbar.ax.tick_params(labelsize=7.5)

    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    _stamp(ax, prices_doc)
    plt.tight_layout()

    out = CHARTS_DIR / f"savings-vs-ref-{kind}.svg"
    plt.savefig(out, format="svg", bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Chart 4: spread heatmap — full matrix of canonical models × all providers
# ---------------------------------------------------------------------------


def chart_spread_heatmap(prices_doc: dict, canonical: list[dict], unit: str, kind: str) -> Path:
    records = prices_doc["records"]
    matrix = _matrix(records, unit)

    models = [m for m in canonical if any(k[0] == m["canonical"] for k in matrix)]
    models.sort(key=lambda m: (m.get("tier", 99), m["canonical"]))
    providers = [p for p in PROVIDER_ORDER if any(k[1] == p for k in matrix)]
    if not models or not providers:
        return CHARTS_DIR / f"spread-heatmap-{kind}.svg"

    grid = np.full((len(models), len(providers)), np.nan)
    for i, m in enumerate(models):
        for j, p in enumerate(providers):
            v = matrix.get((m["canonical"], p))
            if v is not None:
                grid[i, j] = v

    fig, ax = plt.subplots(figsize=(8, max(3.5, 0.5 * len(models) + 1.5)), dpi=110)
    masked = np.ma.masked_invalid(grid)
    cmap = plt.cm.viridis_r
    cmap.set_bad(color="#f3f4f6")

    vmin = max(np.nanmin(grid), 1e-3)
    vmax = np.nanmax(grid)
    im = ax.imshow(masked, aspect="auto", cmap=cmap, norm=LogNorm(vmin=vmin, vmax=vmax))

    for i in range(len(models)):
        for j in range(len(providers)):
            v = grid[i, j]
            if not np.isnan(v):
                color = "white" if v > vmin * 30 else "#222"
                ax.text(j, i, _fmt(v), ha="center", va="center", fontsize=8.5, color=color)
            else:
                ax.text(j, i, "—", ha="center", va="center", fontsize=10, color="#9ca3af")

    ax.set_xticks(np.arange(len(providers)))
    ax.set_xticklabels(
        [PROVIDER_LABELS.get(p, p) for p in providers],
        fontsize=9, rotation=20, ha="right",
    )
    ax.set_yticks(np.arange(len(models)))
    ax.set_yticklabels(
        [f"T{m.get('tier', '?')}  {m['canonical']}" for m in models],
        fontsize=9,
    )
    ax.set_title(
        f"Full matrix — every canonical model × every provider, {kind} pricing",
        fontsize=10.8, pad=10,
    )

    cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label(f"USD per 1M {kind} tokens (log)", fontsize=8.5)
    cbar.ax.tick_params(labelsize=7.5)

    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    _stamp(ax, prices_doc)
    plt.tight_layout()

    out = CHARTS_DIR / f"spread-heatmap-{kind}.svg"
    plt.savefig(out, format="svg", bbox_inches="tight")
    plt.close(fig)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    prices_doc, canonical = _load()
    written: list[Path] = []
    for unit, kind in (
        ("per_1m_input_tokens", "input"),
        ("per_1m_output_tokens", "output"),
    ):
        written += [
            chart_tier_ladder(prices_doc, canonical, unit, kind),
            chart_spread_range(prices_doc, canonical, unit, kind),
            chart_savings_vs_ref(prices_doc, canonical, unit, kind),
            chart_spread_heatmap(prices_doc, canonical, unit, kind),
        ]
    console.rule("[bold green]Charts built")
    for p in written:
        console.print(f"  {p.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
