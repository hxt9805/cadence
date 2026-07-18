"""Cadence must treat software as one project kind, not the default schema."""

import json
from pathlib import Path


ROOT = Path(__file__).parent.parent
INIT_SKILL = (ROOT / "skills/cadence-init/SKILL.md").read_text(encoding="utf-8")
SCAN_RULES = (
    ROOT / "skills/cadence-init/references/scan-rules.md"
).read_text(encoding="utf-8")
SCANNER = (
    ROOT / "skills/cadence-init/agents/project-scanner.md"
).read_text(encoding="utf-8")
QUERY = (
    ROOT / "skills/project-discuss/references/query-behavior.md"
).read_text(encoding="utf-8")
PROJECT_DISCUSS = (
    ROOT / "skills/project-discuss/SKILL.md"
).read_text(encoding="utf-8")


def test_existing_project_detection_accepts_non_software_materials():
    assert "有任何有意义的项目材料" in INIT_SKILL
    for material in ["研究材料", "文稿", "学习记录", "运营计划", "源代码"]:
        assert material in INIT_SKILL


def test_scanner_selects_a_domain_adapter_after_generic_discovery():
    for term in [
        "通用发现",
        "软件",
        "研究",
        "写作",
        "学习",
        "运营",
        "项目主产物",
    ]:
        assert term in SCAN_RULES
    assert "代码是事实，文档是意图" not in SCAN_RULES


def test_scanner_report_keeps_general_fields_and_optional_software_fields():
    assert '"project_kind"' in SCANNER
    assert '"primary_artifacts"' in SCANNER
    assert "detected_stack" in SCANNER
    assert "仅软件项目" in SCANNER


def test_query_authority_depends_on_question_and_declared_source_of_truth():
    assert "问题相关性" in QUERY
    assert "项目声明的权威来源" in QUERY
    assert "优先级：**代码 > cadence 档案 > 手写文档**" not in QUERY
    for artifact in ["研究方案", "稿件", "学习记录", "运营看板", "代码"]:
        assert artifact in QUERY


def test_project_discuss_verifies_primary_artifacts_not_only_code():
    assert "项目主产物 / 权威来源" in PROJECT_DISCUSS


def test_public_plugin_descriptions_are_domain_neutral():
    def read(relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    descriptions = [
        read("README.md").splitlines()[2],
        read("AGENTS.md").splitlines()[2],
        json.loads(read(".claude-plugin/plugin.json"))["description"],
        json.loads(read(".codex-plugin/plugin.json"))["description"],
        json.loads(read(".codex-plugin/plugin.json"))["interface"][
            "shortDescription"
        ],
    ]
    marketplace = json.loads(read(".claude-plugin/marketplace.json"))
    descriptions.extend(
        plugin["description"] for plugin in marketplace["plugins"]
    )

    forbidden = ["软件开发", "software development", "dev workflow"]
    for description in descriptions:
        lowered = description.lower()
        assert not any(term.lower() in lowered for term in forbidden), (
            f"domain-locked public description: {description}"
        )
