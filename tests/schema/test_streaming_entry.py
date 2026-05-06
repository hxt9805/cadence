"""
streaming/<date>-<slug>.md entry schema 校验测试。

对应:skills/project-discuss/references/recording-protocol.md § α
"""
from pathlib import Path
import pytest
from validate_streaming import parse_entries

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
