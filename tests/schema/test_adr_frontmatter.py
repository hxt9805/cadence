"""
ADR discussion doc 最小结构校验测试(Phase B)。

Phase B 只校验:
- front-matter:status in {accepted, superseded}, source_streaming_file non-empty
- body:4 个 h2 节存在(## Context / ## Decision / ## Rationale / ## Alternatives Considered)

完整字段校验(rejected_because, from_source, references)留 Phase C。
"""
from pathlib import Path
import pytest
from validate_adr import parse_adr, validate_adr_minimal, validate_adr_full

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_valid_adr_passes():
    doc = parse_adr(_load("adr_valid.md"))
    validate_adr_minimal(doc)


def test_missing_section_raises():
    doc = parse_adr(_load("adr_missing_section.md"))
    with pytest.raises(ValueError, match="Rationale"):
        validate_adr_minimal(doc)


def test_bad_status_raises():
    doc = parse_adr(_load("adr_bad_status.md"))
    with pytest.raises(ValueError, match="status"):
        validate_adr_minimal(doc)


def test_front_matter_source_required():
    doc = parse_adr(_load("adr_valid.md"))
    del doc.front_matter["source_streaming_file"]
    with pytest.raises(ValueError, match="source_streaming_file"):
        validate_adr_minimal(doc)


def test_full_valid_adr_passes():
    doc = parse_adr(_load("adr_full_valid.md"))
    validate_adr_full(doc, base_dir=FIXTURES)


def test_alternative_missing_rejected_raises():
    doc = parse_adr(_load("adr_alternative_missing_rejected.md"))
    with pytest.raises(ValueError, match="rejected_because"):
        validate_adr_full(doc, base_dir=FIXTURES)


def test_alternative_missing_source_raises():
    doc = parse_adr(_load("adr_alternative_missing_source.md"))
    with pytest.raises(ValueError, match="source"):
        validate_adr_full(doc, base_dir=FIXTURES)


def test_references_must_exist():
    doc = parse_adr(_load("adr_references_nonexistent.md"))
    with pytest.raises(ValueError, match="references.*not found|not exist"):
        validate_adr_full(doc, base_dir=FIXTURES)


def test_decision_id_format():
    doc = parse_adr(_load("adr_full_valid.md"))
    doc.front_matter["decision_id"] = "invalid-id"
    with pytest.raises(ValueError, match="decision_id"):
        validate_adr_full(doc, base_dir=FIXTURES)


def test_alternatives_accept_mixed_indent():
    """Alternatives 字段缩进 2-space / 4-space 都应被解析。"""
    doc = parse_adr(_load("adr_mixed_indent.md"))
    validate_adr_full(doc, base_dir=FIXTURES)


# ---------------------------------------------------------------------------
# B6: status 状态机扩展(implemented / stale 新增 + archived 拒绝)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["implemented", "stale"])
def test_adr_new_status_values_accepted(status):
    """v0.4 ADR doc 接受扩展 status 值(implemented / stale)"""
    doc = parse_adr(_load("adr_valid.md"))
    doc.front_matter["status"] = status
    validate_adr_minimal(doc)  # should not raise


def test_adr_status_archived_rejected():
    """v0.4 ADR doc 不接受 archived 作为 status(它是物理动作)"""
    doc = parse_adr(_load("adr_valid.md"))
    doc.front_matter["status"] = "archived"
    with pytest.raises(ValueError, match="status"):
        validate_adr_minimal(doc)
