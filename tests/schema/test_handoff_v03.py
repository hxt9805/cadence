"""
Handoff v0.3 snapshot schema 校验测试。

对应:design doc § 12.2、skills/cadence-handoff/SKILL.md v0.3 schema
"""
from pathlib import Path
import pytest
from validate_handoff import parse_handoff, validate_handoff_v03, is_legacy_v22

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    return parse_handoff((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_v03_passes():
    doc = _load("handoff_v03_valid.md")
    validate_handoff_v03(doc)


def test_missing_content_hashes_raises():
    doc = _load("handoff_v03_missing_hashes.md")
    with pytest.raises(ValueError, match="content_hashes"):
        validate_handoff_v03(doc)


def test_bad_sha1_format_raises():
    doc = _load("handoff_v03_bad_sha1.md")
    with pytest.raises(ValueError, match="sha1"):
        validate_handoff_v03(doc)


def test_legacy_v22_detected():
    """v0.2.2 老格式应被 is_legacy_v22 识别(resume 走 mtime 兜底)。"""
    doc = _load("handoff_v22_legacy.md")
    assert is_legacy_v22(doc) is True
    # v0.2.2 legacy 应被 v0.3 validator 显式拒绝
    with pytest.raises(ValueError, match="legacy.*v0.2.2"):
        validate_handoff_v03(doc)


def test_cursor_last_discussed_required():
    doc = _load("handoff_v03_valid.md")
    del doc.front_matter["cursor"]["last_discussed"]
    with pytest.raises(ValueError, match="last_discussed"):
        validate_handoff_v03(doc)
