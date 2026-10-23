import json, os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "otpi_vs_relays.json")))
rows, labs, meta = D["models"], D["lab_level"], D["meta"]
LABC = {"anthropic": "#c2410c", "openai": "#0f766e", "google": "#1d4ed8", "deepseek": "#6d28d9"}
fig = plt.figure(figsize=(14, 11), dpi=150)
gs = fig.add_gridspec(2, 2, height_ratios=[2.6, 1], hspace=0.32, wspace=0.08, left=0.17, right=0.98, top=0.865, bottom=0.135)
ys = list(range(len(rows)))[::-1]
for col, side in enumerate(["in", "out"]):
    ax = fig.add_subplot(gs[0, col])
    for y, r in zip(ys, rows):
        c = LABC[r["provider"]]
        ax.plot([r[f"relay_min_{side}"], r[f"relay_max_{side}"]], [y, y], color=c, alpha=0.35, lw=6, solid_capstyle="round")
        ax.scatter(r[f"ref_{side}"], y, marker="|", s=320, color="black", lw=2.2, zorder=4)
        ax.scatter(r[f"relay_median_{side}"], y, marker="o", s=55, color=c, zorder=5)
        ax.scatter(r[f"relay_median_{side}_topup_adj"], y, marker="D", s=40, facecolor="white", edgecolor=c, lw=1.6, zorder=6)
        sp = r[f"spread_{side}_pct_topup_adj"]
        ax.annotate(f"{sp:+.0f}%", (max(r[f"relay_max_{side}"], r[f"ref_{side}"]), y), xytext=(8, -3), textcoords="offset points", fontsize=8, color="#444")
    ax.set_xscale("log"); ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r['model']}  (n={r['n_relays']})" for r in rows] if col == 0 else [], fontsize=9)
    if col == 0:
        for t, r in zip(ax.get_yticklabels(), rows): t.set_color(LABC[r["provider"]])
    ax.set_title(f"{'Input' if side=='in' else 'Output'} price, USD per 1M tokens (log)", fontsize=11)
    ax.grid(axis="x", which="both", alpha=0.25)
    ax.set_xlim(0.03, 120 if side == "out" else 30)
leg = [Line2D([], [], color="black", marker="|", ls="", ms=14, mew=2.2, label="OpenRouter posted price (reference)"),
       Line2D([], [], color="grey", marker="o", ls="", label="Relay median, as listed (USD-labeled)"),
       Line2D([], [], color="grey", marker="D", ls="", mfc="white", label="Relay median, adjusted for published top-up rate"),
       Line2D([], [], color="grey", lw=6, alpha=0.35, label="Relay min–max (as listed)")]
fig.legend(handles=leg, loc="upper center", ncol=4, fontsize=9, frameon=False, bbox_to_anchor=(0.575, 0.935))
fig.text(0.98, 0.895, "% = top-up-adjusted relay median vs reference", ha="right", fontsize=8, color="#444")
ax = fig.add_subplot(gs[1, :])
import numpy as np
x = np.arange(len(labs)); w = 0.26
b1 = ax.bar(x - w, [l["otpi"] for l in labs], w, color="#111827", label=f"Ornn OTPI (lab blended, {labs[0]['otpi_date']})")
b2 = ax.bar(x, [l["implied_relay_index_listed"] for l in labs], w, color="#9ca3af", label="Relay-implied index, as listed")
b3 = ax.bar(x + w, [l["implied_relay_index_topup_adj"] for l in labs], w, color="white", edgecolor="#374151", hatch="//", label="Relay-implied index, top-up adjusted")
for bars in (b1, b2, b3):
    for b in bars: ax.annotate(f"${b.get_height():.3f}", (b.get_x() + b.get_width()/2, b.get_height()), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=8)
for i, l in enumerate(labs):
    ax.annotate(f"{l['spread_vs_otpi_pct_topup_adj']:+.0f}% vs OTPI", (x[i] + w, l["implied_relay_index_topup_adj"]), xytext=(0, 14), textcoords="offset points", ha="center", fontsize=8, color="#b91c1c")
ax.set_xticks(x); ax.set_xticklabels([{"anthropic":"Anthropic","openai":"OpenAI","google":"Google","deepseek":"DeepSeek"}[l["lab"]] for l in labs], fontsize=10)
ax.set_ylabel("USD / 1M tokens (blended)"); ax.set_ylim(0, max(l["implied_relay_index_listed"] for l in labs) * 1.45)
ax.set_title("Lab level: OTPI vs relay-implied index  (= OTPI × median relay/reference price ratio across the lab's models above)", fontsize=10.5)
ax.legend(fontsize=8.5, frameon=False, loc="upper right"); ax.grid(axis="y", alpha=0.25)
fig.suptitle("China/SEA relay prices vs OTPI per MTok", fontsize=17, fontweight="bold", x=0.57, y=0.975)
o, rs = meta["otpi"], meta["relay_snapshot"]
foot = (f"Sources: Ornn Token Price Index, api.ornnai.com/api/otpi (free tier; settlement date {o['settlement_date']}, fetched {o['fetched_at_utc']}). "
        f"Relay + OpenRouter prices: github.com/howardpen9/awesome-ai-api-proxy data/prices.latest.json, snapshot {rs['snapshot_date']} (commit {rs['commit'][:7]}).\n"
        f"Relays: {', '.join(meta['relay_set'])} (n per model shown; several operator-submitted/unverified). Excluded: bltcy (announced shutdown 2026-05-01), placeholder prices ($75/M new-api default). "
        f"Top-up adjustment uses each relay's public /api/status 'price' (CNY per 1 USD of quota)\nand USD/CNY {meta['fx']['USD_CNY']:.4f} (open.er-api.com, fetched 2026-10-23). "
        "OTPI is a lab-level volume-weighted blend with no input/output split, so per-model rows compare against OpenRouter's posted price. Default/listed group ratios only; account-pool groups flagged. "
        "Regional price discovery, not a recommendation.")
import textwrap
foot = "\n".join(textwrap.wrap(foot.replace("\n", " "), 210))
fig.text(0.01, 0.012, foot, fontsize=7, color="#374151", va="bottom")
for ext in ("png", "svg"): fig.savefig(os.path.join(HERE, f"chart.{ext}"))
