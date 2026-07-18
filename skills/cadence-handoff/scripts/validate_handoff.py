"""
Handoff v0.3/v0.4 snapshot validator。

v0.3 schema(design doc § 12.2):
    handoff_id / created_at / topic
    content_hashes: { _INDEX.md: <sha1>, _ACTIVE.md: <sha1> }      # I-1 必需
    cursor: { last_discussed, pending_questions?, next_step? }
    soft_context: { tone?, notes? }
    consolidation: { triggered, produced? }

v0.2.2 legacy 识别:frontmatter 无 content_hashes + 有 item_counts → legacy。

v0.4 optional extension:
    continuation_refs: [{path: discussions/..., sha1: <40 hex>}]  # 1-3
    fidelity: {status: complete | partial, uncovered: [...]}
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass

from _common import ensure_yaml, run_cli

yaml = ensure_yaml()

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
HASH_TARGETS = ("_INDEX.md", "_ACTIVE.md")


@dataclass
class HandoffDoc:
    front_matter: dict
    body: str


def parse_handoff(content: str) -> HandoffDoc:
    if not content.startswith("---"):
        raise ValueError("missing front matter")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("malformed front matter")
    fm = yaml.safe_load(parts[1]) or {}
    return HandoffDoc(front_matter=fm, body=parts[2])


def is_legacy_v22(doc: HandoffDoc) -> bool:
    """v0.2.2 老格式:无 content_hashes + 有 item_counts。

    判据仅在 v0.2.2 → v0.3 过渡期有效;若未来 schema 再变(如 v0.4 重加 item_counts)
    可能误判,届时改用显式 schema_version 字段。
    """
    fm = doc.front_matter
    return "content_hashes" not in fm and "item_counts" in fm


def validate_handoff_v03(doc: HandoffDoc) -> None:
    """校验 v0.3 schema 及向后兼容的 v0.4 扩展。"""
    if is_legacy_v22(doc):
        raise ValueError(
            "legacy v0.2.2 detected (has item_counts, no content_hashes); "
            "use mtime fallback path in cadence-resume"
        )

    fm = doc.front_matter

    for key in ("handoff_id", "created_at", "topic"):
        if not fm.get(key):
            raise ValueError(f"{key} required")

    hashes = fm.get("content_hashes")
    if not isinstance(hashes, dict):
        raise ValueError("content_hashes required (dict with _INDEX.md + _ACTIVE.md)")
    for target in HASH_TARGETS:
        h = hashes.get(target)
        if not h:
            raise ValueError(f"content_hashes.{target} required")
        if not SHA1_RE.match(str(h)):
            raise ValueError(
                f"content_hashes.{target} must be 40-char lowercase hex sha1, got {h!r}"
            )

    cursor = fm.get("cursor")
    if not isinstance(cursor, dict):
        raise ValueError("cursor required (dict)")
    if not cursor.get("last_discussed"):
        raise ValueError("cursor.last_discussed required")

    cons = fm.get("consolidation", {})
    if "triggered" not in cons:
        raise ValueError("consolidation.triggered required (bool)")

    refs_present = "continuation_refs" in fm
    fidelity_present = "fidelity" in fm
    if refs_present != fidelity_present:
        raise ValueError(
            "continuation_refs and fidelity must be provided together"
        )
    if refs_present:
        _validate_continuation_refs(fm["continuation_refs"])
        _validate_fidelity(fm["fidelity"])


def _validate_continuation_refs(refs) -> None:
    if not isinstance(refs, list) or not 1 <= len(refs) <= 3:
        raise ValueError("continuation_refs must contain 1-3 items")
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            raise ValueError(f"continuation_refs[{index}] must be a dict")
        path = ref.get("path")
        if not isinstance(path, str) or not path.startswith("discussions/"):
            raise ValueError(
                f"continuation_refs[{index}].path must start with discussions/"
            )
        sha1 = ref.get("sha1")
        if not isinstance(sha1, str) or not SHA1_RE.match(sha1):
            raise ValueError(
                f"continuation_refs[{index}].sha1 must be 40-char lowercase hex"
            )


def _validate_fidelity(fidelity) -> None:
    if not isinstance(fidelity, dict):
        raise ValueError("fidelity must be a dict")
    status = fidelity.get("status")
    if status not in {"complete", "partial"}:
        raise ValueError("fidelity.status must be complete or partial")
    uncovered = fidelity.get("uncovered")
    if not isinstance(uncovered, list):
        raise ValueError(f"{status} fidelity requires uncovered list")
    if status == "complete" and uncovered:
        raise ValueError("complete fidelity requires uncovered to be empty")
    if status == "partial" and not uncovered:
        raise ValueError("partial fidelity requires non-empty uncovered")


if __name__ == "__main__":
    run_cli(sys.argv[1], parse_handoff, validate_handoff_v03, "handoff v0.3 schema")
