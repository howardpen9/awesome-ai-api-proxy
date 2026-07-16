"""Schema / sanity checks for data/*.

Used by CI on PRs and also as a final gate in the weekly workflow.
Exit code 0 = OK, 1 = problems found.

Beyond field presence / enums, enforces contribution hygiene (P0):
  - HTTPS-only URLs, no referral / UTM query params
  - Duplicate name / URL detection
  - notes length + marketing-ban phrases
  - status honesty (active requires maintainer verify; operator_submitted ≠ active)
  - crude type-vs-notes contradiction for reverse channels
"""

from __future__ import annotations

import json
import re
import sys
from urllib.parse import parse_qs, urlparse

import yaml
from rich.console import Console

from ._paths import CANONICAL_YAML, PRICES_LATEST, PROVIDERS_YAML

console = Console()

REQUIRED_PROVIDER_FIELDS = {"name", "url", "type", "status"}
ALLOWED_TYPES = {
    "official-relay",
    "mixed",
    "reverse",
    "aggregator",
    "gateway-oss",
    "observability",
    "comparison",
    "list",
}
ALLOWED_STATUS = {"active", "unverified", "inactive"}
ALLOWED_RISK_FLAGS = {
    "operator_submitted",
    "no_entity",
    "reverse_channel",
    "prices_too_cheap",
    "ran_away",
}
ALLOWED_UNITS = {
    "per_1m_input_tokens",
    "per_1m_output_tokens",
    "per_1m_input_cache_read_tokens",
    "per_image",
    "per_second",
    "per_request",
}

# Soft ceiling so technical bilingual notes still fit (UnoRouter ~305 today).
# Walls of marketing copy almost always exceed this.
NOTES_MAX_CHARS = 360

# Tracking / affiliate query keys (case-insensitive).
_REFERRAL_QUERY_KEYS = frozenset({
    "ref",
    "affiliate",
    "invite",
    "campaignid",
    "campaign_id",
    "gclid",
    "fbclid",
    "mc_cid",
    "mc_eid",
    "referral",
    "referrer",
})

# Promotional / superlative phrases we reject in notes (editorial rule).
# Keep tight — factual uses of "cheap" / "lowest-price" in existing entries are OK.
_NOTES_BAN_RE = re.compile(
    r"(?i)"
    r"("
    r"\b#\s*1\b"
    r"|\bno\.?\s*1\b"
    r"|\bworld'?s\s+best\b"
    r"|\bthe\s+best\b"
    r"|\bbest\s+(in|of|api|relay|gateway|provider)\b"
    r"|\bnumber\s+one\b"
    r"|强烈推荐|强烈推薦|强烈安利"
    r"|不降智|官方不降智"
    r"|最强推荐|最強推薦"
    r")"
)

# Notes implying reverse channel while type claims official-relay.
_REVERSE_HINT_RE = re.compile(
    r"(?i)(reverse[- ]engineered|\breverse\b|逆向|非官转|非官轉)"
)


def _problem(messages: list[str], msg: str) -> None:
    console.print(f"[red]✗[/red] {msg}")
    messages.append(msg)


_REQUIRED_SUBMITTED_FIELDS = {
    "canonical_model", "unit", "price_usd", "source_url",
    "captured_at", "submitted_by", "verified_by",
}


