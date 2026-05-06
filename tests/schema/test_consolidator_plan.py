"""
recall-consolidator Plan-only 输出 yaml schema 校验测试。

对应:skills/project-discuss/agents/recall-consolidator.md 输出 schema
     docs/design/2026-04-21-project-discuss-v0.3-design.md § 9.3
"""
from pathlib import Path
import pytest
from validate_consolidator_plan import validate_plan, load_plan, validate_plan_with_warnings

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str):
    return load_plan((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_plan_passes():
    plan = _load("consolidator_plan_valid.yaml")
    validate_plan(plan)  # 不抛异常即通过


def test_missing_plan_version_raises():
    plan = _load("consolidator_plan_missing_version.yaml")
    with pytest.raises(ValueError, match="plan_version"):
        validate_plan(plan)


def test_bad_trigger_reason_raises():
    plan = _load("consolidator_plan_bad_trigger.yaml")
    with pytest.raises(ValueError, match="trigger_reason"):
        validate_plan(plan)


def test_body_missing_rationale_no_longer_raises():
    """v0.4 降建议: body.rationale 缺失不再必须(向后兼容: v0.3 fixture 用新 validator 也通过)"""
    plan = _load("consolidator_plan_missing_rationale.yaml")
    validate_plan(plan)  # 不抛即通过


def test_streaming_status_must_be_archived():
    plan = _load("consolidator_plan_valid.yaml")
    plan["streaming_file_updates"]["front_matter_update"]["status"] = "active"
    with pytest.raises(ValueError, match="archived"):
        validate_plan(plan)


def test_references_must_be_string_list():
    plan = _load("consolidator_plan_bad_references.yaml")
    with pytest.raises(ValueError, match="references"):
        validate_plan(plan)


def test_references_string_path_format():
    plan = _load("consolidator_plan_valid.yaml")
    plan["references"] = ["no-leading-dir.md"]
    with pytest.raises(ValueError, match="references.*path"):
        validate_plan(plan)


def _base_plan_v04():
    """构造一个 v0.4 完整合法 plan(用于参数化测试中删字段)"""
    return {
        "plan_version": "v0.4",
        "trigger_reason": "llm_initiated",
        "target_streaming_file": "streaming/2026-04-27-test.md",
        "target_topic_slug": "test",
        "new_doc_path": "discussions/2026-04-27-test.md",
        "new_doc_content": {
            "front_matter": {
                "decision_id": "D99",
                "status": "accepted",
                "source_streaming_file": "streaming/2026-04-27-test.md",
                "references": [],
            },
            "body": {
                "context": "test ctx",
                "decision": "use X",
                "rationale": "because Y",
                "alternatives_considered": [],
            },
        },
        "streaming_file_updates": {
            "file": "streaming/2026-04-27-test.md",
            "front_matter_update": {
                "status": "archived",
                "superseded_by": "discussions/2026-04-27-test.md",
            },
            "tombstone_entry": {
                "id": "^entry-20260427-99",
                "timestamp": "2026-04-27T18:00:00+08:00",
                "body": "整合入 discussions/2026-04-27-test.md",
            },
        },
    }


@pytest.mark.parametrize("removed_field_path", [
    ["new_doc_content", "front_matter", "decision_id"],
    ["new_doc_content", "front_matter", "source_streaming_file"],
    ["new_doc_content", "front_matter", "references"],
])
def test_plan_optional_front_matter_fields_v04(removed_field_path):
    """v0.4 降建议: front_matter 中的 decision_id / source_streaming_file / references 缺失不抛"""
    plan = _base_plan_v04()
    target = plan
    for key in removed_field_path[:-1]:
        target = target[key]
    del target[removed_field_path[-1]]

    # 不抛 ValueError 即通过(v0.3 API 风格)
    validate_plan(plan)


@pytest.mark.parametrize("missing_body_section", [
    "context", "decision", "rationale", "alternatives_considered",
])
def test_plan_optional_body_sections_v04(missing_body_section):
    """v0.4 降建议: body 四节中任一缺失不抛(建议级，非必填)"""
    plan = _base_plan_v04()
    del plan["new_doc_content"]["body"][missing_body_section]

    validate_plan(plan)  # 不抛即通过


def test_plan_status_still_required_v04():
    """v0.4 status 仍必填(状态机硬约束)"""
    plan = _base_plan_v04()
    del plan["new_doc_content"]["front_matter"]["status"]

    with pytest.raises(ValueError, match="front_matter.status"):
        validate_plan(plan)


def test_plan_version_v04_accepted():
    """v0.4 plan_version: 'v0.4' 被接受, 未知版本 'v0.5' 被拒绝"""
    plan = _base_plan_v04()  # 默认 plan_version = "v0.4"
    validate_plan(plan)  # 不抛即通过

    # 负面 assertion: 未知版本应被拒绝
    plan["plan_version"] = "v0.5"
    with pytest.raises(ValueError, match="plan_version"):
        validate_plan(plan)


def test_plan_with_undo_hint_v04():
    """v0.4 lifecycle plan 含 undo_hint 字段时,无 warning"""
    plan = _base_plan_v04()
    plan["active_md_edits"] = [{
        "action": "archive_decision",
        "target": "D5",
        "new_status": "implemented",
        "archive_to": "discussions/2026-04-27-x.md",
        "reason": "git_log_window 命中 commit abc",
        "undo_hint": "用户说'撤回归档 D5' → 主 session: Edit _ACTIVE.md 还原 D5 + Edit archive 移除条目",
    }]
    warnings = validate_plan_with_warnings(plan)
    assert warnings == [], f"Expected no warnings, got: {warnings}"


@pytest.mark.parametrize("lifecycle_action", [
    "archive_decision",
    "delete_todo",
    "promote_pending_to_decision",
])
def test_plan_active_md_edit_without_undo_hint_warns_v04(lifecycle_action):
    """v0.4 lifecycle action 缺 undo_hint → warnings 列表有提示(不抛 ValueError)"""
    plan = _base_plan_v04()
    plan["active_md_edits"] = [{
        "action": lifecycle_action,
        "target": "D5" if lifecycle_action == "archive_decision" else "T1",
        # undo_hint 故意缺失
    }]
    warnings = validate_plan_with_warnings(plan)
    assert any("undo_hint" in w for w in warnings), \
        f"Expected undo_hint warning for action={lifecycle_action}, got: {warnings}"


def test_plan_active_md_edits_none_no_warnings_v04():
    """v0.4 active_md_edits=None 时 validate_plan_with_warnings 返回空列表(不报 undo_hint warning)"""
    plan = _base_plan_v04()
    plan["active_md_edits"] = None
    warnings = validate_plan_with_warnings(plan)
    assert warnings == [], f"Expected empty warnings, got: {warnings}"


# ---------------------------------------------------------------------------
# B6: status 状态机扩展(implemented / stale / done + 转换图)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("new_status", [
    "accepted", "implemented", "stale", "superseded",
])
def test_plan_status_extended_values_v04(new_status):
    """v0.4 status 接受扩展值(archived 不在 status 集合内 — 是物理动作)"""
    plan = _base_plan_v04()
    plan["new_doc_content"]["front_matter"]["status"] = new_status
    validate_plan(plan)  # 不抛即通过


