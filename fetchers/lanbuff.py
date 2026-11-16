"""Lanbuff (蓝博API) — new-api fork. Thin wrapper over fetchers._new_api."""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "lanbuff"
PROVIDER_NAME = "蓝博API (Lanbuff)"
SOURCE_URL = "https://lanbuff.app/api/pricing"
DISPLAY_URL = "https://lanbuff.app/pricing"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="mixed",  # official-relay | mixed | reverse | aggregator
        group=None,
    )
