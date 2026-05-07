"""
保证 skills/cadence-handoff/scripts/ 下的 validate_handoff.py + _common.py
与 tests/schema/ 下的 dev 副本 byte-equal。

为什么有两份:
- tests/schema/ 给 pytest 用(裸 import,conftest.py 加 sys.path)
- skills/cadence-handoff/scripts/ 是 plugin 分发版本,SKILL.md 调用它做写入前 schema 校验
- _common.py 还被另外 3 个 validator(adr/consolidator/streaming)用,不能整体搬走
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_SCHEMA = REPO_ROOT / "tests" / "schema"
RUNTIME_SCRIPTS = REPO_ROOT / "skills" / "cadence-handoff" / "scripts"

PAIRS = [
    ("validate_handoff.py", "validate_handoff.py"),
    ("_common.py", "_common.py"),
]


def test_runtime_copies_match_dev():
    for dev_name, runtime_name in PAIRS:
        dev = (TESTS_SCHEMA / dev_name).read_bytes()
        runtime = (RUNTIME_SCRIPTS / runtime_name).read_bytes()
        assert dev == runtime, (
            f"{runtime_name} 在 tests/schema 与 skills/cadence-handoff/scripts 之间漂移;"
            f"修改任一处后必须同步另一处"
        )