def test_plan_status_invalid_value_v04():
    """v0.4 不接受未定义的 status 值(含 archived — 它是动作不是 status)"""
    plan = _base_plan_v04()
    plan["new_doc_content"]["front_matter"]["status"] = "weird_status"
    with pytest.raises(ValueError, match="status"):
        validate_plan(plan)


def test_plan_status_archived_rejected_v04():
    """v0.4 'archived' 不是合法 status 值(archived 是动作,状态机终态是 implemented/stale/superseded)"""
    plan = _base_plan_v04()
    plan["new_doc_content"]["front_matter"]["status"] = "archived"
    with pytest.raises(ValueError, match="status"):
        validate_plan(plan)


@pytest.mark.parametrize("from_status,to_status,should_pass", [
    ("accepted", "implemented", True),     # 合法
    ("accepted", "stale", True),           # 合法
    ("accepted", "superseded", True),      # 合法
    ("implemented", "stale", False),       # 非法(终态不能反向衰退)
    ("implemented", "accepted", False),    # 非法(终态不可逆)
    ("superseded", "accepted", False),     # 非法(终态不可逆)
    ("stale", "implemented", False),       # 非法(终态不可转 implemented)
])
def test_plan_status_transition_v04(from_status, to_status, should_pass):
    """v0.4 active_md_edits[].new_status 转换必须沿合法路径"""
    plan = _base_plan_v04()
    plan["active_md_edits"] = [{
        "action": "archive_decision",
        "target": "D5",
        "from_status": from_status,
        "new_status": to_status,
        "undo_hint": "test undo",
    }]
    if should_pass:
        validate_plan(plan)  # 不抛即通过
    else:
        with pytest.raises(ValueError, match="transition"):
            validate_plan(plan)


def test_plan_status_transition_first_assignment_v04():
    """v0.4 active_md_edits[].new_status 首次设置(无 from_status)允许任意合法 to_status"""
    plan = _base_plan_v04()
    plan["active_md_edits"] = [{
        "action": "archive_decision",
        "target": "D5",
        # 无 from_status (首次设置)
        "new_status": "implemented",
        "undo_hint": "test undo",
    }]
    validate_plan(plan)  # 不抛即通过
