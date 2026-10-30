"""Entry point: read providers.yaml, run all fetchers (or a single one), write snapshots.

Usage:
    python -m scripts.scrape                # run every fetcher
    python -m scripts.scrape openrouter     # run one
    python -m scripts.scrape atlascloud relaydance  # run several
"""

from __future__ import annotations

import os
import sys
import traceback

import yaml
from rich.console import Console

from fetchers import get_fetcher
from fetchers._common import write_error, write_snapshot

from ._paths import PROVIDERS_YAML, SNAPSHOTS_DIR

console = Console()


def include_in_scrape(entry: dict) -> bool:
    """True when this provider should be fetched on a price refresh.

    Inactive (shut down / ran away) providers keep their catalog entry and
    historical snapshots, but their pricing endpoints can keep answering
    after service ends. Those prices are not purchasable. bltcy's status
    change itself is PR #157; this is the shared skip.
    """
    pricing = entry.get("pricing") or {}
    if not pricing.get("fetcher"):
        return False
    return entry.get("status") != "inactive"


def discover_fetchers() -> dict[str, str]:
    """Walk providers.yaml and return {fetcher_id: provider_name}.

    Providers with `status: inactive` are skipped.
    """
    raw = yaml.safe_load(PROVIDERS_YAML.read_text(encoding="utf-8"))
    found: dict[str, str] = {}
    for _section, entries in raw.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if not include_in_scrape(entry):
                fetcher = (entry.get("pricing") or {}).get("fetcher")
                if fetcher and entry.get("status") == "inactive":
                    console.print(f"[dim]skip {fetcher}: status inactive[/dim]")
                continue
            fetcher = entry["pricing"]["fetcher"]
            found[fetcher] = entry.get("name", fetcher)
    return found


def run_fetcher(fetcher_id: str, display_name: str) -> bool:
    """Run one fetcher. Any exception is logged and skipped.

    Import failures (a missing module, or a dependency that raises at import
    time) must be caught here. They happen inside get_fetcher(), before fetch()
    runs, and previously aborted the whole scrape.
    """
    console.rule(f"[bold]{display_name} ({fetcher_id})")
    try:
        fn = get_fetcher(fetcher_id)
        result = fn()
    except Exception as exc:
        err_path = write_error(fetcher_id, exc, SNAPSHOTS_DIR)
        console.print(f"[red]fail[/red] {type(exc).__name__}: {exc}")
        console.print(f"       error log → {err_path.relative_to(SNAPSHOTS_DIR.parent.parent)}")
        console.print(traceback.format_exc())
        return False
    snapshot_path = write_snapshot(result, SNAPSHOTS_DIR)
    console.print(
        f"[green]ok[/green] {len(result.records)} records "
        f"(from {result.raw_model_count} raw models) → {snapshot_path.relative_to(SNAPSHOTS_DIR.parent.parent)}"
    )
    return True


def main(argv: list[str]) -> int:
    available = discover_fetchers()
    if not available:
        console.print("[red]No providers in providers.yaml have a pricing.fetcher.[/red]")
        return 1

    if argv:
        requested = argv
        unknown = [f for f in requested if f not in available]
        if unknown:
            console.print(f"[red]Unknown fetcher(s):[/red] {unknown}")
            console.print(f"available: {sorted(available)}")
            return 2
        to_run = [(f, available[f]) for f in requested]
    else:
        to_run = sorted(available.items())

    failed: list[str] = []
    for fid, name in to_run:
        if not run_fetcher(fid, name):
            failed.append(fid)

    succeeded = len(to_run) - len(failed)
    console.rule()
    console.print(f"Done. {succeeded}/{len(to_run)} fetchers succeeded.")
    if failed:
        console.print("[red]Failed fetchers:[/red] " + ", ".join(failed))
        # Visible on the Actions run without failing the step. The weekly
        # workflow reads *.error.json and puts the same names in the PR body.
        if os.environ.get("GITHUB_ACTIONS"):
            print(f"::warning::Failed fetchers: {', '.join(failed)}", flush=True)
    _write_github_summary(succeeded, len(to_run), failed)
    # One broken fetcher must not abort the refresh. Exit non-zero only when
    # nothing succeeded, so we don't publish an empty price file.
    if succeeded == 0:
        return 3
    return 0


def _write_github_summary(succeeded: int, total: int, failed: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    failed_text = ", ".join(f"`{fid}`" for fid in failed) if failed else "(none)"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(
            "\n".join(
                [
                    "### Scrape",
                    "",
                    f"Succeeded: {succeeded}/{total}",
                    "",
                    f"Failed fetchers: {failed_text}",
                    "",
                ]
            )
        )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
