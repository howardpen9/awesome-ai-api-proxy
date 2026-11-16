"""Shared fixtures for validate.py unit tests."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def minimal_provider_entry(
    *,
    name: str = "Test Provider",
    url: str = "https://example.com",
    type: str = "official",
    status: str = "unverified",
    **extra: object,
) -> dict:
    """One provider dict that satisfies required fields and status rules."""
    entry: dict = {
        "name": name,
        "url": url,
        "type": type,
        "status": status,
    }
    entry.update(extra)
    return entry


def providers_doc(*sections: tuple[str, list[dict]]) -> dict:
    """Build a providers.yaml-shaped document (section -> list of entries)."""
    doc: dict = {"schema_version": 2}
    for section, entries in sections:
        doc[section] = entries
    return doc


@pytest.fixture
def write_providers_yaml(tmp_path: Path):
    """Write a minimal providers YAML file under tmp_path and return its Path."""

    def _write(doc: dict) -> Path:
        path = tmp_path / "providers.yaml"
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
        return path

    return _write
