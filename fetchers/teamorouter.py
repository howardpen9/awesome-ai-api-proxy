"""TeamoRouter — custom Next.js marketing site, no public JSON pricing API.

The /pricing page renders absolute per-1M-token prices server-side inside
`article.pf-card` blocks (`.pf-now` = current price, `.pf-off` = list price).
`/api/pricing` returns 404 and `/v1/models` requires an API key, so this
fetcher parses the static HTML with selectolax (method: dom).
"""

from __future__ import annotations

import re

from selectolax.parser import HTMLParser

from ._common import FetchResult, PriceRecord, http_client

PROVIDER_ID = "teamorouter"
PROVIDER_NAME = "TeamoRouter"
SOURCE_URL = "https://teamorouter.com/pricing"

_UNIT_BY_CAP = {
    "input": "per_1m_input_tokens",
    "output": "per_1m_output_tokens",
}

_DOLLARS_RE = re.compile(r"^\$([\d.]+)$")


def _parse_price(text: str) -> float | None:
    m = _DOLLARS_RE.match(text.strip())
    return float(m.group(1)) if m else None


def fetch() -> FetchResult:
    with http_client() as c:
        r = c.get(SOURCE_URL)
        r.raise_for_status()

    tree = HTMLParser(r.text)
    cards = tree.css("article.pf-card")

    seen_names: set[str] = set()
    records: list[PriceRecord] = []
    for card in cards:
        name_node = card.css_first("b.pf-name")
        if name_node is None:
            continue
        model_name = name_node.text(strip=True)
        if not model_name:
            continue
        seen_names.add(model_name)
        for col in card.css(".pf-prices .pf-col"):
            cap_node = col.css_first("span.pf-cap")
            now_node = col.css_first("b.pf-now")
            if cap_node is None or now_node is None:
                continue
            cap = cap_node.text(strip=True).lower()
            unit = next((u for key, u in _UNIT_BY_CAP.items() if key in cap), None)
            price = _parse_price(now_node.text(strip=True))
            if unit is None or price is None or price <= 0:
                continue
            records.append(
                PriceRecord(
                    provider_id=PROVIDER_ID,
                    provider_name=PROVIDER_NAME,
                    raw_model_name=model_name,
                    channel_type="mixed",
                    unit=unit,
                    price_usd=price,
                    source_url=SOURCE_URL,
                    confidence="medium",
                    method="dom",
                )
            )

    return FetchResult(
        provider_id=PROVIDER_ID,
        records=records,
        raw_model_count=len(seen_names),
    )
