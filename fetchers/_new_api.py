"""Shared logic for new-api / one-api fork pricing endpoints.

Every new-api fork (Calcium-Ion's new-api, songquanpeng's one-api derivatives,
and most Chinese relay stations built on these templates) exposes a public
`/api/pricing` endpoint with the same JSON shape:

    {
      "success": true,
      "data": [ { model_name, quota_type, model_ratio, completion_ratio, model_price, ... }, ... ],
      "group_ratio": { "default": 1, "vip": 0.8, ... }
    }

Pricing convention (per-token, quota_type=0):
    input_per_1m  = model_ratio * BASE * group_ratio
    output_per_1m = model_ratio * completion_ratio * BASE * group_ratio
    BASE = $2.00 per 1M tokens

Pricing convention (per-call, quota_type=1):
    cost_per_call = model_price * group_ratio
"""

from __future__ import annotations

from ._common import FetchResult, PriceRecord, http_client

NEW_API_BASE_USD_PER_1M = 2.0
QUOTA_TYPE_PER_TOKEN = 0
QUOTA_TYPE_PER_CALL = 1


def _ratio_for_model(
    model: dict,
    group_ratios: dict,
    *,
    group: str | None,
    per_enable_group: bool,
    uniform_ratio: float,
) -> float | None:
    """Return the group_ratio to apply, or None to skip this model.

    `per_enable_group` prices each model at its own access group. BetterToken
    publishes one enable_group per model (Claude 0.68, MiniMax 0.58, Gemini 1,
    …). A flat ratio of 1 records the undiscounted list price.
    """
    if not per_enable_group:
        if group is not None:
            enable_groups = model.get("enable_groups") or [group]
            if group not in enable_groups:
                return None
        return uniform_ratio

    enabled = [g for g in (model.get("enable_groups") or []) if g in group_ratios]
    if len(enabled) == 1:
        return float(group_ratios[enabled[0]])
    return 1.0


def fetch_new_api(
    provider_id: str,
    provider_name: str,
    pricing_api_url: str,
    public_pricing_url: str,
    channel_type: str = "mixed",
    group: str | None = "default",
    per_enable_group: bool = False,
) -> FetchResult:
    """Fetch + normalize a new-api fork's /api/pricing response.

    Args:
        provider_id: stable slug, must match providers.yaml `pricing.fetcher`
        provider_name: display name (e.g., "Relaydance")
        pricing_api_url: the JSON endpoint, usually `<host>/api/pricing`
        public_pricing_url: the user-facing page (recorded as `source_url` on
            each PriceRecord — this is what gets cited)
        channel_type: one of the ChannelType literals; vendors vary
        group: which access group's price to record. Pass `None` for forks that
            don't expose a flat "default" group (e.g. per-model channel groups
            on UnoRouter) — group_ratio is treated as 1 and the enable_groups
            filter is skipped.
        per_enable_group: when True, skip the single-group filter and multiply
            each model by the ratio of its sole `enable_groups` entry. Models
            in zero or several known groups keep ratio 1.
    """
    with http_client() as c:
        r = c.get(pricing_api_url)
        r.raise_for_status()
        payload = r.json()

    if not payload.get("success", True):
        raise RuntimeError(f"{provider_id} API returned success=false: {payload}")

    models = payload.get("data", [])
    group_ratios = payload.get("group_ratio") or {}
    if group is None or per_enable_group:
        uniform_ratio = 1.0
    else:
        uniform_ratio = float(group_ratios.get(group, 1))

    records: list[PriceRecord] = []
    for m in models:
        name = m.get("model_name")
        if not name:
            continue
        group_ratio = _ratio_for_model(
            m,
            group_ratios,
            group=group,
            per_enable_group=per_enable_group,
            uniform_ratio=uniform_ratio,
        )
        if group_ratio is None:
            continue

        quota_type = m.get("quota_type", QUOTA_TYPE_PER_TOKEN)
        if quota_type == QUOTA_TYPE_PER_TOKEN:
            ratio = m.get("model_ratio")
            comp_ratio = m.get("completion_ratio")
            if ratio is None or float(ratio) <= 0:
                continue
            input_price = float(ratio) * NEW_API_BASE_USD_PER_1M * group_ratio
            records.append(
                _rec(
                    provider_id, provider_name, public_pricing_url, channel_type,
                    name, "per_1m_input_tokens", input_price,
                )
            )
            if comp_ratio is not None and float(comp_ratio) > 0:
                output_price = (
                    float(ratio) * float(comp_ratio) * NEW_API_BASE_USD_PER_1M * group_ratio
                )
                records.append(
                    _rec(
                        provider_id, provider_name, public_pricing_url, channel_type,
                        name, "per_1m_output_tokens", output_price,
                    )
                )
        elif quota_type == QUOTA_TYPE_PER_CALL:
            price = m.get("model_price")
            if price is None or float(price) <= 0:
                continue
            unit = _per_call_unit(name)
            records.append(
                _rec(
                    provider_id, provider_name, public_pricing_url, channel_type,
                    name, unit, float(price) * group_ratio,
                )
            )

    return FetchResult(
        provider_id=provider_id,
        records=records,
        raw_model_count=len(models),
    )


def _per_call_unit(model_name: str) -> str:
    n = model_name.lower()
    if any(tag in n for tag in ("video", "i2v", "r2v", "t2v", "seedance", "video-edit")):
        return "per_second"
    if "image" in n or "imagine-image" in n:
        return "per_image"
    return "per_request"


def _rec(
    provider_id: str, provider_name: str, source_url: str, channel_type: str,
    model_id: str, unit: str, price: float,
) -> PriceRecord:
    return PriceRecord(
        provider_id=provider_id,
        provider_name=provider_name,
        raw_model_name=model_id,
        channel_type=channel_type,  # type: ignore[arg-type]
        unit=unit,  # type: ignore[arg-type]
        price_usd=price,
        source_url=source_url,
        method="json-api",
    )
