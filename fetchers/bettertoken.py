"""BetterToken — new-api fork with per-vendor access groups.

Each model is enabled in exactly one group (Claude, GPT, DeepSeek, …) and
that group's ratio is the price a buyer in the group actually pays. Pass
`per_enable_group=True` so a ratio of 1 is not recorded as the paid price.
"""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "bettertoken"
PROVIDER_NAME = "BetterToken"
SOURCE_URL = "https://bettertoken.ai/api/pricing"
DISPLAY_URL = "https://bettertoken.ai/pricing"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="aggregator",
        per_enable_group=True,
    )
