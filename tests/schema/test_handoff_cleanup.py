"""Tests for handoff_cleanup_helper.py (B1 修复 — Step 6 archive cleanup)."""
import json
import sys
from pathlib import Path

import pytest

# 让 import 能找到 skills/cadence-resume/handoff_cleanup_helper
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "cadence-resume"))
from handoff_cleanup_helper import cleanup_handoff


@pytest.fixture
def handoff_dir(tmp_path):
    """构造一个完整的 .handoff/ 目录 fixture，含 pending index + 1 个 handoff 文件。"""
    handoff = tmp_path / ".handoff"
    handoff.mkdir()
    archived = handoff / "archived"
    # archived 目录默认不创建，让某些 test 验证 helper 自动创建

    # pending index.json — flat list per cadence-handoff/SKILL.md:98
    pending_index = handoff / "index.json"
    pending_index.write_text(json.dumps([
        {"handoff_id": "h_001", "created_at": "2026-04-25T10:00:00+08:00", "topic": "test handoff", "path": ".handoff/h_001.md"},
        {"handoff_id": "h_002", "created_at": "2026-04-26T10:00:00+08:00", "topic": "another", "path": ".handoff/h_002.md"},
    ], ensure_ascii=False), encoding="utf-8")

    # handoff 文件 h_001.md
    (handoff / "h_001.md").write_text("# h_001\nhandoff content", encoding="utf-8")
    (handoff / "h_002.md").write_text("# h_002\nhandoff content", encoding="utf-8")

    return handoff


def test_resume_step6_normal_cleanup(handoff_dir):
    """场景 1: 正常 resume 一个 pending handoff → 6a/b/c 全部成功"""
    result = cleanup_handoff(handoff_dir, "h_001")

    # 6a: 从 index.json 移除
    pending_index = json.loads((handoff_dir / "index.json").read_text(encoding="utf-8"))
    assert all(item["handoff_id"] != "h_001" for item in pending_index), \
        "h_001 should be removed from pending index.json"

    # 6b: 文件移到 archived/
    assert not (handoff_dir / "h_001.md").exists(), "h_001.md should be moved out of .handoff/"
    assert (handoff_dir / "archived" / "h_001.md").exists(), "h_001.md should exist in archived/"

    # 6c: 追加到 archived/index.json
    archived_index = json.loads((handoff_dir / "archived" / "index.json").read_text(encoding="utf-8"))
    assert any(item["handoff_id"] == "h_001" for item in archived_index), \
        "h_001 should be appended to archived/index.json"
    h001_archived = [i for i in archived_index if i["handoff_id"] == "h_001"][0]
    assert "resumed_at" in h001_archived, "archived item should have resumed_at timestamp"

    # M3: original_index_entry 应保留原 pending entry 字段
    assert "original_index_entry" in h001_archived, \
        "archived item should preserve original pending index entry"
    assert h001_archived["original_index_entry"]["created_at"] == "2026-04-25T10:00:00+08:00", \
        "original_index_entry should preserve created_at"
    assert h001_archived["original_index_entry"]["topic"] == "test handoff", \
        "original_index_entry should preserve topic"

    # 验证 status 全 success
    assert result["6a"] == "success", f"Expected 6a success, got {result}"
    assert result["6b"] == "success", f"Expected 6b success, got {result}"
    assert result["6c"] == "success", f"Expected 6c success, got {result}"


def test_resume_step6_idempotent(handoff_dir):
    """场景 2: resume 同一 handoff 两次 → 第二次 skip cleanup + 不报错"""
    # 第一次 resume
    cleanup_handoff(handoff_dir, "h_001")

    # 第二次 resume — 幂等
    result = cleanup_handoff(handoff_dir, "h_001")

    # 6a: index.json 中已无 h_001 → skip
    assert result["6a"] == "skip", f"Expected 6a skip on second resume, got {result}"
    # 6b: h_001.md 已在 archived/ → skip
    assert result["6b"] == "skip", f"Expected 6b skip on second resume, got {result}"
    # 6c: archived/index.json 中已有 h_001 → skip(不重复追加)
    assert result["6c"] == "skip", f"Expected 6c skip on second resume, got {result}"

    # archived/index.json 中 h_001 仍只有 1 条(不重复)
    archived_index = json.loads((handoff_dir / "archived" / "index.json").read_text(encoding="utf-8"))
    h001_count = sum(1 for i in archived_index if i["handoff_id"] == "h_001")
    assert h001_count == 1, f"Expected 1 h_001 entry, got {h001_count}"


def test_resume_step6_creates_archived_dir(handoff_dir):
    """场景 3: archived/ 目录不存在 → helper 自动创建后执行"""
    # fixture 默认未创建 archived/
    assert not (handoff_dir / "archived").exists()

    result = cleanup_handoff(handoff_dir, "h_001")

    assert (handoff_dir / "archived").exists(), "archived/ should be auto-created"
    assert (handoff_dir / "archived" / "h_001.md").exists()
    assert result["6b"] == "success"


def test_resume_step6_pending_index_externally_emptied(handoff_dir):
    """场景 4: index.json 已被外部清空 → skip 6a，仍走 6b/6c"""
    # 模拟外部清空 index.json
    (handoff_dir / "index.json").write_text(json.dumps([], ensure_ascii=False), encoding="utf-8")

    result = cleanup_handoff(handoff_dir, "h_001")

    # 6a skip(h_001 已不在 pending index)
    assert result["6a"] == "skip", f"Expected 6a skip on empty pending index, got {result}"
    # 6b 仍执行(文件还在 .handoff/)
    assert result["6b"] == "success"
    assert (handoff_dir / "archived" / "h_001.md").exists()
    # 6c 仍执行(追加到 archived/index.json)
    archived_index = json.loads((handoff_dir / "archived" / "index.json").read_text(encoding="utf-8"))
    assert any(item["handoff_id"] == "h_001" for item in archived_index)
