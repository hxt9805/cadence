"""Cross-file contract tests for domain-neutral recording fidelity guidance."""

from pathlib import Path


ROOT = Path(__file__).parent.parent
BOOTSTRAP = (ROOT / "skills/cadence-bootstrap/SKILL.md").read_text(encoding="utf-8")
PROJECT_DISCUSS = (ROOT / "skills/project-discuss/SKILL.md").read_text(
    encoding="utf-8"
)
RECORDING_PROTOCOL = (
    ROOT / "skills/project-discuss/references/recording-protocol.md"
).read_text(encoding="utf-8")
FIDELITY_PATH = (
    ROOT / "skills/project-discuss/references/recording-fidelity.md"
)
HANDOFF = (ROOT / "skills/cadence-handoff/SKILL.md").read_text(
    encoding="utf-8"
)
RESUME = (ROOT / "skills/cadence-resume/SKILL.md").read_text(encoding="utf-8")


def _fidelity_reference() -> str:
    return FIDELITY_PATH.read_text(encoding="utf-8")


def test_bootstrap_defines_three_separate_recording_decisions():
    assert "承接决定是否记录" in BOOTSTRAP
    assert "持久语义增量决定是否新建 entry" in BOOTSTRAP
    assert "影响等级决定记录多详细" in BOOTSTRAP


def test_project_discuss_captures_the_proposal_not_the_acceptance_shorthand():
    assert "不是承接短句本身" in PROJECT_DISCUSS
    for shorthand in ["可以", "认可", "方案二", "按你推荐的来"]:
        assert shorthand in PROJECT_DISCUSS


def test_fidelity_reference_is_linked_directly_from_active_skills():
    relative = "references/recording-fidelity.md"
    assert relative in PROJECT_DISCUSS
    assert "../project-discuss/references/recording-fidelity.md" in BOOTSTRAP


def test_reference_classifies_impact_without_locking_to_project_type():
    reference = _fidelity_reference()
    for dimension in [
        "可逆性",
        "影响范围",
        "损失风险",
        "持续时间",
        "外部承诺",
        "不确定性",
        "协作复杂度",
    ]:
        assert dimension in reference
    assert "领域名称只能作为示例" in reference
    assert "不能成为固定 schema" in reference


def test_reference_covers_non_software_projects_with_the_same_profiles():
    reference = _fidelity_reference()
    for domain in ["研究", "写作", "学习", "运营"]:
        assert domain in reference
    for profile in ["Light", "Standard", "High"]:
        assert profile in reference


def test_reference_protects_sensitive_and_replaceable_content():
    reference = _fidelity_reference()
    for protected in ["密码", "验证码", "令牌", "密钥", "工具日志"]:
        assert protected in reference
    assert "产物路径" in reference


def test_protocol_uses_profile_aware_fidelity_instead_of_one_minimum():
    assert "profile-aware" in RECORDING_PROTOCOL
    assert "Light / Standard / High" in RECORDING_PROTOCOL


def test_reference_contains_cold_start_recovery_questions():
    reference = _fidelity_reference()
    for question in [
        "已决定什么",
        "为什么",
        "否决过什么",
        "哪些约束不能破坏",
        "哪些问题仍未决定",
        "下一步是什么",
    ]:
        assert question in reference


def test_handoff_stays_compact_while_resume_reads_canonical_context():
    assert "15-30 行" in HANDOFF
    assert "continuation_refs" in HANDOFF
    assert "读取所有校验通过的 continuation discussion" in RESUME
    for question in [
        "已决定什么?",
        "为什么?",
        "否决过什么?",
        "哪些约束不能破坏?",
        "哪些问题仍未决定?",
        "下一步是什么?",
    ]:
        assert question in RESUME
