"""Build regional price discovery dataset: China/SEA relay prices vs Ornn OTPI.
Inputs: raw/otpi_*.json (Ornn API), raw/relays/*_status_*.json + *_pricing_*.json,
raw/fx_usd_cny.json, <repo root>/data/prices.latest.json (awesome-ai-api-proxy main; override with AAP_ROOT)."""
import json, glob, statistics as st, csv, subprocess, os
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = f"{HERE}/raw"
AAP = os.environ.get("AAP_ROOT", os.path.abspath(os.path.join(HERE, "..", "..")))  # repo root
snap = json.load(open(f"{AAP}/data/prices.latest.json"))
aap_commit = subprocess.check_output(["git", "-C", AAP, "rev-parse", "HEAD"]).decode().strip()
otpi_raw = json.load(open(f"{RAW}/otpi_latest.json"))
OTPI = {r["lab"]: r for r in otpi_raw["body"]["data"]}
OTPI_ASOF = otpi_raw["body"]["date"]
fx = json.load(open(f"{RAW}/fx_usd_cny.json")); USDCNY = fx["USD_CNY"]

LAB_OF = {"claude": "anthropic", "gpt": "openai", "gemini": "google", "deepseek": "deepseek"}
MODELS = ["claude-opus-5", "claude-sonnet-5", "claude-fable-5",
          "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5", "gpt-5.4",
          "gemini-3.1-pro-preview", "gemini-3.8-flash", "gemini-3.5-flash",
          "deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v3.2"]
RELAYS = ["uiuiapi", "relaydance", "teamorouter", "wappkit", "unorouter"]
REF = "openrouter"
EXCLUDED_PROVIDERS = {"bltcy": "Announced shutdown in its own /api/status announcements (published 2026-04-24T16:00Z): new registrations and top-ups stopped, all API service ends 2026-05-01. Pricing endpoint still responds, but prices are not purchasable.", "quicksilverpro": "Card-only gateway, operator claims MachineFi Labs; not a China/SEA new-api relay", "atlascloud": "Card-only multimodal aggregator; not a China/SEA new-api relay", "openrouter": "used as reference, not a relay"}
UNVERIFIED = {"teamorouter", "wappkit", "unorouter"}  # providers.yaml status: unverified / operator_submitted

# Top-up rate: new-api /api/status `price` = CNY charged per 1 USD of quota (Alipay/WeChat path).
topup = {}
for rid in RELAYS:
    fs = sorted(glob.glob(f"{RAW}/relays/{rid}_status_*.json"))
    if not fs: topup[rid] = None; continue
    d = json.load(open(fs[-1])).get("data", {})
    topup[rid] = {"cny_per_usd_quota": d.get("price"), "stripe_unit_price": d.get("stripe_unit_price"),
                  "quota_display_type": d.get("quota_display_type"), "status_file": os.path.basename(fs[-1])}
def factor(rid):
    t = topup.get(rid)
    if rid == "unorouter":  # card-only, USD display, usd_exchange_rate 1 -> treat as USD-billed (unverified)
        return 1.0, "topup_assumed_usd"
    if not t or not t["cny_per_usd_quota"]:
        return 1.0, "topup_unknown"
    f = t["cny_per_usd_quota"] / USDCNY
    return f, f"topup_cny{t['cny_per_usd_quota']}_per_usd_quota"

# group ratios available per model (live pricing)
groups = {}
for rid in RELAYS:
    fs = sorted(glob.glob(f"{RAW}/relays/{rid}_pricing_*.json"))
    if not fs: continue
    d = json.load(open(fs[-1])); gr = d.get("group_ratio") or {}
    for m in d.get("data", []):
        rs = [gr[g] for g in (m.get("enable_groups") or []) if g in gr]
        if rs: groups[(rid, m["model_name"].lower())] = (min(rs), max(rs), len(rs))

