"""Runtime discovery contracts for the shared Cadence skill sources."""

import json
from pathlib import Path


ROOT = Path(__file__).parent.parent


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_opencode_injects_the_shared_root_bootstrap_skill():
    plugin = _read(".opencode/plugin/cadence.js")
    assert "const SKILLS_DIR = path.join(PLUGIN_ROOT, 'skills')" in plugin
    assert (
        "path.join(SKILLS_DIR, 'cadence-bootstrap', 'SKILL.md')" in plugin
    )
    assert "fs.readFileSync(skillPath, 'utf8')" in plugin


def test_codex_discovers_the_shared_root_skills_directory():
    manifest = json.loads(_read(".codex-plugin/plugin.json"))
    assert manifest["skills"] == "./skills/"
    assert (ROOT / "skills" / "cadence-bootstrap" / "SKILL.md").is_file()
    assert (
        ROOT
        / "skills"
        / "project-discuss"
        / "references"
        / "recording-fidelity.md"
    ).is_file()


def test_claude_hook_reads_the_shared_root_bootstrap_skill():
    hook = _read("hooks/session-start")
    assert (
        'BOOTSTRAP_FILE="$PLUGIN_ROOT/skills/cadence-bootstrap/SKILL.md"'
        in hook
    )


def test_no_runtime_specific_copy_of_recording_fidelity_exists():
    canonical = (
        ROOT
        / "skills"
        / "project-discuss"
        / "references"
        / "recording-fidelity.md"
    ).resolve()
    copies = [
        path.resolve()
        for path in ROOT.rglob("recording-fidelity.md")
        if path.resolve() != canonical
        and "docs" not in path.relative_to(ROOT).parts
    ]
    assert copies == []
