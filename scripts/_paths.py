"""Centralize repo paths so scripts don't depend on each other for layout."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
PROVIDERS_YAML = DATA_DIR / "providers.yaml"
CANONICAL_YAML = DATA_DIR / "canonical-models.yaml"
PRICES_LATEST = DATA_DIR / "prices.latest.json"
PRICES_HISTORY = DATA_DIR / "prices.history.jsonl"
DOCS_DIR = REPO_ROOT / "docs"
PRICES_DOC = DOCS_DIR / "prices.md"
LLMS_TXT = REPO_ROOT / "llms.txt"
DOCS_LLMS_TXT = DOCS_DIR / "llms.txt"
PRICES_INDEX = DOCS_DIR / "prices-index.json"
READMES = [
    REPO_ROOT / "README.md",
    REPO_ROOT / "README.zh-TW.md",
    REPO_ROOT / "README.zh-CN.md",
]
