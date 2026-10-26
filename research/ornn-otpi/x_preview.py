"""X/Twitter preview (1600x900): lab-level OTPI vs relay-implied index. Reads otpi_lab_level.csv next to this file."""
import csv, os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
labs = list(csv.DictReader(open(os.path.join(HERE, "otpi_lab_level.csv"))))
NAME = {"anthropic": "Anthropic", "openai": "OpenAI", "google": "Google", "deepseek": "DeepSeek"}
otpi = [float(l["otpi"]) for l in labs]
lst = [float(l["implied_relay_index_listed"]) for l in labs]
adj = [float(l["implied_relay_index_topup_adj"]) for l in labs]
sp = [float(l["spread_vs_otpi_pct_topup_adj"]) for l in labs]
date = labs[0]["otpi_date"]

fig = plt.figure(figsize=(16, 9), dpi=100)
ax = fig.add_axes([0.06, 0.235, 0.92, 0.55])
x = np.arange(len(labs)); w = 0.28
b1 = ax.bar(x - w, otpi, w, color="#111827", label=f"Ornn OTPI (settled {date})")
b2 = ax.bar(x, lst, w, color="#9ca3af", label="Relay-implied, as listed*")
b3 = ax.bar(x + w, adj, w, color="#fde68a", edgecolor="#92400e", lw=2, label="Relay-implied, after CNY top-up rate*")
for bars in (b1, b2, b3):
    for b in bars:
        ax.annotate(f"${b.get_height():.2f}" if b.get_height() >= 0.1 else f"${b.get_height():.3f}",
                    (b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=19 if b.get_height() >= 0.1 else 15, fontweight="bold", color="#111827")
for i in range(len(labs)):
    col = "#b91c1c" if sp[i] > 0 else ("#15803d" if sp[i] < 0 else "#374151")
    ax.annotate(("±0%" if round(sp[i]) == 0 else f"{sp[i]:+.0f}%") + " vs OTPI", (x[i] + w * 0.5, max(otpi[i], lst[i], adj[i])), xytext=(0, 38), textcoords="offset points",
                ha="center", fontsize=19, fontweight="bold", color=col)
ax.set_xticks(x); ax.set_xticklabels([NAME[l["lab"]] for l in labs], fontsize=26, fontweight="bold")
ax.tick_params(axis="y", labelsize=17)
ax.set_ylabel("USD per 1M tokens (blended)", fontsize=18)
ax.set_ylim(0, max(lst + otpi) * 1.38)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=0.25)
ax.legend(fontsize=18, frameon=False, loc="upper right", ncol=1)
fig.text(0.04, 0.925, "What China/SEA relays actually charge vs Ornn's OTPI", fontsize=35, fontweight="bold", color="#111827")
fig.text(0.04, 0.865, "Lab-level blended price, $ per 1M tokens  ·  regional price discovery", fontsize=22, color="#374151")
foot = (f"Sources: Ornn OTPI, api.ornnai.com (free tier, settlement date {date}); awesome-ai-api-proxy relay snapshot 2026-10-22, ~5 relays; OpenRouter.\n"
        "*Relay-implied = estimate: OTPI × median relay/OpenRouter price ratio. Small sample (1–3 relays per model); group discounts not applied; not verified.\n% labels = after-top-up relay-implied index vs OTPI. Not a recommendation of any relay.")
fig.text(0.04, 0.035, foot, fontsize=14, color="#4b5563", va="bottom", linespacing=1.5)
fig.text(0.975, 0.145, "github.com/howardpen9/awesome-ai-api-proxy", fontsize=17, fontweight="bold", color="#1d4ed8", ha="right")
fig.savefig(os.path.join(HERE, "x-preview.png"), dpi=100)
