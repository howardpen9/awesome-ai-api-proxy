"""CrowLLM — new-api gateway. Thin wrapper over fetchers._new_api.

One key for models from several labs; public `/api/pricing` exposes the
standard new-api ratio shape (USD/1M = model_ratio * 2).
"""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "crowllm"
PROVIDER_NAME = "CrowLLM"
SOURCE_URL = "https://crowllm.com/api/pricing"
DISPLAY_URL = "https://crowllm.com/pricing"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="aggregator",
        group=None,
    )
