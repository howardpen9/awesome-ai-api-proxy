"""Per-provider price fetchers.

Each fetcher module exposes:
    PROVIDER_ID: str
    fetch() -> list[PriceRecord]

scripts/scrape.py imports and dispatches.
"""

from __future__ import annotations

from importlib import import_module
from typing import Callable

REGISTRY: dict[str, str] = {
    "openrouter": "fetchers.openrouter",
    "atlascloud": "fetchers.atlascloud",
    "relaydance": "fetchers.relaydance",
    "uiuiapi": "fetchers.uiuiapi",
    "bltcy": "fetchers.bltcy",
    "unorouter": "fetchers.unorouter",
    "quicksilverpro": "fetchers.quicksilverpro",
    "wappkit": "fetchers.wappkit",
    "teamorouter": "fetchers.teamorouter",
}


def get_fetcher(provider_id: str) -> Callable[[], list]:
    module_path = REGISTRY.get(provider_id)
    if not module_path:
        raise KeyError(f"unknown provider_id: {provider_id!r} (known: {sorted(REGISTRY)})")
    return import_module(module_path).fetch
