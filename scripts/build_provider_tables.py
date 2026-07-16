"""Auto-generate provider tables in the three READMEs from data/providers.yaml.

Fixes two long-standing problems at once:
1. The China relays table was 7 columns, which squeezed Notes into 3-4 lines per
   row on GitHub's render. Reduces to 5 columns (Station / Type / Payment /
   Trust / Notes) — Notes now reads in one line for most entries.
2. Every prior provider PR had to hand-edit three READMEs alongside
   providers.yaml. Now PRs only touch providers.yaml; tables regenerate.

`notes` in providers.yaml can be either a string (English-only) or a dict
{en, zh-TW, zh-CN} for bilingual entries. Missing translations fall back to en.

Tables sit between `<!-- providers:<section>:start -->` and `:end -->` markers
in each README. Sections supported: china_relays, global_gateways,
self_hosted_alternatives, comparison_tools.

Run after editing providers.yaml. Idempotent.

CLI:
  python -m scripts.build_provider_tables           # write READMEs
  python -m scripts.build_provider_tables --check   # fail if READMEs drift
  python -m scripts.build_provider_tables --check-pr
      # PR-aware: reject hand-edited provider tables; allow yaml-only PRs
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

import yaml
from rich.console import Console

from ._paths import PROVIDERS_YAML, READMES, REPO_ROOT

console = Console()

LANGS_BY_FILE = {
    "README.md": "en",
    "README.zh-TW.md": "zh-TW",
    "README.zh-CN.md": "zh-CN",
}

PAYMENT_LABELS = {
    "en": {
        "alipay": "Alipay", "wechat": "WeChat", "card": "Card",
        "crypto": "Crypto", "enterprise-invoice": "Invoice",
    },
    "zh-TW": {
        "alipay": "支付寶", "wechat": "微信", "card": "卡",
        "crypto": "加密貨幣", "enterprise-invoice": "對公",
    },
    "zh-CN": {
        "alipay": "支付宝", "wechat": "微信", "card": "卡",
        "crypto": "加密货币", "enterprise-invoice": "对公",
    },
}

SECTION_HEADERS = {
    "china_relays": {
        "en": ["Station", "Type", "Payment", "Trust", "Notes"],
        "zh-TW": ["中轉站", "類型", "支付", "信任", "備註"],
        "zh-CN": ["中转站", "类型", "支付", "信任", "备注"],
    },
    "global_gateways": {
        "en": ["Service", "Type", "Payment", "Notes"],
        "zh-TW": ["服務", "類型", "支付", "備註"],
        "zh-CN": ["服务", "类型", "支付", "备注"],
    },
    "self_hosted_alternatives": {
        "en": ["Project", "Type", "Notes"],
        "zh-TW": ["專案", "類型", "備註"],
        "zh-CN": ["项目", "类型", "备注"],
    },
    "comparison_tools": {
        "en": ["Tool", "Notes"],
        "zh-TW": ["工具", "備註"],
        "zh-CN": ["工具", "备注"],
    },
}

TRUST_TEMPLATE = {
    "en": {
        "active": "active",
        "unverified": "unverified",
        "inactive": "inactive",
        "registered_suffix": " · registered",
        "date_prefix": " · ",
    },
    "zh-TW": {
        "active": "active", "unverified": "unverified", "inactive": "inactive",
        "registered_suffix": " · 已註冊", "date_prefix": " · ",
    },
    "zh-CN": {
        "active": "active", "unverified": "unverified", "inactive": "inactive",
        "registered_suffix": " · 已注册", "date_prefix": " · ",
    },
}

# Per-status emoji prefix on the Station/Service cell.
# 🟢 maintainer-verified active · 🟡 community-listed or unverified · 🔴 inactive
STATUS_EMOJI = {
    "active": "🟢",      # adjusted to 🟡 below if verified_by != maintainer
    "unverified": "🟡",
    "inactive": "🔴",
}

# Risk flag short labels, per language. Brief on purpose — these appear inside the Trust cell.
RISK_LABELS = {
    "en": {
        "operator_submitted": "operator-self",
        "no_entity": "no-entity",
        "reverse_channel": "reverse",
        "prices_too_cheap": "cheap-trap",
        "ran_away": "ran-away",
    },
    "zh-TW": {
        "operator_submitted": "自薦",
        "no_entity": "無主體",
        "reverse_channel": "逆向",
        "prices_too_cheap": "價過低",
        "ran_away": "跑路",
    },
    "zh-CN": {
        "operator_submitted": "自荐",
        "no_entity": "无主体",
        "reverse_channel": "逆向",
        "prices_too_cheap": "价过低",
        "ran_away": "跑路",
    },
}


def _notes_for(entry: dict, lang: str) -> str:
    notes = entry.get("notes") or ""
    if isinstance(notes, dict):
        return notes.get(lang) or notes.get("en") or ""
    return notes


def _payments_cell(entry: dict, lang: str) -> str:
    payments = entry.get("payment") or []
    labels = PAYMENT_LABELS[lang]
    if not payments:
        return "—"
    return "/".join(labels.get(p, p) for p in payments)


def _trust_cell(entry: dict, lang: str) -> str:
    tmpl = TRUST_TEMPLATE[lang]
    status = entry.get("status", "unverified")
    parts = [tmpl.get(status, status)]
    last_verified = entry.get("last_verified")
    if last_verified and status == "active":
        parts.append(f"{tmpl['date_prefix']}{last_verified}")
    if entry.get("entity_registered") is True:
        parts.append(tmpl["registered_suffix"])
    flags = entry.get("risk_flags") or []
    if flags:
        labels = RISK_LABELS[lang]
        rendered = ", ".join(labels.get(f, f) for f in flags)
        parts.append(f" · ⚠ {rendered}")
    return "".join(parts)


def _status_emoji(entry: dict) -> str:
    """Pick a status emoji. `active + verified_by maintainer` → 🟢; other active → 🟡; etc."""
    status = entry.get("status", "unverified")
    if status == "active" and entry.get("verified_by") != "maintainer":
        return "🟡"  # active but only community-verified — slightly less trusted
    return STATUS_EMOJI.get(status, "🟡")


def _station_cell(entry: dict) -> str:
    return f"{_status_emoji(entry)} [{entry['name']}]({entry['url']})"


def _render_china_row(entry: dict, lang: str) -> str:
    return "| {station} | {type} | {payment} | {trust} | {notes} |".format(
        station=_station_cell(entry),
        type=entry.get("type", "?"),
        payment=_payments_cell(entry, lang),
        trust=_trust_cell(entry, lang),
        notes=_notes_for(entry, lang),
    )


def _render_global_row(entry: dict, lang: str) -> str:
    return "| {svc} | {type} | {payment} | {notes} |".format(
        svc=_station_cell(entry),
        type=entry.get("type", "?"),
        payment=_payments_cell(entry, lang),
        notes=_notes_for(entry, lang),
    )


def _render_self_hosted_row(entry: dict, lang: str) -> str:
    return "| {proj} | {type} | {notes} |".format(
        proj=_station_cell(entry),
        type=entry.get("type", "?"),
        notes=_notes_for(entry, lang),
    )


def _render_comparison_row(entry: dict, lang: str) -> str:
    return "| {tool} | {notes} |".format(
        tool=_station_cell(entry),
        notes=_notes_for(entry, lang),
    )


ROW_RENDERERS = {
    "china_relays": _render_china_row,
    "global_gateways": _render_global_row,
    "self_hosted_alternatives": _render_self_hosted_row,
    "comparison_tools": _render_comparison_row,
}


def _render_section(section: str, entries: list[dict], lang: str) -> str:
    headers = SECTION_HEADERS[section][lang]
    header_row = "| " + " | ".join(headers) + " |"
    align_row = "|" + "|".join(["---"] * len(headers)) + "|"
    rows = [ROW_RENDERERS[section](e, lang) for e in entries if isinstance(e, dict)]
    return "\n".join([header_row, align_row, *rows])


def _update_markers(readme_text: str, section: str, body: str) -> tuple[str, bool]:
    start_marker = f"<!-- providers:{section}:start -->"
    end_marker = f"<!-- providers:{section}:end -->"
    if start_marker not in readme_text or end_marker not in readme_text:
        return readme_text, False
    start = readme_text.index(start_marker) + len(start_marker)
    end = readme_text.index(end_marker)
    new_text = readme_text[:start] + "\n" + body + "\n" + readme_text[end:]
    return new_text, True


def _extract_section(readme_text: str, section: str) -> str | None:
    start_marker = f"<!-- providers:{section}:start -->"
    end_marker = f"<!-- providers:{section}:end -->"
    if start_marker not in readme_text or end_marker not in readme_text:
        return None
    start = readme_text.index(start_marker) + len(start_marker)
    end = readme_text.index(end_marker)
    return readme_text[start:end].strip("\n")


def _load_doc() -> dict:
    return yaml.safe_load(PROVIDERS_YAML.read_text(encoding="utf-8"))


def _sections_present(doc: dict) -> list[str]:
    return [s for s in SECTION_HEADERS if s in doc]


def _expected_body(doc: dict, section: str, lang: str) -> str | None:
    entries = doc.get(section) or []
    if not entries:
        return None
    return _render_section(section, entries, lang)


def write_tables(doc: dict | None = None) -> int:
    doc = doc or _load_doc()
    sections_present = _sections_present(doc)
    console.print(f"sections to render: {sections_present}")

    updates = 0
    for readme_path in READMES:
        lang = LANGS_BY_FILE.get(readme_path.name)
        if not lang or not readme_path.exists():
            continue
        text = readme_path.read_text(encoding="utf-8")
        original = text
        for section in sections_present:
            body = _expected_body(doc, section, lang)
            if body is None:
                continue
            text, updated = _update_markers(text, section, body)
            if updated:
                updates += 1
        if text != original:
            readme_path.write_text(text, encoding="utf-8")
            console.print(f"[green]updated[/green] {readme_path.relative_to(REPO_ROOT)}")
        else:
            console.print(f"[dim]unchanged[/dim] {readme_path.relative_to(REPO_ROOT)}")
    console.rule()
    console.print(f"[bold green]Done.[/bold green] {updates} section block(s) updated across READMEs.")
    return 0


def check_tables(doc: dict | None = None) -> int:
    """Fail if any README provider section differs from data/providers.yaml."""
    doc = doc or _load_doc()
    problems: list[str] = []
    for readme_path in READMES:
        lang = LANGS_BY_FILE.get(readme_path.name)
        if not lang or not readme_path.exists():
            continue
        rel = str(readme_path.relative_to(REPO_ROOT))
        text = readme_path.read_text(encoding="utf-8")
        for section in _sections_present(doc):
            expected = _expected_body(doc, section, lang)
            if expected is None:
                continue
            actual = _extract_section(text, section)
            if actual is None:
                problems.append(f"{rel}: missing markers for providers:{section}")
                continue
            if actual.strip() != expected.strip():
                problems.append(
                    f"{rel}: providers:{section} out of sync with data/providers.yaml "
                    f"— run `python -m scripts.build_provider_tables`"
                )
    if problems:
        for p in problems:
            console.print(f"[red]✗[/red] {p}")
        console.print(f"[red]{len(problems)} README sync problem(s).[/red]")
        return 1
    console.print("[bold green]README provider tables match providers.yaml.[/bold green]")
    return 0


def _git_changed_files(base: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # Fallback: three-dot may fail on shallow clones; try two-dot.
        result = subprocess.run(
            ["git", "diff", "--name-only", base, "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        console.print(f"[red]git diff failed:[/red] {result.stderr.strip()}")
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _git_show(base: str, rel_path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{base}:{rel_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _resolve_pr_base() -> str | None:
    """Prefer explicit env (CI), else upstream main/master merge-base."""
    for key in ("PR_BASE_SHA", "GITHUB_BASE_SHA"):
        val = os.environ.get(key)
        if val:
            return val
    # Local convenience: merge-base with origin/main or main.
    for ref in ("origin/main", "main", "origin/master", "master"):
        result = subprocess.run(
            ["git", "merge-base", "HEAD", ref],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return None


def check_pr(base: str | None = None) -> int:
    """PR hygiene for generated README tables.

    Policy:
      - Hand-editing provider table blocks without touching providers.yaml → fail
      - Touching both yaml + README tables but leaving them out of sync → fail
      - Yaml-only PRs (preferred) → pass even if tables lag until maintainer regen
      - README edits outside provider markers → pass
    """
    base = base or _resolve_pr_base()
    if not base:
        console.print(
            "[yellow]![/yellow] No PR base ref found; falling back to full --check"
        )
        return check_tables()

    changed = _git_changed_files(base)
    if not changed:
        console.print("[dim]No changed files vs base — skip README PR check.[/dim]")
        return 0

    yaml_changed = "data/providers.yaml" in changed
    doc = _load_doc()
    problems: list[str] = []

    for readme_path in READMES:
        lang = LANGS_BY_FILE.get(readme_path.name)
        if not lang or not readme_path.exists():
            continue
        rel = str(readme_path.relative_to(REPO_ROOT))
        readme_changed = rel in changed
        text = readme_path.read_text(encoding="utf-8")
        base_text = _git_show(base, rel) if readme_changed else None

        for section in _sections_present(doc):
            expected = _expected_body(doc, section, lang)
            if expected is None:
                continue
            actual = _extract_section(text, section)
            if actual is None:
                continue
            in_sync = actual.strip() == expected.strip()
            if in_sync:
                continue

            base_section = (
                _extract_section(base_text, section) if base_text is not None else None
            )
            section_edited = (
                base_section is not None
                and base_section.strip() != actual.strip()
            )

            if not yaml_changed and section_edited:
                problems.append(
                    f"{rel}: providers:{section} was hand-edited without changing "
                    f"data/providers.yaml — edit the YAML only; tables auto-regenerate"
                )
            elif yaml_changed and readme_changed and section_edited:
                problems.append(
                    f"{rel}: providers:{section} was edited but does not match "
                    f"data/providers.yaml — run `python -m scripts.build_provider_tables` "
                    f"or leave the README tables untouched"
                )

    if problems:
        for p in problems:
            console.print(f"[red]✗[/red] {p}")
        console.print(f"[red]{len(problems)} PR README hygiene problem(s).[/red]")
        return 1
    console.print(
        f"[bold green]PR README check passed[/bold green] "
        f"(base={base[:12]}…, yaml_changed={yaml_changed})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if README provider tables drift from providers.yaml",
    )
    parser.add_argument(
        "--check-pr",
        action="store_true",
        help="PR-aware check: block hand-edited tables; allow yaml-only PRs",
    )
    parser.add_argument(
        "--base",
        default=None,
        help="Git base SHA/ref for --check-pr (default: env or origin/main merge-base)",
    )
    args = parser.parse_args(argv)

    if args.check and args.check_pr:
        console.print("[red]Use only one of --check / --check-pr[/red]")
        return 2
    if args.check:
        return check_tables()
    if args.check_pr:
        return check_pr(base=args.base)
    return write_tables()


if __name__ == "__main__":
    raise SystemExit(main())
