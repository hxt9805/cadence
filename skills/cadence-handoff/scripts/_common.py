"""共享 boilerplate(Phase D 起抽)。只放跨 validator 纯工具,不放领域逻辑。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

# Windows GBK 控制台无法输出 ✅/❌ → UnicodeEncodeError → 误报 validator 失败
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, Exception):
        pass


def ensure_yaml():
    """统一的 yaml import shim。返回 yaml 模块或退出。"""
    try:
        import yaml
        return yaml
    except ImportError as e:
        raise SystemExit("pip install pyyaml required") from e


def run_cli(path_arg: str, parser: Callable, validator: Callable, label: str):
    """统一的 `python validate_*.py <path>` CLI 入口。

    parser: 输入 (content: str) → 任意 doc 对象
    validator: 输入 (doc) → None(抛 ValueError 表示失败)
    label: 用于 success 消息的 schema 名
    """
    path = Path(path_arg)
    content = path.read_text(encoding="utf-8")
    doc = parser(content)
    try:
        validator(doc)
    except ValueError as e:
        print(f"❌ {path}: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"✅ {path}: {label} valid")
