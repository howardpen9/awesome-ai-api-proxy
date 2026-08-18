"""Wappkit API — new-api fork. Thin wrapper over fetchers._new_api.

Public /api/pricing has no flat `default` group. Every listed model is in
`Codex-Pro(救急)` (group_ratio 0.3); other Codex/Claude-Code pools exist in
group_ratio but are not attached to the published model rows.
"""

from __future__ import annotations

from ._common import FetchResult
from ._new_api import fetch_new_api

PROVIDER_ID = "wappkit"
PROVIDER_NAME = "Wappkit API"
SOURCE_URL = "https://api.wappkit.com/api/pricing"
DISPLAY_URL = "https://api.wappkit.com"
# Only group that currently appears on enable_groups for published models.
_GROUP = "Codex-Pro(救急)"


def fetch() -> FetchResult:
    return fetch_new_api(
        provider_id=PROVIDER_ID,
        provider_name=PROVIDER_NAME,
        pricing_api_url=SOURCE_URL,
        public_pricing_url=DISPLAY_URL,
        channel_type="mixed",
        group=_GROUP,
    )
