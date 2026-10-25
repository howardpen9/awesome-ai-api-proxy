"""Paidyun AI — new-api fork. Thin wrapper over fetchers._new_api."""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "paidyun"
PROVIDER_NAME = "Paidyun AI"
SOURCE_URL = "https://paidyun.xyz/api/pricing"
DISPLAY_URL = "https://paidyun.xyz/pricing"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="mixed",
        group=None,
    )
