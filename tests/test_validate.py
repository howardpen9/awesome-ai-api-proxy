"""Unit tests for scripts.validate.validate_providers (isolated YAML via tmp_path)."""

from __future__ import annotations

from pathlib import Path

from scripts.validate import validate_providers

from conftest import minimal_provider_entry, providers_doc


def _run(path: Path) -> list[str]:
    problems: list[str] = []
    validate_providers(problems, providers_path=path)
    return problems


def test_valid_entry_passes(write_providers_yaml):
    path = write_providers_yaml(
        providers_doc(
            ("china_relays", [minimal_provider_entry()]),
        )
    )
    assert _run(path) == []


def test_official_type_is_allowed(write_providers_yaml):
    path = write_providers_yaml(
        providers_doc(
            (
                "global_gateways",
                [
                    minimal_provider_entry(
                        name="OpenAI",
                        url="https://platform.openai.com",
                        type="official",
                    ),
                ],
            ),
        )
    )
    assert _run(path) == []


def test_missing_required_field_fails(write_providers_yaml):
    entry = minimal_provider_entry()
    del entry["type"]
    path = write_providers_yaml(providers_doc(("china_relays", [entry])))
    problems = _run(path)
    assert any("missing fields" in p and "type" in p for p in problems)


def test_invalid_type_fails(write_providers_yaml):
    path = write_providers_yaml(
        providers_doc(
            ("china_relays", [minimal_provider_entry(type="not-a-real-type")]),
        )
    )
    problems = _run(path)
    assert len(problems) == 1
    assert "invalid type" in problems[0]


def test_bad_url_fails(write_providers_yaml):
    path = write_providers_yaml(
        providers_doc(
            ("china_relays", [minimal_provider_entry(url="http://insecure.example.com")]),
        )
    )
    problems = _run(path)
    assert any("must be https://" in p for p in problems)


def test_duplicate_name_fails(write_providers_yaml):
    entry = minimal_provider_entry(name="Same Name", url="https://a.example.com")
    other = minimal_provider_entry(name="Same Name", url="https://b.example.com")
    path = write_providers_yaml(providers_doc(("china_relays", [entry, other])))
    problems = _run(path)
    assert any("duplicate name" in p for p in problems)
