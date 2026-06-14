"""Shared types and helpers for fetchers.

Schema is designed for LLM-agent citation: every record carries source_url,
captured_at, and method so an agent can quote the price with provenance.
See docs/agent-citation.md.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal

import httpx
from pydantic import BaseModel, Field

Unit = Literal[
    "per_1m_input_tokens",
    "per_1m_output_tokens",
    "per_1m_input_cache_read_tokens",
    "per_image",
    "per_second",
    "per_request",
]

ChannelType = Literal["official-relay", "mixed", "reverse", "aggregator", "gateway-oss", "unknown"]
Method = Literal["json-api", "dom", "playwright", "manual"]
Confidence = Literal["high", "medium", "low"]


class PriceRecord(BaseModel):
    """One model × one unit × one provider snapshot."""

    provider_id: str
    provider_name: str
    raw_model_name: str
    canonical_model: str | None = None  # resolved by build_prices.py against canonical-models.yaml
    model_family: str | None = None
    tier: int | None = None
    channel_type: ChannelType = "unknown"
    unit: Unit
    price_usd: float
    # When a provider advertises a discount, price_usd is the discounted (paid) price,
    # origin_price_usd is the pre-discount list price, and discount_pct is how much off
    # (e.g. 35.0 means -35%). All None when the provider has no discount concept.
    origin_price_usd: float | None = None
    discount_pct: float | None = None
    source_url: str
    captured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: Confidence = "high"
    method: Method
    notes: str | None = None


class FetchResult(BaseModel):
    provider_id: str
    captured_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    records: list[PriceRecord]
    raw_model_count: int  # total models seen on the source, even ones we couldn't price


def http_client(*, timeout: float = 20.0) -> httpx.Client:
    """Single client config so retries/headers/UA stay consistent."""
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; awesome-ai-api-proxy-bot/0.1; "
                "+https://github.com/howardpen9/awesome-ai-api-proxy)"
            ),
            "Accept": "application/json, text/html",
        },
    )


def per_token_to_per_1m(price_per_token: float | str) -> float:
    """OpenRouter expresses prices as $/token. Convert to $/1M tokens."""
    return float(price_per_token) * 1_000_000


_NEXT_F_RE = re.compile(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', re.S)


def next_f_blob(html: str) -> str:
    """Reassemble a Next.js RSC payload from its self.__next_f.push() chunks.

    Atlas Cloud and docs.x.ai both server-render their pricing tables into this
    stream instead of a public JSON API, so we concatenate the chunks and undo
    the JS string escaping to get one searchable blob of embedded JSON.
    """
    blob = "".join(_NEXT_F_RE.findall(html))
    return blob.encode().decode("unicode_escape", errors="ignore")


def iter_objects_containing(blob: str, needle: str) -> Iterator[dict]:
    """Yield each JSON object in `blob` whose text contains `needle`.

    Walks back from every `needle` hit to the enclosing object's opening brace,
    then forward to its matching close, and json.loads the slice. Objects that
    fail to parse (truncated/nested oddly) are skipped silently.
    """
    for m in re.finditer(re.escape(needle), blob):
        start = _enclosing_brace(blob, m.start())
        if start is None:
            continue
        raw = _balanced_object(blob, start)
        if raw is None:
            continue
        try:
            yield json.loads(raw)
        except json.JSONDecodeError:
            continue


def _enclosing_brace(s: str, pos: int) -> int | None:
    depth = 0
    i = pos
    while i > 0:
        c = s[i]
        if c == "}":
            depth += 1
        elif c == "{":
            if depth == 0:
                return i
            depth -= 1
        i -= 1
    return None


def _balanced_object(s: str, start: int) -> str | None:
    depth = 0
    for j in range(start, len(s)):
        c = s[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start : j + 1]
    return None


def write_snapshot(result: FetchResult, snapshots_dir: Path) -> Path:
    """Write one fetcher's normalized output to data/snapshots/<date>/<provider>.json."""
    date_str = result.captured_at[:10]
    out_dir = snapshots_dir / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{result.provider_id}.json"
    out_path.write_text(
        json.dumps(result.model_dump(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_path


def write_error(provider_id: str, exc: BaseException, snapshots_dir: Path) -> Path:
    """When a fetcher fails, drop an .error.json so the weekly PR shows what broke."""
    now = datetime.now(timezone.utc).isoformat()
    date_str = now[:10]
    out_dir = snapshots_dir / date_str
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{provider_id}.error.json"
    out_path.write_text(
        json.dumps(
            {
                "provider_id": provider_id,
                "captured_at": now,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return out_path
