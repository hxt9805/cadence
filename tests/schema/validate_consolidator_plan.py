"""
recall-consolidator plan yaml validator.

Plan schema(design doc § 9.3 MVP):
    plan_version: "v0.3" | "v0.4"         # 必需;v0.3/v0.4 均接受
    trigger_reason: llm_initiated | handoff_sweep
    target_streaming_file: <path>
    target_topic_slug: <slug>
    new_doc_path: discussions/<date>-<slug>.md
    new_doc_content:
      front_matter:
        status: accepted | superseded      # 必填(状态机硬约束)
        decision_id?                       # 建议(v0.4 降建议)
        source_streaming_file?             # 建议(v0.4 降建议)
        references?                        # 建议(v0.4 降建议)
      body?:                               # 建议(v0.4 降建议)
        context?                           # 建议
        decision?                          # 建议
        rationale?                         # 建议
        alternatives_considered?           # 建议
    streaming_file_updates:
      file: <path>
      front_matter_update: { status: archived, superseded_by: <path> }
      tombstone_entry: { id, timestamp, body }
    active_md_edits: []         # optional
    references: []              # optional
    warnings: []                # optional

v0.4 schema 变更(design doc § 5.2.5):
- decision_id / source_streaming_file / front_matter.references / body 四节
  从必填降为建议(缺失不报错,存在则校验合法性)
- status 仍必填(状态机硬约束)
- plan_version 接受 "v0.3"(向后兼容) 和 "v0.4"

MVP scope:本 validator 只校验 Phase B 的 MVP 路径——`new_doc_path` 指向新建
`discussions/<date>-<slug>.md`。spec § 9.3 提到的 `merge_into_existing`(并入已有
discussion)分支留 Phase C 或 v0.4+,本 Phase 不实现不校验。

DRY:复制 validate_streaming.py 的 try/except ImportError shim 和
if __name__ == "__main__" 段(几乎一致)。暂不提取共享 helper;待第 4 个 validator
(Phase D handoff)时再抽 _common.py。
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError as e:
    raise SystemExit("pip install pyyaml required") from e


VALID_TRIGGERS = {"llm_initiated", "handoff_sweep"}
VALID_PLAN_VERSIONS = {"v0.3", "v0.4"}
LIFECYCLE_ACTIONS = {"archive_decision", "delete_todo", "promote_pending_to_decision"}

# ---------------------------------------------------------------------------
# v0.4 状态机定义 — archived/done/resolved/tombstone 都是终态/物理动作,不在 status 集合
# ---------------------------------------------------------------------------
DECISION_STATUSES = {"accepted", "implemented", "stale", "superseded"}
DECISION_TRANSITIONS = {
    "accepted": {"implemented", "stale", "superseded"},
    "implemented": set(),   # 终态(archive 是物理动作)
    "stale": set(),         # 终态
    "superseded": set(),    # 终态
}
# TODO 状态机(在 _ACTIVE.md TODO 段使用,不在 ADR doc)
TODO_STATUSES = {"pending", "done"}
TODO_TRANSITIONS = {"pending": {"done"}, "done": set()}
# 待决状态机
PENDING_STATUSES = {"open", "resolved"}
PENDING_TRANSITIONS = {"open": {"resolved"}, "resolved": set()}

# 向后兼容别名(validate_plan 内部使用)
VALID_STATUS = DECISION_STATUSES


def _check_status(status: str, allowed: set, field: str = "status") -> None:
    """v0.3 风格: 不合法 → 抛 ValueError"""
    if status not in allowed:
        raise ValueError(f"{field}={status!r} not in allowed set {sorted(allowed)}")


def _check_transition(
    from_s: str | None, to_s: str, transitions: dict, action: str = "transition"
) -> None:
    """v0.3 风格: 不合法转换 → 抛 ValueError

    if from_s is None (first assignment), transition check is skipped —
    caller must validate to_s independently via _check_status before this call.
    """
    if from_s is None:
        return
    if from_s not in transitions:
        raise ValueError(f"{action}: from_status={from_s!r} unknown")
    if to_s not in transitions[from_s]:
        raise ValueError(f"{action}: illegal transition {from_s!r}→{to_s!r}")


def load_plan(content: str) -> dict:
    """Parse yaml plan content. Raises yaml.YAMLError on syntax errors."""
    return yaml.safe_load(content)


def validate_plan(plan: dict) -> None:
    """Validate consolidator plan schema. Raises ValueError on violations."""
    if not isinstance(plan, dict):
        raise ValueError("plan must be a dict")

    pv = plan.get("plan_version")
    if pv not in VALID_PLAN_VERSIONS:
        raise ValueError(
            f'plan_version must be one of {sorted(VALID_PLAN_VERSIONS)}, got {pv!r}'
        )

    tr = plan.get("trigger_reason")
    if tr not in VALID_TRIGGERS:
        raise ValueError(
            f"trigger_reason must be in {VALID_TRIGGERS}, got {tr!r}"
        )

    for key in ("target_streaming_file", "target_topic_slug", "new_doc_path"):
        if not plan.get(key):
            raise ValueError(f"{key} required and non-empty")

    if not plan["target_streaming_file"].startswith("streaming/"):
        raise ValueError(
            f'target_streaming_file must start with "streaming/", '
            f'got {plan["target_streaming_file"]!r}'
        )
    if not plan["new_doc_path"].startswith("discussions/"):
        raise ValueError(
            f'new_doc_path must start with "discussions/", got {plan["new_doc_path"]!r}'
        )

    ndc = plan.get("new_doc_content")
    if not isinstance(ndc, dict):
        raise ValueError("new_doc_content required (dict)")

    if "front_matter" not in ndc:
        raise ValueError("new_doc_content.front_matter required")
    fm = ndc["front_matter"]
    if not isinstance(fm, dict):
        raise ValueError("new_doc_content.front_matter must be dict")
    if fm.get("status") not in DECISION_STATUSES:
        raise ValueError(
            f"front_matter.status must be in {sorted(DECISION_STATUSES)}, got {fm.get('status')!r}"
        )
    # source_streaming_file: v0.4 降建议(缺失不报错)
    # decision_id / references: 同为建议字段(缺失不报错,无需额外校验)

    # body 整节及其四节(context/decision/rationale/alternatives_considered)v0.4
    # 全部建议级,缺失不报错;存在时校验结构合法
    body = ndc.get("body")
    if body is not None:
        if not isinstance(body, dict):
            raise ValueError("new_doc_content.body must be dict")
        # alternatives_considered 存在时必须是 list
        alts = body.get("alternatives_considered")
        if alts is not None and not isinstance(alts, list):
            raise ValueError("body.alternatives_considered must be list")

    sfu = plan.get("streaming_file_updates")
    if not isinstance(sfu, dict):
        raise ValueError("streaming_file_updates required (dict)")
    if "front_matter_update" not in sfu:
        raise ValueError("streaming_file_updates.front_matter_update required")
    fmu = sfu["front_matter_update"]
    if not isinstance(fmu, dict):
        raise ValueError("streaming_file_updates.front_matter_update must be dict")
    if fmu.get("status") != "archived":
        raise ValueError(
            f'streaming_file_updates.front_matter_update.status must be "archived", got {fmu.get("status")!r}'
        )
    if "tombstone_entry" not in sfu:
        raise ValueError("streaming_file_updates.tombstone_entry required")
    tombstone = sfu["tombstone_entry"]
    if not isinstance(tombstone, dict):
        raise ValueError("streaming_file_updates.tombstone_entry must be dict")
    for key in ("id", "timestamp", "body"):
        if not tombstone.get(key):
            raise ValueError(f"tombstone_entry.{key} required")

    # MVP: plan 顶层 references 简化为字符串路径列表(简化 design § 9.3 对象形式,
    # 详见 Phase C / Task C4 Scope 说明)。v0.4+ 可扩展:若遇到 dict 则走对象校验分支。
    # 路径硬约束:必须含目录前缀("/" in ref),避免裸文件名歧义。v0.4+ 可支持 URL(scheme 检测)。
    refs = plan.get("references") or []
    if not isinstance(refs, list):
        raise ValueError("references must be a list (or omitted)")
    for i, ref in enumerate(refs):
        if not isinstance(ref, str):
            raise ValueError(f"references[{i}] must be string, got {type(ref).__name__}")
        if "/" not in ref:
            raise ValueError(
                f"references[{i}] must be a path with directory prefix "
                f"(e.g. discussions/... or streaming/...), got {ref!r}"
            )

    # v0.4 active_md_edits: 按 action 分发 status + transition 校验
    edits = plan.get("active_md_edits") or []
    if not isinstance(edits, list):
        raise ValueError("active_md_edits must be a list (or omitted)")
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict):
            continue  # 类型错误在 warnings 层处理,hard validator 不管
        action = edit.get("action")
        if action not in LIFECYCLE_ACTIONS:
            continue  # 未知 action 暂不校验(向前兼容)
        new_status = edit.get("new_status")
        from_status = edit.get("from_status")
        if new_status is None:
            continue  # new_status 是可选字段(非必填)
        if action == "archive_decision":
            statuses = DECISION_STATUSES
            transitions = DECISION_TRANSITIONS
        elif action == "delete_todo":
            statuses = TODO_STATUSES
            transitions = TODO_TRANSITIONS
        elif action == "promote_pending_to_decision":
            statuses = PENDING_STATUSES
            transitions = PENDING_TRANSITIONS
        else:
            continue
        _check_status(new_status, statuses, field=f"active_md_edits[{i}].new_status")
        if from_status is not None:
            _check_transition(
                from_status, new_status, transitions,
                action=f"active_md_edits[{i}] transition"
            )


def validate_plan_with_warnings(plan):
    """v0.4 双 API: 调用 validate_plan(失败仍抛 ValueError) + 收集软警告。

    Returns:
        list[str]: warnings 列表(空列表 = 无 warning)

    Raises:
        ValueError: hard error 仍抛(与 validate_plan 一致)
    """
    # 先跑 hard validation(抛 ValueError)
    validate_plan(plan)

    # 再收集 warnings
    warnings = []

    # v0.4 lifecycle action 应带 undo_hint
    edits = plan.get("active_md_edits") or []
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict):
            # validate_plan does not currently validate active_md_edits element types;
            # skip non-dict entries defensively
            continue
        action = edit.get("action")
        if action in LIFECYCLE_ACTIONS and "undo_hint" not in edit:
            warnings.append(
                f"active_md_edits[{i}].action={action} missing undo_hint "
                "(recommended for v0.4 lifecycle reversibility)"
            )

    return warnings


if __name__ == "__main__":
    path = Path(sys.argv[1])
    plan = load_plan(path.read_text(encoding="utf-8"))
    try:
        validate_plan(plan)
    except ValueError as e:
        print(f"❌ {path}: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ {path}: consolidator plan schema valid")
