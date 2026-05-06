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

Hook interpreter is selected from shebang so this file works against both
the legacy bash implementation and the Python rewrite.
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


def _run_hook(plugin_root: Path) -> subprocess.CompletedProcess:
    """Run hooks/session-start with given plugin_root. Picks interpreter from shebang.

    Uses cwd + relative path (or POSIX-form path) so bash on Windows doesn't
    mangle backslashes.
    """
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
    return subprocess.run(cmd, capture_output=True, env=env, cwd=str(plugin_root))


def _make_plugin_root(tmp_path: Path, with_skill: bool = True) -> Path:
    """Build an isolated plugin_root mirror in tmp_path for tests that need to
    perturb the filesystem (e.g. SKILL.md missing case)."""
    pr = tmp_path / 'plugin'
    (pr / 'hooks').mkdir(parents=True)
    (pr / 'skills' / 'cadence-bootstrap').mkdir(parents=True)
    shutil.copy(HOOK_PATH, pr / 'hooks' / 'session-start')
    os.chmod(pr / 'hooks' / 'session-start', 0o755)
    if with_skill:
        shutil.copy(SKILL_PATH, pr / 'skills' / 'cadence-bootstrap' / 'SKILL.md')
    return pr


def test_hook_exits_zero_with_valid_json():
    result = _run_hook(REPO_ROOT)
    assert result.returncode == 0, f'stderr: {result.stderr.decode("utf-8", errors="replace")}'
    data = json.loads(result.stdout.decode('utf-8'))
    assert isinstance(data, dict)


def test_hook_event_name_is_session_start():
    result = _run_hook(REPO_ROOT)
    data = json.loads(result.stdout.decode('utf-8'))
    assert data['hookSpecificOutput']['hookEventName'] == 'SessionStart'


def test_chinese_characters_round_trip_cleanly():
    """Known Chinese strings from SKILL.md must appear unmodified in the
    injected context (i.e. not corrupted by encoding mismatch)."""
    result = _run_hook(REPO_ROOT)
    data = json.loads(result.stdout.decode('utf-8'))
    ctx = data['hookSpecificOutput']['additionalContext']
    assert 'Cadence 工作流' in ctx, 'core Chinese marker missing/corrupted'
    assert '讨论' in ctx, 'common Chinese term missing/corrupted'


def test_no_lone_surrogates_in_additional_context():
    """REGRESSION GUARD: Anthropic API rejects JSON containing lone Unicode
    surrogates (U+D800-U+DFFF). Python's surrogateescape error handler can
    smuggle them in when stdin/stdout encoding is not UTF-8 (the original
    Windows GBK bug). Even one such codepoint produces a 400 error."""
    result = _run_hook(REPO_ROOT)
    data = json.loads(result.stdout.decode('utf-8'))
    ctx = data['hookSpecificOutput']['additionalContext']
    bad = [(i, hex(ord(c))) for i, c in enumerate(ctx) if 0xD800 <= ord(c) <= 0xDFFF]
    assert not bad, f'Found {len(bad)} lone surrogate(s); first 5: {bad[:5]}'


def test_additional_context_wrapped_in_extremely_important():
    result = _run_hook(REPO_ROOT)
    data = json.loads(result.stdout.decode('utf-8'))
    ctx = data['hookSpecificOutput']['additionalContext']
    assert ctx.startswith('<EXTREMELY_IMPORTANT>\n'), repr(ctx[:60])
    assert ctx.rstrip('\n').endswith('</EXTREMELY_IMPORTANT>'), repr(ctx[-60:])


def test_frontmatter_stripped_from_injection():
    """The YAML frontmatter (---\\n...\\n---\\n) of SKILL.md must not appear
    in the injected context — only body content."""
    result = _run_hook(REPO_ROOT)
    data = json.loads(result.stdout.decode('utf-8'))
    ctx = data['hookSpecificOutput']['additionalContext']
    assert 'name: cadence-bootstrap' not in ctx, 'frontmatter leaked'
    # Marker that immediately follows frontmatter in SKILL.md
    assert '## Cadence 工作流' in ctx


def test_graceful_degrade_when_skill_missing(tmp_path):
    """SKILL.md missing → exit 0 with empty additionalContext (not crash)."""
    pr = _make_plugin_root(tmp_path, with_skill=False)
    result = _run_hook(pr)
    assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
    data = json.loads(result.stdout.decode('utf-8'))
    assert data['hookSpecificOutput']['hookEventName'] == 'SessionStart'
    assert data['hookSpecificOutput']['additionalContext'] == ''


def test_hook_works_without_claude_plugin_root_env():
    """验证 hook 脚本在缺 CLAUDE_PLUGIN_ROOT 环境变量时通过 BASH_SOURCE fallback
    自定位 plugin_root,输出与显式传入 CLAUDE_PLUGIN_ROOT 一致。"""
    # 显式传 CLAUDE_PLUGIN_ROOT(基线)
    cc_result = _run_hook(REPO_ROOT)
    assert cc_result.returncode == 0
    cc_data = json.loads(cc_result.stdout.decode('utf-8'))
    cc_ctx = cc_data['hookSpecificOutput']['additionalContext']

    hp = REPO_ROOT / 'hooks' / 'session-start'
    shebang = hp.read_text(encoding='utf-8').splitlines()[0]
    if 'python' in shebang:
        cmd = [sys.executable, 'hooks/session-start']
    else:
        cmd = ['bash', 'hooks/session-start']

    # unset CLAUDE_PLUGIN_ROOT(纯 fallback)
    env = os.environ.copy()
    env.pop('CLAUDE_PLUGIN_ROOT', None)
    res = subprocess.run(cmd, capture_output=True, env=env, cwd=str(REPO_ROOT))
    assert res.returncode == 0, res.stderr.decode('utf-8', errors='replace')
    data = json.loads(res.stdout.decode('utf-8'))
    assert data['hookSpecificOutput']['hookEventName'] == 'SessionStart'
    assert data['hookSpecificOutput']['additionalContext'] == cc_ctx, (
        'fallback (no CLAUDE_PLUGIN_ROOT) output diverges from explicit env path'
    )
