"""Cadence SessionStart hook contract tests.

Verifies the CC SessionStart hook output contract:
  1. Exit 0 + valid JSON
  2. hookEventName == "SessionStart"
  3. Chinese characters round-trip cleanly
  4. No lone Unicode surrogates (regression test — see Gate 1 design)
  5. additionalContext wrapped in <EXTREMELY_IMPORTANT>...</EXTREMELY_IMPORTANT>
  6. Frontmatter stripped from injected content
  7. Graceful degrade when SKILL.md missing
  8. Fallback works when CLAUDE_PLUGIN_ROOT env var missing
  9. cadence/_INDEX.md gating: missing → empty context (commit 08ca9c6)

Hook interpreter is selected from shebang so this file works against both
the legacy bash implementation and the Python rewrite.

Tests run against an isolated mirror in tmp_path so they don't depend on
the real repo having a cadence/_INDEX.md (it doesn't — this repo is the
plugin source, not a cadence-managed project).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
HOOK_PATH = REPO_ROOT / 'hooks' / 'session-start'
SKILL_PATH = REPO_ROOT / 'skills' / 'cadence-bootstrap' / 'SKILL.md'


def _run_hook(plugin_root: Path, project_root: Path = None) -> subprocess.CompletedProcess:
    """Run hooks/session-start with given plugin_root. Picks interpreter from shebang.

    Uses cwd + relative path (or POSIX-form path) so bash on Windows doesn't
    mangle backslashes. project_root defaults to plugin_root (typical setup
    where the cadence-managed project also hosts the plugin mirror).
    """
    if project_root is None:
        project_root = plugin_root
    hp = plugin_root / 'hooks' / 'session-start'
    shebang = hp.read_text(encoding='utf-8').splitlines()[0]
    if 'python' in shebang:
        cmd = [sys.executable, 'hooks/session-start']
    elif 'bash' in shebang or shebang.startswith('#!/bin/sh'):
        cmd = ['bash', 'hooks/session-start']
    else:
        raise RuntimeError(f'Unrecognized shebang: {shebang!r}')
    env = os.environ.copy()
    env['CLAUDE_PLUGIN_ROOT'] = plugin_root.resolve().as_posix()
    env['CLAUDE_PROJECT_DIR'] = project_root.resolve().as_posix()
    return subprocess.run(cmd, capture_output=True, env=env, cwd=str(plugin_root))


def _make_plugin_root(
    tmp_path: Path,
    with_skill: bool = True,
    with_index: bool = True,
) -> Path:
    """Build an isolated plugin_root mirror in tmp_path.

    By default builds a fully cadence-managed project layout: hook + bootstrap
    SKILL.md + cadence/_INDEX.md. Toggle flags to perturb specific files for
    failure-mode tests.
    """
    pr = tmp_path / 'plugin'
    (pr / 'hooks').mkdir(parents=True)
    (pr / 'skills' / 'cadence-bootstrap').mkdir(parents=True)
    shutil.copy(HOOK_PATH, pr / 'hooks' / 'session-start')
    os.chmod(pr / 'hooks' / 'session-start', 0o755)
    if with_skill:
        shutil.copy(SKILL_PATH, pr / 'skills' / 'cadence-bootstrap' / 'SKILL.md')
    if with_index:
        (pr / 'cadence').mkdir(parents=True, exist_ok=True)
        (pr / 'cadence' / '_INDEX.md').write_text(
            '# Cadence Index (test fixture)\n', encoding='utf-8'
        )
    return pr


def test_hook_exits_zero_with_valid_json(tmp_path):
    pr = _make_plugin_root(tmp_path)
    result = _run_hook(pr)
    assert result.returncode == 0, f'stderr: {result.stderr.decode("utf-8", errors="replace")}'
    data = json.loads(result.stdout.decode('utf-8'))
    assert isinstance(data, dict)


def test_hook_event_name_is_session_start(tmp_path):
    pr = _make_plugin_root(tmp_path)
    result = _run_hook(pr)
    data = json.loads(result.stdout.decode('utf-8'))
    assert data['hookSpecificOutput']['hookEventName'] == 'SessionStart'


def test_chinese_characters_round_trip_cleanly(tmp_path):
    """Known Chinese strings from SKILL.md must appear unmodified in the
    injected context (i.e. not corrupted by encoding mismatch)."""
    pr = _make_plugin_root(tmp_path)
    result = _run_hook(pr)
    data = json.loads(result.stdout.decode('utf-8'))
    ctx = data['hookSpecificOutput']['additionalContext']
    assert 'Cadence 工作流' in ctx, 'core Chinese marker missing/corrupted'
    assert '讨论' in ctx, 'common Chinese term missing/corrupted'


def test_no_lone_surrogates_in_additional_context(tmp_path):
    """REGRESSION GUARD: Anthropic API rejects JSON containing lone Unicode
    surrogates (U+D800-U+DFFF). Python's surrogateescape error handler can
    smuggle them in when stdin/stdout encoding is not UTF-8 (the original
    Windows GBK bug). Even one such codepoint produces a 400 error."""
    pr = _make_plugin_root(tmp_path)
    result = _run_hook(pr)
    data = json.loads(result.stdout.decode('utf-8'))
    ctx = data['hookSpecificOutput']['additionalContext']
    bad = [(i, hex(ord(c))) for i, c in enumerate(ctx) if 0xD800 <= ord(c) <= 0xDFFF]
    assert not bad, f'Found {len(bad)} lone surrogate(s); first 5: {bad[:5]}'


def test_additional_context_wrapped_in_extremely_important(tmp_path):
    pr = _make_plugin_root(tmp_path)
    result = _run_hook(pr)
    data = json.loads(result.stdout.decode('utf-8'))
    ctx = data['hookSpecificOutput']['additionalContext']
    assert ctx.startswith('<EXTREMELY_IMPORTANT>\n'), repr(ctx[:60])
    assert ctx.rstrip('\n').endswith('</EXTREMELY_IMPORTANT>'), repr(ctx[-60:])


def test_frontmatter_stripped_from_injection(tmp_path):
    """The YAML frontmatter (---\\n...\\n---\\n) of SKILL.md must not appear
    in the injected context — only body content."""
    pr = _make_plugin_root(tmp_path)
    result = _run_hook(pr)
    data = json.loads(result.stdout.decode('utf-8'))
    ctx = data['hookSpecificOutput']['additionalContext']
    assert 'name: cadence-bootstrap' not in ctx, 'frontmatter leaked'
    # Marker that immediately follows frontmatter in SKILL.md
    assert '## Cadence 工作流' in ctx


def test_graceful_degrade_when_skill_missing(tmp_path):
    """SKILL.md missing → exit 0 with empty additionalContext (not crash).
    _INDEX.md must still exist so we exercise the SKILL.md branch, not the
    earlier _INDEX.md gate."""
    pr = _make_plugin_root(tmp_path, with_skill=False, with_index=True)
    result = _run_hook(pr)
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    data = json.loads(result.stdout.decode('utf-8'))
    assert data['hookSpecificOutput']['hookEventName'] == 'SessionStart'
    assert data['hookSpecificOutput']['additionalContext'] == ''


def test_no_index_md_returns_empty_context(tmp_path):
    """commit 08ca9c6: project without cadence/_INDEX.md is not cadence-managed
    → hook returns empty context to keep non-cadence projects bootstrap-noise free."""
    pr = _make_plugin_root(tmp_path, with_skill=True, with_index=False)
    result = _run_hook(pr)
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    data = json.loads(result.stdout.decode('utf-8'))
    assert data['hookSpecificOutput']['hookEventName'] == 'SessionStart'
    assert data['hookSpecificOutput']['additionalContext'] == ''


def test_hook_works_without_claude_plugin_root_env(tmp_path):
    """验证 hook 脚本在缺 CLAUDE_PLUGIN_ROOT 环境变量时通过 BASH_SOURCE fallback
    自定位 plugin_root,输出与显式传入 CLAUDE_PLUGIN_ROOT 一致。"""
    pr = _make_plugin_root(tmp_path)

    # 显式传 CLAUDE_PLUGIN_ROOT(基线)
    cc_result = _run_hook(pr)
    assert cc_result.returncode == 0
    cc_data = json.loads(cc_result.stdout.decode('utf-8'))
    cc_ctx = cc_data['hookSpecificOutput']['additionalContext']

    hp = pr / 'hooks' / 'session-start'
    shebang = hp.read_text(encoding='utf-8').splitlines()[0]
    if 'python' in shebang:
        cmd = [sys.executable, 'hooks/session-start']
    else:
        cmd = ['bash', 'hooks/session-start']

    # unset CLAUDE_PLUGIN_ROOT(纯 fallback)— 但 CLAUDE_PROJECT_DIR 仍需指向 mirror
    # 否则 _INDEX.md gate 会让两次都返回空,无法区分 fallback 是否真的工作。
    env = os.environ.copy()
    env.pop('CLAUDE_PLUGIN_ROOT', None)
    env['CLAUDE_PROJECT_DIR'] = pr.resolve().as_posix()
    res = subprocess.run(cmd, capture_output=True, env=env, cwd=str(pr))
    assert res.returncode == 0, res.stderr.decode('utf-8', errors='replace')
    data = json.loads(res.stdout.decode('utf-8'))
    assert data['hookSpecificOutput']['hookEventName'] == 'SessionStart'
    assert data['hookSpecificOutput']['additionalContext'] == cc_ctx, (
        'fallback (no CLAUDE_PLUGIN_ROOT) output diverges from explicit env path'
    )
