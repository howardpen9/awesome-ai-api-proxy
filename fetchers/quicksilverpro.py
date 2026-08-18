"""QuickSilver Pro — public /pricing.json catalog (already $/1M or $/image).

Operator-submitted aggregator. Catalog is generated from their model list;
do not treat `discount_vs_official` as independently verified.
"""

from __future__ import annotations

from ._common import FetchResult, PriceRecord, http_client

PROVIDER_ID = "quicksilverpro"
PROVIDER_NAME = "QuickSilver Pro"
SOURCE_URL = "https://quicksilverpro.io/pricing.json"
DISPLAY_URL = "https://quicksilverpro.io"


def fetch() -> FetchResult:
    with http_client() as c:
        r = c.get(SOURCE_URL)
        r.raise_for_status()
        payload = r.json()

    models = payload.get("models") or []
    records: list[PriceRecord] = []
    for m in models:
        model_id = m.get("id")
        if not model_id:
            continue
        for src_key, unit in (
            ("input_per_1m", "per_1m_input_tokens"),
            ("output_per_1m", "per_1m_output_tokens"),
            ("cached_input_per_1m", "per_1m_input_cache_read_tokens"),
            ("output_per_image", "per_image"),
        ):
            raw = m.get(src_key)
            if raw is None:
                continue
            try:
                price = float(raw)
            except (TypeError, ValueError):
                continue
            if price <= 0:
                continue
            records.append(
                PriceRecord(
                    provider_id=PROVIDER_ID,
                    provider_name=PROVIDER_NAME,
                    raw_model_name=model_id,
                    channel_type="aggregator",
                    unit=unit,  # type: ignore[arg-type]
                    price_usd=price,
                    source_url=DISPLAY_URL,
                    method="json-api",
                )
            )

    return FetchResult(
        provider_id=PROVIDER_ID,
        records=records,
        raw_model_count=len(models),
    )
