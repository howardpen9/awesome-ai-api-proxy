"""Shared logic for new-api / one-api fork pricing endpoints.

Every new-api fork (Calcium-Ion's new-api, songquanpeng's one-api derivatives,
and most Chinese relay stations built on these templates) exposes a public
`/api/pricing` endpoint with the same JSON shape:

    {
      "success": true,
      "data": [ { model_name, quota_type, model_ratio, completion_ratio, model_price, ... }, ... ],
      "group_ratio": { "default": 1, "vip": 0.8, ... },
      "billing_expr": optional, on each model
    }

Legacy per-token pricing (quota_type=0), before the group multiplier:

    input_per_1m  = model_ratio * BASE
    output_per_1m = model_ratio * completion_ratio * BASE
    BASE = $2.00 per 1M tokens

A configured `billing_expr` replaces that legacy pair. new-api's unset legacy
ratio is 37.5 ($75/1M at group ratio 1). Relays leave that default in place
and put the real price in `billing_expr` (`p` input, `c` output, USD per 1M).

The recorded `price_usd` is the legacy or expression price times the public
group ratio (see `choose_pricing_group`). `list_price_usd` keeps the
ratio-1 figure. Policy and top-up adjustment: docs/methodology.md.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from ._common import FetchResult, PriceRecord

NEW_API_BASE_USD_PER_1M = 2.0
# Hard-coded new-api fallback when a model has no configured legacy ratio.
UNSET_MODEL_RATIO = 37.5
QUOTA_TYPE_PER_TOKEN = 0
QUOTA_TYPE_PER_CALL = 1

_P_RE = re.compile(r"(?<![A-Za-z_])p\s*\*\s*([0-9]+(?:\.[0-9]+)?)")
_C_RE = re.compile(r"(?<![A-Za-z_])c\s*\*\s*([0-9]+(?:\.[0-9]+)?)")
_CR_RE = re.compile(r"(?<![A-Za-z_])cr\s*\*\s*([0-9]+(?:\.[0-9]+)?)")
_FIXED_RE = re.compile(r"fixed\(\s*([0-9]+(?:\.[0-9]+)?)\s*\)")


class PricingGroup(NamedTuple):
    name: str | None
    ratio: float
    ratio_max: float | None
    enabled_count: int


class ParsedBilling(NamedTuple):
    tier: str | None
    input_per_1m: float | None
    output_per_1m: float | None
    cache_read_per_1m: float | None
    fixed_price: float | None


def _enabled_groups(model: dict, group_ratios: dict) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for name in model.get("enable_groups") or []:
        if name not in group_ratios:
            continue
        try:
            out.append((str(name), float(group_ratios[name])))
        except (TypeError, ValueError):
            continue
    return out


def choose_pricing_group(
    model: dict,
    group_ratios: dict,
    *,
    group: str | None,
    per_enable_group: bool,
) -> PricingGroup | None:
    """Pick the group ratio a public buyer is billed at.

    Returns None to skip the model (it is not in an explicitly requested group).

    * Explicit `group` (and not `per_enable_group`): that group, if the model
      enables it. Missing ratio falls back to 1.
    * Else a sole `enable_groups` entry, including BetterToken's per-vendor groups.
    * Else a group named exactly `default`, when this model enables it.
    * Else the cheapest **positive** enabled ratio (free ratio-0 groups are not
      the paid price). Ties break by group name.
    * No group metadata: ratio 1, which is the historical list price.
    """
    enabled = _enabled_groups(model, group_ratios)
    positive = [(name, ratio) for name, ratio in enabled if ratio > 0]
    ratio_max = max((ratio for _, ratio in positive), default=None)

    if group is not None and not per_enable_group:
        names = model.get("enable_groups") or [group]
        if group not in names:
            return None
        match = next((ratio for name, ratio in enabled if name == group), None)
        if match is None:
            try:
                match = float(group_ratios.get(group, 1))
            except (TypeError, ValueError):
                match = 1.0
        return PricingGroup(group, match, ratio_max, len(enabled))

    if len(enabled) == 1:
        name, ratio = enabled[0]
        return PricingGroup(name, ratio, ratio, 1)

    for name, ratio in enabled:
        if name == "default":
            return PricingGroup("default", ratio, ratio_max, len(enabled))

    if positive:
        name, ratio = min(positive, key=lambda item: (item[1], item[0]))
        return PricingGroup(name, ratio, ratio_max, len(enabled))

    if not enabled:
        return PricingGroup(None, 1.0, None, 0)

    name, ratio = enabled[0]
    return PricingGroup(name, ratio, None, len(enabled))


def _first_tier(expr: str) -> tuple[str, str] | None:
    """Return (label, body) of the first tier() call, which is the short-context price."""
    start = expr.find("tier(")
    if start < 0:
        return None
    j = start + len("tier(")
    depth = 1
    buf: list[str] = []
    args: list[str] = []
    while j < len(expr):
        ch = expr[j]
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            if depth == 0:
                args.append("".join(buf).strip())
                break
            buf.append(ch)
        elif ch == "," and depth == 1:
            args.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        j += 1
    else:
        return None
    if len(args) < 2:
        return None
    label = args[0].strip()
    if len(label) >= 2 and label[0] == label[-1] and label[0] in "\"'":
        label = label[1:-1]
    return label, args[1]


def parse_billing_expr(expr: object) -> ParsedBilling | None:
    """Parse the first tier of a new-api billing expression.

    `p` / `c` / `cr` are USD per 1M tokens. `fixed(n)` is a per-call price.
    The first tier is the short-context price when the expression is a
    `len <= N ? tier(...) : tier(...)` pair. Returns None if nothing priced
    can be read; the caller then uses the legacy ratio.
    """
    if not isinstance(expr, str) or not expr.strip():
        return None
    tier = _first_tier(expr)
    if tier is None:
        return None
    label, body = tier
    prompt = _P_RE.search(body)
    completion = _C_RE.search(body)
    cache_read = _CR_RE.search(body)
    fixed = _FIXED_RE.search(body)
    if prompt is None and completion is None and fixed is None:
        return None
    return ParsedBilling(
        tier=label or None,
        input_per_1m=float(prompt.group(1)) if prompt else None,
        output_per_1m=float(completion.group(1)) if completion else None,
        cache_read_per_1m=float(cache_read.group(1)) if cache_read else None,
        fixed_price=float(fixed.group(1)) if fixed and prompt is None else None,
    )


def is_unset_model_ratio(ratio: float) -> bool:
    return abs(ratio - UNSET_MODEL_RATIO) < 1e-6


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
        public_pricing_url: the user-facing page (recorded as `source_url`)
        channel_type: one of the ChannelType literals; vendors vary
        group: access group to record. `"default"` keeps only models that
            enable that group and uses its ratio. `None` does not filter;
            each model uses `default` when it has one, otherwise its sole
            group, otherwise the cheapest positive enabled ratio.
        per_enable_group: price each model at its own access group. A model
            enabled in exactly one known group uses that ratio (BetterToken).
            Other models use the same public-group rule as `group=None`.
    """
    # Local import keeps tests of the pure helpers free of httpx setup order.
    from ._common import http_client

    with http_client() as c:
        r = c.get(pricing_api_url)
        r.raise_for_status()
        payload = r.json()

    if not payload.get("success", True):
        raise RuntimeError(f"{provider_id} API returned success=false: {payload}")

    models = payload.get("data", [])
    raw_groups = payload.get("group_ratio") or {}
    group_ratios: dict[str, float] = {}
    for name, value in raw_groups.items():
        try:
            group_ratios[str(name)] = float(value)
        except (TypeError, ValueError):
            continue

    records: list[PriceRecord] = []
    for m in models:
        name = m.get("model_name")
        if not name:
            continue
        choice = choose_pricing_group(
            m,
            group_ratios,
            group=group,
            per_enable_group=per_enable_group,
        )
        if choice is None or choice.ratio <= 0:
            continue

        parsed = parse_billing_expr(m.get("billing_expr"))
        expr = m.get("billing_expr") if parsed is not None else None
        tier = parsed.tier if parsed is not None else None
        if parsed is not None and parsed.fixed_price is not None and parsed.fixed_price > 0:
            records.append(
                _rec(
                    provider_id, provider_name, public_pricing_url, channel_type,
                    name, _per_call_unit(name), parsed.fixed_price * choice.ratio,
                    choice, list_price=parsed.fixed_price, billing_expr=expr, price_tier=tier,
                )
            )
            continue
        if parsed is not None and (
            (parsed.input_per_1m or 0) > 0 or (parsed.output_per_1m or 0) > 0
        ):
            if parsed.input_per_1m is not None and parsed.input_per_1m > 0:
                records.append(
                    _rec(
                        provider_id, provider_name, public_pricing_url, channel_type,
                        name, "per_1m_input_tokens", parsed.input_per_1m * choice.ratio,
                        choice, list_price=parsed.input_per_1m, billing_expr=expr, price_tier=tier,
                    )
                )
            if parsed.output_per_1m is not None and parsed.output_per_1m > 0:
                records.append(
                    _rec(
                        provider_id, provider_name, public_pricing_url, channel_type,
                        name, "per_1m_output_tokens", parsed.output_per_1m * choice.ratio,
                        choice, list_price=parsed.output_per_1m, billing_expr=expr, price_tier=tier,
                    )
                )
            if parsed.cache_read_per_1m is not None and parsed.cache_read_per_1m > 0:
                records.append(
                    _rec(
                        provider_id, provider_name, public_pricing_url, channel_type,
                        name, "per_1m_input_cache_read_tokens",
                        parsed.cache_read_per_1m * choice.ratio,
                        choice, list_price=parsed.cache_read_per_1m,
                        billing_expr=expr, price_tier=tier,
                    )
                )
            continue

        quota_type = m.get("quota_type", QUOTA_TYPE_PER_TOKEN)
        if quota_type == QUOTA_TYPE_PER_TOKEN:
            ratio = m.get("model_ratio")
            comp_ratio = m.get("completion_ratio")
            if ratio is None or float(ratio) <= 0:
                continue
            ratio_f = float(ratio)
            placeholder = is_unset_model_ratio(ratio_f)
            input_list = ratio_f * NEW_API_BASE_USD_PER_1M
            records.append(
                _rec(
                    provider_id, provider_name, public_pricing_url, channel_type,
                    name, "per_1m_input_tokens", input_list * choice.ratio,
                    choice, list_price=input_list, placeholder=placeholder,
                )
            )
            if comp_ratio is not None and float(comp_ratio) > 0:
                output_list = ratio_f * float(comp_ratio) * NEW_API_BASE_USD_PER_1M
                records.append(
                    _rec(
                        provider_id, provider_name, public_pricing_url, channel_type,
                        name, "per_1m_output_tokens", output_list * choice.ratio,
                        choice, list_price=output_list, placeholder=placeholder,
                    )
                )
        elif quota_type == QUOTA_TYPE_PER_CALL:
            price = m.get("model_price")
            if price is None or float(price) <= 0:
                continue
            unit = _per_call_unit(name)
            list_price = float(price)
            records.append(
                _rec(
                    provider_id, provider_name, public_pricing_url, channel_type,
                    name, unit, list_price * choice.ratio,
                    choice, list_price=list_price,
                )
            )

    return FetchResult(
        provider_id=provider_id,
        records=records,
        raw_model_count=len(models),
        group_ratios=group_ratios or None,
    )


