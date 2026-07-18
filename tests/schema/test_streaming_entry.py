"""
streaming/<date>-<slug>.md entry schema 校验测试。

对应:skills/project-discuss/references/recording-protocol.md § α
"""
from pathlib import Path
import pytest
from validate_streaming import parse_entries, validate_entry_with_warnings

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_valid_entries_parse():
    entries = parse_entries(_load("streaming_valid.md"))
    assert len(entries) == 2
    first = entries[0]
    assert first.entry_id == "^entry-20260421-01"
    assert first.timestamp.tzinfo is not None
    assert first.chosen == "Redis"
    assert first.options == ["Redis", "Memcached"]
    assert first.rejected == {"Memcached": "不原生支持 rate limiting"}


def test_tombstone_recognized():
    entries = parse_entries(_load("streaming_tombstone.md"))
    tombstone = entries[-1]
    assert tombstone.is_tombstone
    assert tombstone.ref == "^entry-20260421-01"
    assert tombstone.reason


def test_missing_id_raises():
    with pytest.raises(ValueError, match="missing entry id"):
        parse_entries(_load("streaming_invalid_no_id.md"))


def test_missing_tz_raises():
    with pytest.raises(ValueError, match="timezone"):
        parse_entries(_load("streaming_invalid_no_tz.md"))


def test_missing_chosen_raises():
    with pytest.raises(ValueError, match="chosen.*required"):
        parse_entries(_load("streaming_missing_chosen.md"))


def test_yaml_entry_parses_to_decision_record():
    entry = parse_entries(_load("streaming_yaml_valid.md"))[0]
    assert entry.entry_id == "^entry-20260718-01"
    assert entry.timestamp.tzinfo is not None
    assert entry.detail_profile == "high"
    assert entry.rationale == "后续参与者必须知道为什么采用这一边界。"
    assert entry.semantic_slots["rules_and_invariants"] == [
        "确认后的范围在下一轮评审前保持不变"
    ]
    assert entry.not_applicable == ["retention_and_exit"]
    assert entry.provenance["chosen"] == "explicit"


def test_high_profile_requires_rationale():
    with pytest.raises(ValueError, match="rationale.*required"):
        parse_entries(_load("streaming_high_missing_rationale.md"))


def test_non_software_high_decision_uses_same_model():
    entry = parse_entries(_load("streaming_domain_neutral.md"))[0]
    assert entry.detail_profile == "high"
    assert entry.semantic_slots["external_commitments"] == [
        "公开报告只引用取得书面授权的访谈"
    ]
    assert "database" not in entry.semantic_slots
    assert "frontend" not in entry.semantic_slots


def test_vague_numbered_choice_returns_fidelity_warning():
    entry = parse_entries(_load("streaming_valid.md"))[0]
    entry.chosen = "采用方案二"
    warnings = validate_entry_with_warnings(entry)
    assert any("具体语义" in warning for warning in warnings)
