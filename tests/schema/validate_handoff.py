"""
Handoff v0.3 snapshot validator。

v0.3 schema(design doc § 12.2):
    handoff_id / created_at / topic
    content_hashes: { _INDEX.md: <sha1>, _ACTIVE.md: <sha1> }      # I-1 必需
    cursor: { last_discussed, pending_questions?, next_step? }
    soft_context: { tone?, notes? }
    consolidation: { triggered, produced? }

v0.2.2 legacy 识别:frontmatter 无 content_hashes + 有 item_counts → legacy。
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
    """校验 v0.3 schema。遇 legacy 或缺字段抛 ValueError。"""
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


if __name__ == "__main__":
    run_cli(sys.argv[1], parse_handoff, validate_handoff_v03, "handoff v0.3 schema")