def _per_call_unit(model_name: str) -> str:
    n = model_name.lower()
    if any(tag in n for tag in ("video", "i2v", "r2v", "t2v", "seedance", "video-edit")):
        return "per_second"
    if "image" in n or "imagine-image" in n:
        return "per_image"
    return "per_request"


def _rec(
    provider_id: str,
    provider_name: str,
    source_url: str,
    channel_type: str,
    model_id: str,
    unit: str,
    price: float,
    choice: PricingGroup,
    *,
    list_price: float,
    placeholder: bool = False,
    billing_expr: str | None = None,
    price_tier: str | None = None,
) -> PriceRecord:
    ratio_max = choice.ratio_max
    if ratio_max is not None and abs(ratio_max - choice.ratio) < 1e-9:
        ratio_max = None
    return PriceRecord(
        provider_id=provider_id,
        provider_name=provider_name,
        raw_model_name=model_id,
        channel_type=channel_type,  # type: ignore[arg-type]
        unit=unit,  # type: ignore[arg-type]
        price_usd=price,
        source_url=source_url,
        method="json-api",
        list_price_usd=list_price,
        group_ratio=choice.ratio,
        pricing_group=choice.name,
        group_ratio_max=ratio_max,
        price_placeholder=placeholder,
        billing_expr=billing_expr if isinstance(billing_expr, str) else None,
        price_tier=price_tier,
        confidence="low" if placeholder else "high",
    )