def norm(n): return n.lower().split("/")[-1]
recs = {}
for r in snap["records"]:
    if r["unit"] not in ("per_1m_input_tokens", "per_1m_output_tokens"): continue  # excludes per_request/per_image/per_second/cache
    n = norm(r["raw_model_name"])
    if n not in MODELS: continue
    recs.setdefault((n, r["provider_id"]), {}).setdefault(r["unit"][7:9], []).append(r)

rows, mapping, excluded = [], [], []
for m in MODELS:
    lab = LAB_OF[m.split("-")[0]]
    ref = recs.get((m, REF))
    if not ref or "in" not in ref or "ou" not in ref:
        excluded.append({"model": m, "reason": "no OpenRouter reference"}); continue
    ref_in, ref_out = ref["in"][0]["price_usd"], ref["ou"][0]["price_usd"]
    per = []
    for rid in RELAYS:
        e = recs.get((m, rid))
        if not e or "in" not in e or "ou" not in e: continue
        pin, pout = st.median(x["price_usd"] for x in e["in"]), st.median(x["price_usd"] for x in e["ou"])
        raw_names = sorted({x["raw_model_name"] for x in e["in"]})
        flags = []
        if rid in ("bltcy", "uiuiapi", "relaydance", "unorouter", "wappkit"):
            flags.append("new_api_group_ratio" + ("_default" if rid in ("bltcy", "uiuiapi", "relaydance") else ("_1.0" if rid == "unorouter" else "_codex_pool_0.3")))
        if abs(pin - 75.0) < 1e-9 and rid in ("uiuiapi", "bltcy", "relaydance", "unorouter", "wappkit"):
            excluded.append({"model": m, "relay": rid, "in": pin, "out": pout,
                             "reason": "new-api placeholder model_ratio 37.5 ($75/M input) = unpriced model default"}); continue
        f, ftag = factor(rid); flags.append(ftag)
        if f < 0.6: flags.append("usd_label_billed_in_rmb_risk")
        if rid == "wappkit": flags.append("account_pool_group")
        if rid in UNVERIFIED: flags.append("provider_unverified")
        g = groups.get((rid, m))
        if rid == "unorouter" and g and (g[0] != 1 or g[1] != 1):
            flags.append(f"unorouter_group_ratio_not_applied_live_range_{g[0]}-{g[1]}")
        per.append({"relay": rid, "raw_model_name": raw_names, "in": pin, "out": pout,
                    "in_adj": pin * f, "out_adj": pout * f, "topup_factor": round(f, 4),
                    "group_ratio_range": f"{g[0]}-{g[1]} ({g[2]} groups)" if g else None, "flags": flags})
        mapping.append({"model": m, "relay": rid, "raw_model_name": raw_names, "ref_raw": ref["in"][0]["raw_model_name"]})
    if len(per) < 1:
        excluded.append({"model": m, "reason": "no usable relay quote"}); continue
    def s(k): v = [p[k] for p in per]; return min(v), st.median(v), max(v)
    imin, imed, imax = s("in"); omin, omed, omax = s("out")
    aimin, aimed, aimax = s("in_adj"); aomin, aomed, aomax = s("out_adj")
    o = OTPI.get(lab)
    flags = sorted({f for p in per for f in p["flags"]} | ({"single_relay"} if len(per) == 1 else set()))
    rows.append({
        "model": m, "provider": lab,
        "otpi_in": None, "otpi_out": None,
        "otpi_lab_blended": round(o["indexPerMtok"], 4) if o else None, "otpi_as_of": OTPI_ASOF,
        "ref_in": ref_in, "ref_out": ref_out, "ref_source": "OpenRouter posted price (aap snapshot)",
        "relay_min_in": imin, "relay_median_in": imed, "relay_max_in": imax,
        "relay_min_out": omin, "relay_median_out": omed, "relay_max_out": omax,
        "relay_median_in_topup_adj": round(aimed, 4), "relay_median_out_topup_adj": round(aomed, 4),
        "relay_min_in_topup_adj": round(aimin, 4), "relay_min_out_topup_adj": round(aomin, 4),
        "n_relays": len(per), "relays": ";".join(p["relay"] for p in per),
        "relay_snapshot_date": snap["snapshot_date"],
        "spread_basis": "relay median vs OpenRouter posted price for same model (OTPI free tier has no per-model input/output)",
        "spread_in_pct": round((imed - ref_in) / ref_in * 100, 1), "spread_out_pct": round((omed - ref_out) / ref_out * 100, 1),
        "spread_in_pct_topup_adj": round((aimed - ref_in) / ref_in * 100, 1), "spread_out_pct_topup_adj": round((aomed - ref_out) / ref_out * 100, 1),
        "caveat_flags": ";".join(flags),
        "per_relay": per,
        "sources": f"OTPI: https://api.ornnai.com/api/otpi?lab={lab} (date {OTPI_ASOF}); relays+ref: awesome-ai-api-proxy@{aap_commit[:7]} data/prices.latest.json; top-up: <relay>/api/status",
    })