def _normalize_url_key(url: str) -> str | None:
    """Host + path identity (ignore scheme, www, query, fragment, trailing slash).

    Multiple GitHub repos share host `github.com` — that is fine. Two entries
    pointing at the same page are not.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return None
    path = (parsed.path or "").rstrip("/").lower()
    return f"{host}{path}"


def _check_url(problems: list[str], label: str, url: object) -> None:
    if not isinstance(url, str) or not url.strip():
        _problem(problems, f"{label}: url is empty")
        return
    try:
        parsed = urlparse(url)
    except ValueError:
        _problem(problems, f"{label}: unparseable url: {url!r}")
        return
    if parsed.scheme != "https":
        _problem(problems, f"{label}: url must be https:// (got {parsed.scheme!r}): {url}")
        return
    if not parsed.netloc:
        _problem(problems, f"{label}: url missing host: {url}")
        return
    # Flatten query keys; also flag bare utm_* regardless of value.
    keys = {k.lower() for k in parse_qs(parsed.query, keep_blank_values=True)}
    bad = sorted(
        k for k in keys
        if k in _REFERRAL_QUERY_KEYS or k.startswith("utm_")
    )
    if bad:
        _problem(
            problems,
            f"{label}: referral/tracking query params not allowed ({', '.join(bad)}): {url}",
        )


def _iter_note_texts(notes: object) -> list[tuple[str, str]]:
    if notes is None:
        return []
    if isinstance(notes, str):
        return [("notes", notes)]
    if isinstance(notes, dict):
        return [(f"notes.{k}", v) for k, v in notes.items() if isinstance(v, str)]
    return []


def _check_notes(problems: list[str], section: str, name: str, notes: object) -> None:
    if notes is None:
        return
    if not isinstance(notes, (str, dict)):
        _problem(problems, f"{section}: '{name}' notes must be string or dict")
        return
    if isinstance(notes, dict) and "en" not in notes:
        _problem(problems, f"{section}: '{name}' bilingual notes must include 'en' key")
    for label, text in _iter_note_texts(notes):
        if len(text) > NOTES_MAX_CHARS:
            _problem(
                problems,
                f"{section}: '{name}' {label} is {len(text)} chars "
                f"(max {NOTES_MAX_CHARS}; keep to one factual sentence)",
            )
        m = _NOTES_BAN_RE.search(text)
        if m:
            _problem(
                problems,
                f"{section}: '{name}' {label} has marketing/superlative phrasing "
                f"{m.group(0)!r} — rewrite factually",
            )


def _check_status_honesty(problems: list[str], section: str, entry: dict) -> None:
    name = entry.get("name", "?")
    status = entry.get("status")
    risk_flags = entry.get("risk_flags") or []
    if not isinstance(risk_flags, list):
        return

    if "operator_submitted" in risk_flags and status == "active":
        _problem(
            problems,
            f"{section}: '{name}' has risk_flags operator_submitted but status=active "
            f"— self-submissions must use status: unverified",
        )

    if status == "active":
        if entry.get("verified_by") != "maintainer":
            _problem(
                problems,
                f"{section}: '{name}' status=active requires verified_by: maintainer "
                f"(got {entry.get('verified_by')!r}); use status: unverified otherwise",
            )
        if not entry.get("last_verified"):
            _problem(
                problems,
                f"{section}: '{name}' status=active requires last_verified (YYYY-MM-DD)",
            )


def _check_type_notes_consistency(problems: list[str], section: str, entry: dict) -> None:
    name = entry.get("name", "?")
    if entry.get("type") != "official-relay":
        return
    for label, text in _iter_note_texts(entry.get("notes")):
        if _REVERSE_HINT_RE.search(text):
            _problem(
                problems,
                f"{section}: '{name}' type=official-relay but {label} mentions reverse/逆向 "
                f"— pick an honest type",
            )
            return


def _validate_submitted_prices(problems: list[str], section: str, entry: dict, submitted: list) -> None:
    name = entry.get("name", "?")
    for i, sp in enumerate(submitted):
        if not isinstance(sp, dict):
            _problem(problems, f"{section}: '{name}' submitted_prices[{i}] is not a dict")
            continue
        missing = _REQUIRED_SUBMITTED_FIELDS - sp.keys()
        if missing:
            _problem(problems, f"{section}: '{name}' submitted_prices[{i}] missing: {sorted(missing)}")
        if sp.get("unit") not in ALLOWED_UNITS:
            _problem(problems, f"{section}: '{name}' submitted_prices[{i}] invalid unit: {sp.get('unit')!r}")
        price = sp.get("price_usd")
        if price is None or not (isinstance(price, (int, float)) and 0 < price < 1000):
            _problem(problems, f"{section}: '{name}' submitted_prices[{i}] suspicious price_usd: {price!r}")
        src = sp.get("source_url")
        if src:
            _check_url(problems, f"{section}: '{name}' submitted_prices[{i}].source_url", src)


def validate_providers(problems: list[str]) -> None:
    raw = yaml.safe_load(PROVIDERS_YAML.read_text(encoding="utf-8"))
    seen_names: dict[str, str] = {}
    seen_urls: dict[str, str] = {}

    for section, entries in raw.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name", "?")
            missing = REQUIRED_PROVIDER_FIELDS - entry.keys()
            if missing:
                _problem(problems, f"{section}: '{name}' missing fields: {missing}")
            if entry.get("type") not in ALLOWED_TYPES:
                _problem(problems, f"{section}: '{name}' has invalid type: {entry.get('type')!r}")
            if entry.get("status") not in ALLOWED_STATUS:
                _problem(problems, f"{section}: '{name}' has invalid status: {entry.get('status')!r}")

            risk_flags = entry.get("risk_flags") or []
            if not isinstance(risk_flags, list):
                _problem(problems, f"{section}: '{name}' risk_flags must be a list")
            else:
                for flag in risk_flags:
                    if flag not in ALLOWED_RISK_FLAGS:
                        _problem(
                            problems,
                            f"{section}: '{name}' has invalid risk_flag: {flag!r} "
                            f"(allowed: {sorted(ALLOWED_RISK_FLAGS)})",
                        )

            url = entry.get("url")
            if url is not None:
                _check_url(problems, f"{section}: '{name}' url", url)
                url_key = _normalize_url_key(url) if isinstance(url, str) else None
                if url_key:
                    prev = seen_urls.get(url_key)
                    if prev:
                        _problem(
                            problems,
                            f"{section}: '{name}' url {url_key!r} duplicates {prev}",
                        )
                    else:
                        seen_urls[url_key] = f"{section}:'{name}'"

            if isinstance(name, str) and name != "?":
                key = name.strip().lower()
                prev = seen_names.get(key)
                if prev:
                    _problem(problems, f"{section}: duplicate name {name!r} (also at {prev})")
                else:
                    seen_names[key] = f"{section}"

            pricing = entry.get("pricing")
            if pricing:
                # pricing_url + pricing_currency always required; fetcher optional
                # when submitted_prices is present (manual-only providers).
                for required in ("pricing_url", "pricing_currency"):
                    if required not in pricing:
                        _problem(
                            problems,
                            f"{section}: '{name}' pricing block missing '{required}'",
                        )
                if "fetcher" not in pricing and not pricing.get("submitted_prices"):
                    _problem(
                        problems,
                        f"{section}: '{name}' pricing block needs either 'fetcher' or 'submitted_prices'",
                    )
                if pricing.get("pricing_url"):
                    _check_url(problems, f"{section}: '{name}' pricing.pricing_url", pricing["pricing_url"])
                if pricing.get("api_url"):
                    _check_url(problems, f"{section}: '{name}' pricing.api_url", pricing["api_url"])
                _validate_submitted_prices(problems, section, entry, pricing.get("submitted_prices") or [])

            _check_notes(problems, section, name, entry.get("notes"))
            _check_status_honesty(problems, section, entry)
            _check_type_notes_consistency(problems, section, entry)


def validate_canonical(problems: list[str]) -> None:
    doc = yaml.safe_load(CANONICAL_YAML.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for entry in doc.get("canonical_models", []):
        cm = entry.get("canonical")
        if not cm:
            _problem(problems, f"canonical model missing 'canonical' field: {entry}")
            continue
        if cm in seen:
            _problem(problems, f"duplicate canonical name: {cm}")
        seen.add(cm)
        if entry.get("tier") not in (1, 2, 3, 4):
            _problem(problems, f"canonical {cm} has invalid tier: {entry.get('tier')!r}")


def validate_prices(problems: list[str]) -> None:
    if not PRICES_LATEST.exists():
        console.print("[yellow]![/yellow] prices.latest.json missing — skip (run build_prices first)")
        return
    doc = json.loads(PRICES_LATEST.read_text(encoding="utf-8"))
    if "records" not in doc:
        _problem(problems, "prices.latest.json missing 'records'")
        return
    for i, rec in enumerate(doc["records"]):
        for required in ("provider_id", "raw_model_name", "unit", "price_usd", "source_url", "captured_at", "method"):
            if required not in rec:
                _problem(problems, f"record[{i}] missing '{required}'")
        if rec.get("unit") not in ALLOWED_UNITS:
            _problem(problems, f"record[{i}] has invalid unit: {rec.get('unit')!r}")
        price = rec.get("price_usd")
        # Real-world extreme prices exist (some bltcy thinking variants at $1750/1M).
        # Keep an upper bound for sanity, but loose enough not to false-positive.
        if price is not None and not (price > 0 and price < 5000):
            _problem(
                problems,
                f"record[{i}] suspicious price_usd: {price} "
                f"({rec.get('provider_name')} / {rec.get('raw_model_name')})",
            )


def main() -> int:
    problems: list[str] = []
    console.rule("[bold]Validate providers.yaml")
    validate_providers(problems)
    console.rule("[bold]Validate canonical-models.yaml")
    validate_canonical(problems)
    console.rule("[bold]Validate prices.latest.json")
    validate_prices(problems)
    console.rule()
    if problems:
        console.print(f"[red]{len(problems)} problem(s) found.[/red]")
        return 1
    console.print("[bold green]All validations passed.[/bold green]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
