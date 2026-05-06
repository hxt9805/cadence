"""B1 修复 — Step 6 archive cleanup helper.

Implements the 6a/6b/6c file IO of cadence-resume Step 6:
- 6a: remove handoff entry from .handoff/index.json
- 6b: move .handoff/<id>.md → .handoff/archived/<id>.md
- 6c: append entry to .handoff/archived/index.json

Idempotent: each step skips if already done.
"""
import json
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict


def _iso_now_with_tz() -> str:
    """ISO-8601 timestamp with +08:00 offset (cadence project tz convention)."""
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def cleanup_handoff(handoff_dir: Path, handoff_id: str) -> Dict[str, str]:
    """Execute Step 6a/6b/6c cleanup for given handoff_id.

    Returns: dict with keys '6a', '6b', '6c' each = 'success' | 'skip' | 'fail:<reason>'
    Raises: nothing — failures recorded in return dict (graceful degradation per § 6d).
    """
    handoff_dir = Path(handoff_dir)
    pending_index_path = handoff_dir / "index.json"
    handoff_file = handoff_dir / f"{handoff_id}.md"
    archived_dir = handoff_dir / "archived"
    archived_index_path = archived_dir / "index.json"
    archived_file = archived_dir / f"{handoff_id}.md"

    result = {"6a": "", "6b": "", "6c": ""}
    original_entry = None

    # 6a: 从 pending index.json 移除条目
    # NOTE: cadence-handoff/SKILL.md:98 规定 index.json "保持 json array 形态"
    try:
        if pending_index_path.exists():
            pending = json.loads(pending_index_path.read_text(encoding="utf-8"))
            matching = [i for i in pending if i.get("handoff_id") == handoff_id]
            if matching:
                original_entry = matching[0]
                pending = [i for i in pending if i.get("handoff_id") != handoff_id]
                pending_index_path.write_text(
                    json.dumps(pending, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                result["6a"] = "success"
            else:
                result["6a"] = "skip"  # 已不在 pending(可能已 resumed 过 / 外部清空)
        else:
            result["6a"] = "skip"
    except (json.JSONDecodeError, OSError) as e:
        result["6a"] = f"fail:{e}"

    # 6b: 移动文件到 archived/
    try:
        archived_dir.mkdir(exist_ok=True)
        if archived_file.exists():
            result["6b"] = "skip"  # 已在 archived
        elif handoff_file.exists():
            shutil.move(str(handoff_file), str(archived_file))
            result["6b"] = "success"
        else:
            result["6b"] = "skip"  # 文件已不存在
    except OSError as e:
        result["6b"] = f"fail:{e}"

    # 6c: 追加到 archived/index.json
    # I2: 若 6b 失败,跳过 6c 以避免 archived 状态不一致
    # (文件未移动但 index 记录为 archived 比 clean failure 更难恢复)
    if result["6b"].startswith("fail:"):
        result["6c"] = "skip"
    else:
        try:
            if archived_index_path.exists():
                archived = json.loads(archived_index_path.read_text(encoding="utf-8"))
            else:
                archived = []

            # 幂等：如果已有该 handoff_id 条目 → skip
            if any(i.get("handoff_id") == handoff_id for i in archived):
                result["6c"] = "skip"
            else:
                new_entry = {
                    "handoff_id": handoff_id,
                    "resumed_at": _iso_now_with_tz(),
                }
                if original_entry:
                    new_entry["original_index_entry"] = original_entry
                archived.append(new_entry)
                archived_index_path.write_text(
                    json.dumps(archived, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                result["6c"] = "success"
        except (json.JSONDecodeError, OSError) as e:
            result["6c"] = f"fail:{e}"

    return result


def main():
    """CLI: python handoff_cleanup_helper.py <handoff_dir> <handoff_id>"""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <handoff_dir> <handoff_id>", file=sys.stderr)
        sys.exit(2)
    handoff_dir = Path(sys.argv[1])
    handoff_id = sys.argv[2]
    result = cleanup_handoff(handoff_dir, handoff_id)
    for step, status in result.items():
        marker = "[OK]" if status == "success" else ("[SKIP]" if status == "skip" else "[WARN]")
        print(f"{marker} Step {step}: {status}")
    # exit 0 even if some steps failed (graceful degradation per § 6d)
    sys.exit(0)


if __name__ == "__main__":
    main()
