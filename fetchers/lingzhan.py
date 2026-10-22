"""灵栈中转站 (LingZhan Relay) — self-built relay, NOT a new-api fork.

Public machine-readable pricing endpoint: GET https://lingzhanai.top/api/pricing

Response shape (custom):

    {
      "success": true,
      "data": {
        "groups": [
          {
            "id": "grp_...", "name": "GPT-Pro", "protocol": "OpenAI",
            "final_multiplier": 0.1885,
            "models": [
              {
                "name": "gpt-5.5",
                "pricing_mode": "token" | "image" | "video" | null,
                "input_price": 12.5,     # cents per 1M tokens, site display price (markup included)
                "output_price": 50.0,    # cents per 1M tokens
                "pricing_tiers": [       # image / video absolute tier prices
                  {"label": "1K", "unit_price_yuan": 0.039, "billing_unit": "per_image"}, ...
                ]
              }, ...
            ]
          }, ...
        ],
        "models": { "gpt-5.5": {"group": ..., "multiplier": ..., "input_price": ...}, ... }
      }
    }

Pricing convention (from the endpoint's own `unit` field):
「模型官方目录价按 1:1 记为人民币」— the site bills the official USD catalog price
number 1:1 as CNY, the standard convention among CN relay stations (same basis
as the new-api `model_ratio * $2` formula used by peers in this catalogue).
Therefore cents/1M ÷ 100 → the USD-per-1M number recorded here, matching how
bltcy / unorouter / teamorouter records are quoted.

Image / video tiers expose absolute `unit_price_yuan` (CNY per image / second /
request); under the same 1:1 convention the numeric value is recorded as USD.

Dedup rule: the same model may appear in several access groups; the lowest
observed price per (model, unit) is kept — matching what a user can actually
pay on the cheapest group (the site publishes all groups with no hidden ones).
"""

from __future__ import annotations

from ._common import FetchResult, PriceRecord, http_client

PROVIDER_ID = "lingzhan"
PROVIDER_NAME = "灵栈中转站 (LingZhan)"
SOURCE_URL = "https://lingzhanai.top/api/pricing"
DISPLAY_URL = "https://lingzhanai.top"
CHANNEL_TYPE = "mixed"  # honest type pending maintainer review


def _record(
    provider_id: str,
    provider_name: str,
    name: str,
    unit: str,
    price: float,
    note: str | None = None,
) -> PriceRecord:
    return PriceRecord(
        provider_id=provider_id,
        provider_name=provider_name,
        raw_model_name=name,
        channel_type=CHANNEL_TYPE,
        unit=unit,  # type: ignore[arg-type]
        price_usd=round(price, 6),
        source_url=DISPLAY_URL,
        method="json-api",
        notes=note,
    )


def fetch() -> FetchResult:
    with http_client() as c:
        r = c.get(SOURCE_URL)
        r.raise_for_status()
        payload = r.json()

    if not payload.get("success", True):
        raise RuntimeError(f"{PROVIDER_ID} API returned success=false")

    data = payload.get("data") or {}
    groups = data.get("groups") or []

    # (model, unit) -> lowest price seen across groups
    best: dict[tuple[str, str], PriceRecord] = {}
    raw_models: set[str] = set()

    for group in groups:
        for m in group.get("models") or []:
            name = m.get("name")
            if not name:
                continue
            raw_models.add(name)

            def keep(unit: str, price: float, note: str | None = None) -> None:
                if price <= 0:
                    return
                rec = _record(PROVIDER_ID, PROVIDER_NAME, name, unit, price, note)
                key = (name, unit)
                cur = best.get(key)
                if cur is None or price < cur.price_usd:
                    best[key] = rec

            mode = m.get("pricing_mode")
            if mode == "image":
                for tier in m.get("pricing_tiers") or []:
                    yuan = tier.get("unit_price_yuan")
                    if isinstance(yuan, (int, float)) and yuan > 0:
                        keep("per_image", float(yuan), f"tier {tier.get('label')}")
                continue
            if mode == "video":
                for tier in m.get("pricing_tiers") or []:
                    yuan = tier.get("unit_price_yuan")
                    unit = tier.get("billing_unit") or "per_request"
                    if isinstance(yuan, (int, float)) and yuan > 0 and unit in ("per_image", "per_second", "per_request"):
                        keep(unit, float(yuan), f"tier {tier.get('label')}")
                continue

            # token mode (pricing_mode "token" or null with positive prices)
            input_cents = m.get("input_price")
            if isinstance(input_cents, (int, float)) and input_cents > 0:
                keep("per_1m_input_tokens", float(input_cents) / 100.0)
            output_cents = m.get("output_price")
            if isinstance(output_cents, (int, float)) and output_cents > 0:
                keep("per_1m_output_tokens", float(output_cents) / 100.0)

    return FetchResult(
        provider_id=PROVIDER_ID,
        records=list(best.values()),
        raw_model_count=len(raw_models),
    )
