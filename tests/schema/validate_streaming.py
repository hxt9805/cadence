"""
streaming/<file>.md entry parser + validator.

Entry schema(见 recording-protocol.md § α):
    ^entry-<YYYYMMDD>-<seq> [<ISO-8601 TZ>] <summary>
      context: <...>
      options: [A, B]
      chosen: <...>
      rejected:
        - <name>: <reason>
      ref: ^entry-xx        ← tombstone 专用
      reason: <...>          ← tombstone 专用

可作为模块 import,也可 standalone:
    python tests/schema/validate_streaming.py cadence/streaming/<file>.md
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import _common  # noqa: F401  # imported for UTF-8 stdout/stderr reconfigure side-effect (Windows GBK consoles)

ENTRY_HEADER = re.compile(
    r"^\^entry-(?P<date>\d{8})-(?P<seq>\d{2,})\s+"
    r"\[(?P<ts>[^\]]+)\]\s+(?P<summary>.+)$"
)
KV_LINE = re.compile(r"^\s{2}(?P<key>\w+):\s*(?P<val>.*)$")
LIST_ITEM = re.compile(r"^\s{4}-\s*(?P<val>.+)$")


@dataclass
class Entry:
    entry_id: str
    timestamp: datetime
    summary: str
    context: Optional[str] = None
    options: List[str] = field(default_factory=list)
    chosen: Optional[str] = None
    rejected: Optional[dict] = None
    ref: Optional[str] = None
    reason: Optional[str] = None

    @property
    def is_tombstone(self) -> bool:
        return self.ref is not None


def parse_entries(content: str) -> List[Entry]:
    """Parse full streaming file content, return list of Entry.

    Raises ValueError on schema violations:
      - 'missing entry id' — non-entry line before any entry header (after frontmatter)
      - 'timezone' — timestamp without tz
      - 'chosen ... required' — non-tombstone entry missing chosen
    """
    lines = content.splitlines()
    entries: List[Entry] = []
    current: Optional[Entry] = None
    in_frontmatter = False
    frontmatter_done = False

    for raw in lines:
        line = raw.rstrip("\n")

        if line.strip() == "---":
            if not frontmatter_done and not in_frontmatter:
                in_frontmatter = True
                continue
            if in_frontmatter:
                in_frontmatter = False
                frontmatter_done = True
                continue
        if in_frontmatter:
            continue

        if not line.strip():
            if current is not None:
                _finalize(current)
                entries.append(current)
                current = None
            continue

        m = ENTRY_HEADER.match(line)
        if m:
            if current is not None:
                _finalize(current)
                entries.append(current)
            try:
                ts = datetime.fromisoformat(m.group("ts"))
            except ValueError as e:
                raise ValueError(f"invalid timestamp {m.group('ts')}: {e}") from e
            if ts.tzinfo is None:
                raise ValueError(
                    f"timestamp must include timezone: {m.group('ts')}"
                )
            current = Entry(
                entry_id=f"^entry-{m.group('date')}-{m.group('seq')}",
                timestamp=ts,
                summary=m.group("summary").strip(),
            )
            continue

        if current is None:
            if line.startswith("[") or line.lstrip().startswith("["):
                raise ValueError(f"missing entry id for line: {line}")
            continue

        kv = KV_LINE.match(line)
        if kv:
            key = kv.group("key")
            val = kv.group("val").strip()
            if key == "context":
                current.context = val
            elif key == "options":
                current.options = _parse_inline_list(val)
            elif key == "chosen":
                current.chosen = val
            elif key == "ref":
                current.ref = val
            elif key == "reason":
                current.reason = val
            elif key == "rejected":
                current.rejected = {}
            continue

        li = LIST_ITEM.match(line)
        if li and current is not None and current.rejected is not None:
            name, _, reason = li.group("val").partition(":")
            current.rejected[name.strip()] = reason.strip()

    if current is not None:
        _finalize(current)
        entries.append(current)

    return entries


def _finalize(e: Entry) -> None:
    if e.is_tombstone:
        return
    if not e.chosen:
        raise ValueError(f"chosen field required for {e.entry_id}")


def _parse_inline_list(val: str) -> List[str]:
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        return [x.strip() for x in val[1:-1].split(",") if x.strip()]
    return [val] if val else []


def validate_entry(e: Entry) -> None:
    _finalize(e)
    if not e.entry_id.startswith("^entry-"):
        raise ValueError(f"invalid entry id: {e.entry_id}")


if __name__ == "__main__":
    path = Path(sys.argv[1])
    try:
        entries = parse_entries(path.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"❌ {path}: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ {path}: {len(entries)} entries parsed")
