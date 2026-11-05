"""Tests for scripts/build_provider_tables.py using fixture YAML only."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import pytest
import yaml

from scripts import build_provider_tables as bpt

# ---------------------------------------------------------------------------
# Inline fixtures (no conftest — owned elsewhere)
# ---------------------------------------------------------------------------

FIXTURE_YAML = dedent(
    """
    schema_version: 2
    china_relays:
      - name: Zebra Relay
        url: https://zebra.example
        type: reverse
        status: unverified
        payment: [alipay, card]
        notes:
          en: "English note"
          zh-TW: "繁體備註"
          zh-CN: "简体备注"
      - name: Alpha Relay
        url: https://alpha.example
        type: mixed
        status: active
        verified_by: maintainer
        payment: [wechat]
        last_verified: "2026-01-15"
        notes: "English-only string note"
    global_gateways:
      - name: Gateway One
        url: https://gw.example
        type: aggregator
        status: active
        verified_by: maintainer
        payment: [crypto]
        notes:
          en: "Global EN"
          zh-TW: "Global TW"
          zh-CN: "Global CN"
    comparison_tools:
      - name: CompareX
        url: https://compare.example
        type: observability
        status: active
        notes: "Tool note"
    """
)


@pytest.fixture
def fixture_doc() -> dict:
    return yaml.safe_load(FIXTURE_YAML)


def _marker_block(section: str, body: str) -> str:
    return (
        f"<!-- providers:{section}:start -->\n"
        f"{body}\n"
        f"<!-- providers:{section}:end -->"
    )


def test_sections_render_in_yaml_order(fixture_doc: dict) -> None:
    """Rows follow providers.yaml list order (Alpha after Zebra in fixture)."""
    body = bpt._expected_body(fixture_doc, "china_relays", "en")
    assert body is not None
    zebra_pos = body.index("Zebra Relay")
    alpha_pos = body.index("Alpha Relay")
    assert zebra_pos < alpha_pos


def test_trilingual_headers_notes_and_payments(fixture_doc: dict) -> None:
    """Section headers, payment labels, and notes dict fall back per language."""
    en = bpt._expected_body(fixture_doc, "china_relays", "en")
    tw = bpt._expected_body(fixture_doc, "china_relays", "zh-TW")
    cn = bpt._expected_body(fixture_doc, "china_relays", "zh-CN")

    assert en is not None and tw is not None and cn is not None
    assert "| Station |" in en
    assert "| 中轉站 |" in tw
    assert "| 中转站 |" in cn

    assert "English note" in en
    assert "繁體備註" in tw
    assert "简体备注" in cn
    assert "English-only string note" in cn

    assert "Alipay/Card" in en
    assert "支付寶/卡" in tw
    assert "支付宝/卡" in cn
    assert "WeChat" in en
    assert "微信" in tw


def test_section_grouping_uses_distinct_renderers(fixture_doc: dict) -> None:
    """Each catalog section gets its own column layout."""
    china = bpt._expected_body(fixture_doc, "china_relays", "en")
    global_gw = bpt._expected_body(fixture_doc, "global_gateways", "en")
    tools = bpt._expected_body(fixture_doc, "comparison_tools", "en")

    assert china is not None and global_gw is not None and tools is not None
    assert china.count("|") > global_gw.count("|")  # china has Trust column
    assert "| Trust |" in china
    assert "| Trust |" not in global_gw
    assert "| Service |" in global_gw
    assert "| Tool |" in tools
    assert "CompareX" in tools
    assert "Gateway One" in global_gw


def test_check_tables_detects_readme_drift(fixture_doc: dict, tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    blocks = []
    for section in ("china_relays", "global_gateways", "comparison_tools"):
        body = bpt._expected_body(fixture_doc, section, "en")
        assert body is not None
        blocks.append(_marker_block(section, body))
    synced_readme = "# Test\n\n" + "\n\n".join(blocks) + "\n"
    readme.write_text(synced_readme, encoding="utf-8")

    with (
        patch.object(bpt, "REPO_ROOT", tmp_path),
        patch.object(bpt, "READMES", [readme]),
        patch.object(bpt, "_load_doc", lambda: fixture_doc),
    ):
        assert bpt.check_tables() == 0

        expected_china = bpt._expected_body(fixture_doc, "china_relays", "en")
        assert expected_china is not None
        drifted_china = expected_china.replace("Zebra Relay", "Hand-edited Zebra")
        drifted_readme = synced_readme.replace(expected_china, drifted_china)
        readme.write_text(drifted_readme, encoding="utf-8")
        assert bpt.check_tables() == 1


def test_check_pr_rejects_hand_edited_table_without_yaml(
    fixture_doc: dict, tmp_path: Path
) -> None:
    readme = tmp_path / "README.md"
    rel = "README.md"
    expected = bpt._expected_body(fixture_doc, "china_relays", "en")
    assert expected is not None
    base_body = expected
    hand_body = expected.replace("Alpha Relay", "Manual Alpha Edit")

    readme.write_text(
        f"# Test\n\n{_marker_block('china_relays', hand_body)}\n",
        encoding="utf-8",
    )
    base_readme = f"# Test\n\n{_marker_block('china_relays', base_body)}\n"

    def fake_show(base: str, path: str) -> str | None:
        if path == rel:
            return base_readme
        return None

    with (
        patch.object(bpt, "REPO_ROOT", tmp_path),
        patch.object(bpt, "READMES", [readme]),
        patch.object(bpt, "_load_doc", lambda: fixture_doc),
        patch.object(bpt, "_git_changed_files", lambda base: {rel}),
        patch.object(bpt, "_git_show", fake_show),
    ):
        assert bpt.check_pr(base="deadbeef") == 1


def test_check_pr_allows_yaml_only_when_readme_unchanged(
    fixture_doc: dict, tmp_path: Path
) -> None:
    """Yaml-only PRs pass even if on-disk README tables lag the YAML."""
    readme = tmp_path / "README.md"
    stale_body = "| Station | Type | Payment | Trust | Notes |\n|---|---|---|---|---|\n| stale |"
    readme.write_text(
        f"# Test\n\n{_marker_block('china_relays', stale_body)}\n",
        encoding="utf-8",
    )

    with (
        patch.object(bpt, "REPO_ROOT", tmp_path),
        patch.object(bpt, "READMES", [readme]),
        patch.object(bpt, "_load_doc", lambda: fixture_doc),
        patch.object(
            bpt,
            "_git_changed_files",
            lambda base: {"data/providers.yaml"},
        ),
    ):
        assert bpt.check_pr(base="deadbeef") == 0
