"""
streaming/<file>.md entry parser + validator.

Accepted surface schemas(见 recording-protocol.md § α):
    1. Legacy markdown entry:
    ^entry-<YYYYMMDD>-<seq> [<ISO-8601 TZ>] <summary>
      context: <...>
      options: [A, B]
      chosen: <...>
      rejected:
        - <name>: <reason>
      ref: ^entry-xx        ← tombstone 专用
      reason: <...>          ← tombstone 专用
    2. YAML-frontmatter entry:
    ---
    id: ^entry-<YYYYMMDD>-<seq> | e<seq>
    created: <ISO-8601 TZ>
    detail_profile: light | standard | high
    context: <...>
    chosen: <...>
    rationale: <...>
    semantic_slots: {...}
    ---

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

yaml = _common.ensure_yaml()

ENTRY_HEADER = re.compile(
    r"^\^entry-(?P<date>\d{8})-(?P<seq>\d{2,})\s+"
    r"\[(?P<ts>[^\]]+)\]\s+(?P<summary>.+)$"
)
KV_LINE = re.compile(r"^\s{2}(?P<key>\w+):\s*(?P<val>.*)$")
LIST_ITEM = re.compile(r"^\s{4}-\s*(?P<val>.+)$")
VALID_PROFILES = {"light", "standard", "high"}
YAML_ENTRY_ID = re.compile(r"^(?:\^entry-\d{8}-\d{2,}|e\d+)$")
VAGUE_NUMBERED_CHOICE = re.compile(
    r"^(?:采用|选择|按|用)?\s*方案\s*[A-Za-z0-9一二三四五六七八九十]+[。.]?$"
)


@dataclass
class Entry:
    entry_id: str
    timestamp: datetime
    summary: str
    status: str = "accepted"
    detail_profile: str = "standard"
    context: Optional[str] = None
    options: List[str] = field(default_factory=list)
    chosen: Optional[str] = None
    rejected: Optional[dict] = None
    rationale: Optional[str] = None
    semantic_slots: dict = field(default_factory=dict)
    not_applicable: List[str] = field(default_factory=list)
    provenance: dict = field(default_factory=dict)
    ref: Optional[str] = None
    reason: Optional[str] = None

    @property
    def is_tombstone(self) -> bool:
        return self.ref is not None


def parse_entries(content: str) -> List[Entry]:
    """Parse full streaming file content into normalized Entry records.

    Raises ValueError on schema violations:
      - 'missing entry id' — non-entry line before any entry header (after frontmatter)
      - 'timezone' — timestamp without tz
      - 'chosen ... required' — non-tombstone entry missing chosen
    """
    legacy_entries = _parse_legacy_entries(content)
    yaml_entries = _parse_yaml_entries(content)
    entries = legacy_entries + yaml_entries
    entries.sort(key=lambda entry: entry.timestamp)
    return entries


def _parse_legacy_entries(content: str) -> List[Entry]:
    """Parse the historical caret-header surface format."""
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


def _parse_yaml_entries(content: str) -> List[Entry]:
    """Parse YAML-frontmatter entries while ignoring file-level frontmatter."""
    lines = content.splitlines()
    entries: List[Entry] = []
    index = 0
    in_code_fence = False

    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_fence = not in_code_fence
            index += 1
            continue
        if in_code_fence or lines[index] != "---":
            index += 1
            continue

        closing = index + 1
        while closing < len(lines) and lines[closing] != "---":
            closing += 1
        if closing >= len(lines):
            break

        raw_yaml = "\n".join(lines[index + 1:closing])
        data = yaml.safe_load(raw_yaml) or {}
        if isinstance(data, dict) and (data.get("id") or data.get("entry_id")):
            entry_id = str(data.get("id") or data.get("entry_id")).strip()
            created = data.get("created") or data.get("timestamp")
            timestamp = _parse_timestamp(created)
            summary = str(data.get("summary") or "").strip()
            if not summary:
                summary = _find_following_heading(lines, closing + 1)
            entry = Entry(
                entry_id=entry_id,
                timestamp=timestamp,
                summary=summary or entry_id,
                status=str(data.get("status") or "accepted"),
                detail_profile=str(
                    data.get("detail_profile") or data.get("fidelity") or "standard"
                ).lower(),
                context=_optional_text(data.get("context")),
                options=_string_list(data.get("options")),
                chosen=_optional_text(data.get("chosen")),
                rejected=data.get("rejected") if isinstance(data.get("rejected"), dict) else None,
                rationale=_optional_text(data.get("rationale")),
                semantic_slots=(
                    data.get("semantic_slots")
                    if isinstance(data.get("semantic_slots"), dict)
                    else {}
                ),
                not_applicable=_string_list(data.get("not_applicable")),
                provenance=(
                    data.get("provenance")
                    if isinstance(data.get("provenance"), dict)
                    else {}
                ),
                ref=_optional_text(data.get("ref")),
                reason=_optional_text(data.get("reason")),
            )
            _finalize(entry)
            entries.append(entry)

        index = closing + 1

    return entries


def _find_following_heading(lines: List[str], start: int) -> str:
    for line in lines[start:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        if stripped:
            break
    return ""


def _parse_timestamp(value) -> datetime:
    if isinstance(value, datetime):
        timestamp = value
    elif value is None:
        raise ValueError("created timestamp required for YAML entry")
    else:
        try:
            timestamp = datetime.fromisoformat(str(value))
        except ValueError as error:
            raise ValueError(f"invalid timestamp {value}: {error}") from error
    if timestamp.tzinfo is None:
        raise ValueError(f"timestamp must include timezone: {value}")
    return timestamp


def _optional_text(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _finalize(e: Entry) -> None:
    if e.is_tombstone:
        return
    if not YAML_ENTRY_ID.match(e.entry_id):
        raise ValueError(f"invalid entry id: {e.entry_id}")
    if e.detail_profile not in VALID_PROFILES:
        raise ValueError(
            f"detail_profile must be in {sorted(VALID_PROFILES)}, "
            f"got {e.detail_profile!r}"
        )
    if not e.chosen:
        raise ValueError(f"chosen field required for {e.entry_id}")
    if e.detail_profile == "high":
        if not e.context:
            raise ValueError(f"context field required for high profile {e.entry_id}")
        if not e.rationale:
            raise ValueError(f"rationale field required for high profile {e.entry_id}")
        if not e.semantic_slots and not e.not_applicable:
            raise ValueError(
                f"semantic_slots or not_applicable required for high profile {e.entry_id}"
            )


def _parse_inline_list(val: str) -> List[str]:
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        return [x.strip() for x in val[1:-1].split(",") if x.strip()]
    return [val] if val else []


def validate_entry(e: Entry) -> None:
    _finalize(e)


def validate_entry_with_warnings(e: Entry) -> List[str]:
    """Return profile-aware soft warnings after hard validation succeeds."""
    _finalize(e)
    warnings: List[str] = []
    if e.detail_profile == "standard" and not e.rationale:
        warnings.append(f"{e.entry_id}: standard profile missing rationale")
    if e.chosen and VAGUE_NUMBERED_CHOICE.fullmatch(e.chosen.strip()):
        warnings.append(
            f"{e.entry_id}: chosen 只写了方案编号；"
            "必须记录被承接方案的具体语义"
        )
    return warnings


if __name__ == "__main__":
    path = Path(sys.argv[1])
    try:
        entries = parse_entries(path.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"❌ {path}: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ {path}: {len(entries)} entries parsed")
