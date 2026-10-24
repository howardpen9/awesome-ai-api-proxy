"""YCSG API — new-api fork. Thin wrapper over fetchers._new_api.

Public /api/pricing puts every listed model in the flat `default` group
(group_ratio 1). Operator-submitted; not a maintainer canary.
"""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "ycsg"
PROVIDER_NAME = "YCSG API"
SOURCE_URL = "https://api.ycsgyuuu.study/api/pricing"
DISPLAY_URL = "https://api.ycsgyuuu.study"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="aggregator",
    )
