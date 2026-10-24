"""UnoRouter — new-api fork. Thin wrapper over fetchers._new_api.

Aggregator; one key, latency-based routing. Public `/api/pricing` has no flat
`default` group — ratios hang off per-channel enable groups (often well below
1, plus ratio-0 free pools). `group=None` records each model's default group,
else its only group, else the cheapest positive ratio. The full `group_ratio`
map is stored on the snapshot.
"""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "unorouter"
PROVIDER_NAME = "UnoRouter"
SOURCE_URL = "https://api.unorouter.ai/api/pricing"
DISPLAY_URL = "https://unorouter.ai/models"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="aggregator",
        group=None,
    )