# lab-level: implied relay index = OTPI x median(relay_median / ref) over the lab's models (in & out pooled)
labs = []
for lab, o in OTPI.items():
    lr = [r for r in rows if r["provider"] == lab]
    if not lr: continue
    rat = [r["relay_median_in"] / r["ref_in"] for r in lr] + [r["relay_median_out"] / r["ref_out"] for r in lr]
    rat_adj = [r["relay_median_in_topup_adj"] / r["ref_in"] for r in lr] + [r["relay_median_out_topup_adj"] / r["ref_out"] for r in lr]
    R, RA = st.median(rat), st.median(rat_adj)
    labs.append({"lab": lab, "otpi": round(o["indexPerMtok"], 4), "otpi_date": o["date"], "otpi_computed_at": o["computedAt"],
                 "models": [r["model"] for r in lr], "median_ratio_listed": round(R, 3), "median_ratio_topup_adj": round(RA, 3),
                 "implied_relay_index_listed": round(o["indexPerMtok"] * R, 4), "implied_relay_index_topup_adj": round(o["indexPerMtok"] * RA, 4),
                 "spread_vs_otpi_pct_listed": round((R - 1) * 100, 1), "spread_vs_otpi_pct_topup_adj": round((RA - 1) * 100, 1)})

meta = {"title": "China/SEA relay prices vs OTPI per MTok — regional price discovery",
        "built_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds"),
        "otpi": {"endpoint": "https://api.ornnai.com/api/otpi", "access": otpi_raw["body"].get("access"), "settlement_date": OTPI_ASOF,
                 "fetched_at_utc": otpi_raw["fetched_at_utc"], "fetched_at_utc8": otpi_raw["fetched_at_utc8"],
                 "note": "Lab-level, volume-weighted blended USD/MTok; no input/output split on free tier"},
        "relay_snapshot": {"repo": "howardpen9/awesome-ai-api-proxy", "commit": aap_commit, "snapshot_date": snap["snapshot_date"], "generated_at": snap["generated_at"]},
        "fx": fx, "topup": topup, "relay_set": RELAYS, "excluded_providers": EXCLUDED_PROVIDERS, "reference": REF,
        "excluded": excluded}
json.dump({"meta": meta, "lab_level": labs, "models": rows, "mapping": mapping}, open(f"{HERE}/otpi_vs_relays.json", "w"), indent=1, ensure_ascii=False)
cols = [k for k in rows[0] if k != "per_relay"]
with open(f"{HERE}/otpi_vs_relays.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow({k: r[k] for k in cols})
with open(f"{HERE}/otpi_lab_level.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=[k for k in labs[0] if k != "models"] + ["models"]); w.writeheader()
    for l in labs: w.writerow({**l, "models": ";".join(l["models"])})
print(json.dumps(labs, indent=1)); print(json.dumps(excluded, indent=1))
for r in rows: print(r["model"], r["n_relays"], r["ref_in"], r["ref_out"], (r["relay_min_in"], r["relay_median_in"], r["relay_max_in"]), (r["relay_min_out"], r["relay_median_out"], r["relay_max_out"]), r["spread_in_pct"], r["spread_out_pct"], r["spread_in_pct_topup_adj"], r["spread_out_pct_topup_adj"], r["relays"])
print(topup)
