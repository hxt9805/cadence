"""
ADR discussion doc 最小结构 validator(Phase B)。

Phase B scope:
- front-matter:status in {accepted, superseded},source_streaming_file 非空
- body:4 个 h2 节存在(## Context / ## Decision / ## Rationale / ## Alternatives Considered)

**不校验**(留 Phase C):alternatives 内部结构、rejected_because、from_source、
references 文件存在。

DRY:复制 validate_streaming.py 的 try/except ImportError shim 和
if __name__ == "__main__" 段;暂不共享 helper,待第 4 个 validator
(Phase D handoff)时再抽 _common.py。
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

import _common  # noqa: F401  # imported for UTF-8 stdout/stderr reconfigure side-effect (Windows GBK consoles)

try:
    import yaml
except ImportError as e:
    raise SystemExit("pip install pyyaml required") from e


# v0.4 完整决策状态集(archived 不在此集合 — 它是物理动作)
VALID_STATUS = {"accepted", "implemented", "stale", "superseded"}
REQUIRED_SECTIONS = ["Context", "Decision", "Rationale", "Alternatives Considered"]

SECTION_RE = re.compile(r"^##\s+(?P<name>.+?)\s*$", re.MULTILINE)


@dataclass
class ADRDoc:
    front_matter: dict
    body: str
    sections: List[str]


def parse_adr(content: str) -> ADRDoc:
    """Parse ADR markdown with yaml frontmatter. Raises ValueError."""
    if not content.startswith("---"):
        raise ValueError("missing front matter")
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("malformed front matter")
    fm = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    sections = [m.group("name").strip() for m in SECTION_RE.finditer(body)]
    return ADRDoc(front_matter=fm, body=body, sections=sections)


def validate_adr_minimal(doc: ADRDoc) -> None:
    """Phase B 最小校验:4 节存在 + front-matter 必填。"""
    fm = doc.front_matter
    if fm.get("status") not in VALID_STATUS:
        raise ValueError(
            f"status must be in {VALID_STATUS}, got {fm.get('status')!r}"
        )
    if not fm.get("source_streaming_file"):
        raise ValueError("front_matter.source_streaming_file required")

    for required in REQUIRED_SECTIONS:
        if required not in doc.sections:
            raise ValueError(f"body missing required section: ## {required}")


DECISION_ID_RE = re.compile(r"^D\d+$")
# Alternative 方案名取自第一对 **...**;后续括号注释(如 "**Do Nothing**(保持当前状态)"
# 里的"(保持当前状态)")不入 name,仅作可读性修饰
ALTERNATIVE_HEADER_RE = re.compile(r"^-\s+\*\*(?P<name>.+?)\*\*")
# 接受任意缩进宽度(2-space / 4-space / tab 都兼容),只要比 alternative header 多缩进
ALTERNATIVE_FIELD_RE = re.compile(r"^\s+-\s+(?P<key>\w+):\s*(?P<val>.+)$")


def _parse_alternatives(body: str) -> list:
    """Extract alternatives list from 'Alternatives Considered' section body.

    Returns list of dicts: [{name, rejected_because?, from_source?, source?}, ...]
    """
    lines = body.splitlines()
    in_alt_section = False
    alts = []
    current = None
    for line in lines:
        if line.startswith("## Alternatives Considered"):
            in_alt_section = True
            continue
        if in_alt_section and line.startswith("## "):
            break
        if not in_alt_section:
            continue
        m = ALTERNATIVE_HEADER_RE.match(line)
        if m:
            if current is not None:
                alts.append(current)
            current = {"name": m.group("name").strip()}
            continue
        if current is None:
            continue
        fm = ALTERNATIVE_FIELD_RE.match(line)
        if fm:
            key = fm.group("key")
            val = fm.group("val").strip().strip('"')
            if key == "from_source":
                current[key] = val.lower() == "true"
            else:
                current[key] = val
    if current is not None:
        alts.append(current)
    return alts


def validate_adr_full(doc: ADRDoc, base_dir: Path) -> None:
    """Phase C 完整校验:最小 + Alternatives 内部 + references 存在 + decision_id 格式。

    不校验 rejected_because 是否从原文抽取(§ 16.6 留 v0.4+)。
    """
    validate_adr_minimal(doc)

    # decision_id 格式(可选字段,填了必须合法)
    did = doc.front_matter.get("decision_id")
    if did is not None and not DECISION_ID_RE.match(str(did)):
        raise ValueError(
            f"decision_id must match ^D\\d+$, got {did!r}"
        )

    # Alternatives 内部字段
    alts = _parse_alternatives(doc.body)
    if not alts:
        raise ValueError("Alternatives Considered section must list ≥1 alternative")
    for alt in alts:
        name = alt.get("name", "<unnamed>")
        if "rejected_because" not in alt:
            raise ValueError(f"alternative {name!r} missing rejected_because")
        if "source" not in alt:
            raise ValueError(f"alternative {name!r} missing source (^entry-...)")
        if "from_source" not in alt:
            raise ValueError(
                f"alternative {name!r} missing from_source (true/false)"
            )

    # references 文件存在
    refs = doc.front_matter.get("references") or []
    for ref in refs:
        ref_path = Path(base_dir) / ref
        if not ref_path.exists():
            raise ValueError(f"references entry not found: {ref}")


if __name__ == "__main__":
    path = Path(sys.argv[1])
    # 第二参数可选:references 路径解析基准;默认 = 文件所在目录
    base_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else path.parent
    doc = parse_adr(path.read_text(encoding="utf-8"))
    try:
        validate_adr_full(doc, base_dir=base_dir)
    except ValueError as e:
        print(f"❌ {path}: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ {path}: ADR full schema valid (base_dir={base_dir})")
