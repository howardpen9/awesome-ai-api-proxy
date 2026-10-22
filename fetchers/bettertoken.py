"""BetterToken — new-api fork. Thin wrapper over fetchers._new_api.

Per-vendor access groups (Claude/GPT/DeepSeek/…) instead of a flat default
group — same pattern as UnoRouter; pass group=None so enable_groups is not
filtered and group_ratio is treated as 1.
"""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "bettertoken"
PROVIDER_NAME = "BetterToken"
SOURCE_URL = "https://bettertoken.ai/api/pricing"
DISPLAY_URL = "https://bettertoken.ai"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="aggregator",
        group=None,
    )
