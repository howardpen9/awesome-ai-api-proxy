"""Weekly human-in-the-loop CLI for reviewing community-submitted prices.

Workflow (Howard, every Sunday):

  1. `python -m scripts.review_submissions`
  2. Each open issue labeled `pending-price-review` opens in the browser
     alongside the relay's pricing page so you can cross-check screenshots.
  3. Prompt accepts `a` (accept) / `r` (reject) / `s` (skip) / `q` (quit).
  4. On accept: parses the markdown price table from the issue body,
     appends entries to the matching provider's `submitted_prices` in
     providers.yaml, posts a thank-you comment, closes the issue.
  5. After all issues processed, runs build_prices + build_provider_tables
     so the README / charts pick up new data immediately.

Requires `gh` CLI authenticated.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import webbrowser
from datetime import date

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from ._paths import PROVIDERS_YAML

console = Console()

REPO = "howardpen9/awesome-ai-api-proxy"
LABEL = "pending-price-review"

ALLOWED_UNITS = {
    "per_1m_input_tokens",
    "per_1m_output_tokens",
    "per_1m_input_cache_read_tokens",
    "per_image",
    "per_second",
    "per_request",
}

THANK_YOU_COMMENT = """Thanks for the submission! Verified against the screenshot, prices added to `data/providers.yaml` under `submitted_prices` and will appear in the next [`data/prices.latest.json`](https://github.com/howardpen9/awesome-ai-api-proxy/blob/main/data/prices.latest.json) refresh.

Marked as `method: manual, confidence: medium` — these prices will show with a `†` footnote in the README tables. They'll be promoted to maintainer-verified once an automated fetcher covers this station."""

REJECT_TEMPLATE = """Thanks for the submission. Closing without merge — reason: {reason}

You can re-open / open a new issue once the gap is filled."""


def gh_list_issues() -> list[dict]:
    out = subprocess.run(
        ["gh", "issue", "list", "--repo", REPO, "--label", LABEL,
         "--state", "open", "--limit", "30",
         "--json", "number,title,body,author,createdAt,url"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def gh_comment(issue_number: int, body: str) -> None:
    subprocess.run(
        ["gh", "issue", "comment", str(issue_number),
         "--repo", REPO, "--body", body],
        check=True,
    )


def gh_close(issue_number: int) -> None:
    subprocess.run(
        ["gh", "issue", "close", str(issue_number), "--repo", REPO],
        check=True,
    )


_EMPTY_FORM_VALUES = {"", "_no response_", "n/a", "none", "-", "_"}


def _issue_field(body: str, needle: str) -> str | None:
    """Read a GitHub issue-form heading or a legacy **bold** markdown label."""
    form = re.search(
        rf"^###[^\n]*{re.escape(needle)}[^\n]*\n+(.+)",
        body,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if form:
        line = form.group(1).splitlines()[0].strip()
        if line.lower() not in _EMPTY_FORM_VALUES:
            return line
    bold = re.search(
        rf"\*\*[^*]*{re.escape(needle)}[^*]*\*\*[:：]?\s*(.+)",
        body,
        flags=re.IGNORECASE,
    )
    if bold:
        line = bold.group(1).strip()
        if line.lower() not in _EMPTY_FORM_VALUES:
            return line
    return None


def parse_prices_from_body(body: str) -> tuple[str | None, str | None, list[dict]]:
    """Extract station name, screenshot/source url, and price rows from issue body.

    Accepts GitHub issue-form output (``### Station name``) and the legacy
    ``**Station name:**`` markdown template.
    Returns (station, source_url, rows). rows is a list of
    {canonical_model, unit, price_usd}.
    """
    station = _issue_field(body, "Station name")
    raw_src = _issue_field(body, "Pricing page URL")
    src_match = re.search(r"https?://\S+", raw_src or "")
    source_url = src_match.group(0).rstrip(").,]") if src_match else None

    rows: list[dict] = []
    # Look for any markdown table where columns include canonical_model / unit / price_usd.
    in_table = False
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("|") and "canonical_model" in line and "unit" in line:
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table:
            if not line.startswith("|"):
                in_table = False
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 3:
                continue
            try:
                price = float(cols[2].lstrip("$"))
            except ValueError:
                continue
            if cols[1] not in ALLOWED_UNITS:
                continue
            rows.append({
                "canonical_model": cols[0],
                "unit": cols[1],
                "price_usd": price,
            })
    return station, source_url, rows


def find_provider_entry(doc: dict, station_name: str) -> tuple[str, int] | None:
    name_lc = station_name.lower()
    for section, entries in doc.items():
        if not isinstance(entries, list):
            continue
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            if entry.get("name", "").lower() == name_lc:
                return section, idx
            # Loose match: handle "UiUiAPI" vs "UIUIAPI"
            if name_lc in entry.get("name", "").lower():
                return section, idx
    return None


def append_submitted(
    doc: dict, section: str, idx: int, rows: list[dict],
    source_url: str | None, screenshot_url: str | None,
    submitted_by: str, submitted_by_role: str,
) -> None:
    entry = doc[section][idx]
    pricing = entry.setdefault("pricing", {})
    if "pricing_url" not in pricing and source_url:
        pricing["pricing_url"] = source_url
    pricing.setdefault("pricing_currency", "USD")
    submitted = pricing.setdefault("submitted_prices", [])
    today = date.today().isoformat()
    for row in rows:
        submitted.append({
            **row,
            "source_url": source_url or pricing.get("pricing_url", ""),
            "screenshot_url": screenshot_url or "",
            "captured_at": today,
            "submitted_by": submitted_by,
            "submitted_by_role": submitted_by_role,
            "verified_at": today,
            "verified_by": "maintainer",
        })


def main() -> int:
    issues = gh_list_issues()
    if not issues:
        console.print("[bold green]No pending submissions.[/bold green]")
        return 0

    console.rule(f"[bold]{len(issues)} pending submission(s)")
    doc = yaml.safe_load(PROVIDERS_YAML.read_text(encoding="utf-8"))
    changed = False

    for issue in issues:
        console.rule(f"#{issue['number']} · {issue['title']}")
        console.print(f"[dim]by @{issue['author']['login']} · {issue['createdAt']}[/dim]")
        webbrowser.open(issue["url"])

        station, source_url, rows = parse_prices_from_body(issue["body"])
        console.print(f"\n[bold]Parsed:[/bold] station={station!r} · source={source_url!r} · rows={len(rows)}")
        if rows:
            for r in rows[:8]:
                console.print(f"  {r['canonical_model']:30s} {r['unit']:30s} ${r['price_usd']}")
            if len(rows) > 8:
                console.print(f"  ...+{len(rows) - 8} more")

        if not station or not rows:
            console.print("[red]Could not parse station/rows — please review issue manually.[/red]")
            action = Prompt.ask("[a]ccept manually-edited / [r]eject / [s]kip", choices=["a", "r", "s"], default="s")
        else:
            action = Prompt.ask("[a]ccept / [r]eject / [s]kip / [q]uit", choices=["a", "r", "s", "q"], default="s")

        if action == "q":
            break
        if action == "s":
            continue
        if action == "r":
            reason = Prompt.ask("Reason for reject")
            gh_comment(issue["number"], REJECT_TEMPLATE.format(reason=reason))
            gh_close(issue["number"])
            continue
        # action == "a"
        if not station or not rows:
            console.print("[yellow]Skipping accept — re-run after editing the issue body.[/yellow]")
            continue
        match = find_provider_entry(doc, station)
        if not match:
            console.print(f"[red]No provider matching '{station}' in providers.yaml.[/red]")
            console.print("Add the provider entry first (with status: unverified), then re-run.")
            continue
        section, idx = match
        role = Prompt.ask("Submitter role", choices=["operator", "community"], default="community")
        append_submitted(
            doc, section, idx, rows,
            source_url=source_url,
            screenshot_url=issue["url"],
            submitted_by=f"@{issue['author']['login']}",
            submitted_by_role=role,
        )
        gh_comment(issue["number"], THANK_YOU_COMMENT)
        gh_close(issue["number"])
        changed = True
        console.print(f"[green]✓ accepted into {section}[{idx}].pricing.submitted_prices[/green]")

    if changed:
        PROVIDERS_YAML.write_text(
            yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=200),
            encoding="utf-8",
        )
        console.rule()
        console.print("[bold]Rebuilding outputs...[/bold]")
        subprocess.run([sys.executable, "-m", "scripts.build_prices"], check=True)
        subprocess.run([sys.executable, "-m", "scripts.build_provider_tables"], check=True)
        console.print("[bold green]Done. Commit + push the diff when ready.[/bold green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
