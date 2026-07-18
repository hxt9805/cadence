# Cadence Recording Fidelity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Cadence preserve accepted decisions at a risk-adaptive level of detail without storing transcripts or restricting the plugin to software projects.

**Architecture:** Normalize legacy Markdown and YAML entries into one `DecisionRecord`, apply profile-aware structural checks, and make consolidation coverage explicit before archive. Keep bootstrap concise, move conditional guidance into one recording-fidelity reference, and keep handoff short by storing verified canonical pointers rather than copied detail.

**Tech Stack:** Markdown skills, Python 3.13, PyYAML, pytest, Bash SessionStart hook.

## Global Constraints

- Cadence remains domain-neutral; project type never selects a fixed schema.
- Risk classification uses reversibility, scope, loss, duration, external commitment, uncertainty, and collaboration complexity.
- Legacy Markdown and recommended YAML entries remain readable without bulk migration.
- Handoff remains a 15–30 line bookmark.
- Never record raw transcripts, secrets, unnecessary personal data, or replaceable long tool output.
- Claude Code, OpenCode, and Codex share the same semantic contract.
- New behavior is test-first; each red test must fail for the missing feature before implementation.

---

### Task 1: Normalize streaming entries and validate fidelity profiles

**Files:**
- Modify: `tests/schema/validate_streaming.py`
- Modify: `tests/schema/test_streaming_entry.py`
- Create: `tests/schema/fixtures/streaming_yaml_valid.md`
- Create: `tests/schema/fixtures/streaming_high_missing_rationale.md`
- Create: `tests/schema/fixtures/streaming_domain_neutral.md`

**Interfaces:**
- Consumes: legacy `^entry-...` blocks and YAML fenced entry blocks embedded after streaming file frontmatter.
- Produces: `Entry.detail_profile`, `Entry.rationale`, `Entry.semantic_slots`, `Entry.not_applicable`, `Entry.provenance`, plus `validate_entry_with_warnings(entry) -> list[str]`.

- [x] **Step 1: Write failing dual-schema and profile tests**

Add tests proving:

```python
def test_yaml_entry_parses_to_decision_record():
    entry = parse_entries(_load("streaming_yaml_valid.md"))[0]
    assert entry.entry_id == "^entry-20260718-01"
    assert entry.detail_profile == "high"
    assert entry.semantic_slots["rules_and_invariants"]


def test_high_profile_requires_rationale():
    with pytest.raises(ValueError, match="rationale.*required"):
        parse_entries(_load("streaming_high_missing_rationale.md"))


def test_non_software_high_decision_uses_same_model():
    entry = parse_entries(_load("streaming_domain_neutral.md"))[0]
    assert entry.detail_profile == "high"
    assert "external_commitments" in entry.semantic_slots
```

- [x] **Step 2: Run the focused tests and confirm RED**

Run:

```powershell
py -3.13 -m pytest tests/schema/test_streaming_entry.py -q
```

Expected: failures because YAML entries and fidelity fields are not parsed.

- [x] **Step 3: Implement the normalized entry model**

Extend `Entry` with:

```python
detail_profile: str = "standard"
rationale: Optional[str] = None
semantic_slots: dict = field(default_factory=dict)
not_applicable: List[str] = field(default_factory=list)
provenance: dict = field(default_factory=dict)
```

Parse both surface formats into `Entry`. Keep `_finalize` strict for IDs, timestamps, `chosen`, and High `context/rationale`; return warnings for Standard omissions and vague numbered choices.

- [x] **Step 4: Run focused and full schema tests**

Run:

```powershell
py -3.13 -m pytest tests/schema/test_streaming_entry.py -q
py -3.13 -m pytest tests/schema -q
```

Expected: all pass.

- [x] **Step 5: Commit Task 1**

```powershell
git add tests/schema/validate_streaming.py tests/schema/test_streaming_entry.py tests/schema/fixtures
git commit -m "feat: validate domain-neutral decision fidelity"
```

### Task 2: Add canonical merge and entry coverage to consolidation plans

**Files:**
- Modify: `tests/schema/validate_consolidator_plan.py`
- Modify: `tests/schema/test_consolidator_plan.py`
- Create: `tests/schema/fixtures/consolidator_plan_merge_coverage.yaml`
- Create: `tests/schema/fixtures/consolidator_plan_missing_coverage.yaml`
- Modify: `skills/project-discuss/agents/recall-consolidator.md`

**Interfaces:**
- Consumes: normalized streaming entry IDs and the existing plan schema.
- Produces: `canonical_action`, `coverage[]`, expanded lifecycle triggers, and archive gating.

- [x] **Step 1: Write failing merge, coverage, and trigger tests**

Add tests proving:

```python
def test_merge_plan_with_complete_coverage_passes():
    validate_plan(_load("consolidator_plan_merge_coverage.yaml"))


def test_archive_rejects_missing_coverage():
    with pytest.raises(ValueError, match="coverage"):
        validate_plan(_load("consolidator_plan_missing_coverage.yaml"))


@pytest.mark.parametrize("trigger", [
    "section_70", "section_100", "cold_n_rounds", "mtime_change",
    "high_impact_accepted", "topic_closed",
])
def test_documented_triggers_are_accepted(trigger):
    plan = _load("consolidator_plan_merge_coverage.yaml")
    plan["trigger_reason"] = trigger
    validate_plan(plan)
```

- [x] **Step 2: Run focused tests and confirm RED**

Run:

```powershell
py -3.13 -m pytest tests/schema/test_consolidator_plan.py -q
```

Expected: new trigger and coverage tests fail.

- [x] **Step 3: Implement consolidation plan validation**

Add:

```python
VALID_CANONICAL_ACTIONS = {"create_new", "merge_into_existing"}
VALID_COVERAGE_DISPOSITIONS = {
    "incorporated", "superseded", "duplicate", "deferred", "out_of_scope",
}
```

Require non-empty coverage when `streaming_file_updates.front_matter_update.status == "archived"`. Validate source IDs, disposition, section for incorporated entries, and `superseded_by` for superseded entries.

- [x] **Step 4: Update consolidator instructions**

Require the plan-only agent to:

- choose or create one canonical owner;
- emit coverage for every live entry;
- refuse archive if coverage is incomplete;
- consolidate a single High entry or explicitly closed topic;
- use `merge_into_existing` when a canonical discussion already exists.

- [x] **Step 5: Run focused and full tests**

Run:

```powershell
py -3.13 -m pytest tests/schema/test_consolidator_plan.py -q
py -3.13 -m pytest tests/schema -q
```

Expected: all pass.

- [x] **Step 6: Commit Task 2**

```powershell
git add tests/schema/validate_consolidator_plan.py tests/schema/test_consolidator_plan.py tests/schema/fixtures skills/project-discuss/agents/recall-consolidator.md
git commit -m "feat: require canonical coverage before archive"
```

### Task 3: Extend compact handoff and resume with canonical pointers

**Files:**
- Modify: `tests/schema/validate_handoff.py`
- Modify: `tests/schema/test_handoff_v03.py`
- Create: `tests/schema/fixtures/handoff_v04_valid.md`
- Create: `tests/schema/fixtures/handoff_v04_partial.md`
- Modify: `skills/cadence-handoff/SKILL.md`
- Modify: `skills/cadence-resume/SKILL.md`

**Interfaces:**
- Consumes: canonical discussion paths and SHA-1 values.
- Produces: optional backward-compatible `continuation_refs` and `fidelity` fields.

- [x] **Step 1: Write failing v0.4 handoff tests**

Add tests proving:

```python
def test_v04_continuation_refs_and_fidelity_pass():
    doc = _load("handoff_v04_valid.md")
    validate_handoff_v03(doc)


def test_continuation_ref_sha1_must_be_valid():
    doc = _load("handoff_v04_valid.md")
    doc.front_matter["continuation_refs"][0]["sha1"] = "bad"
    with pytest.raises(ValueError, match="continuation_refs"):
        validate_handoff_v03(doc)


def test_partial_fidelity_requires_uncovered_items():
    doc = _load("handoff_v04_partial.md")
    del doc.front_matter["fidelity"]["uncovered"]
    with pytest.raises(ValueError, match="uncovered"):
        validate_handoff_v03(doc)
```

- [x] **Step 2: Run handoff tests and confirm RED**

Run:

```powershell
py -3.13 -m pytest tests/schema/test_handoff_v03.py -q
```

Expected: v0.4 fields are not validated.

- [x] **Step 3: Implement backward-compatible validation**

Allow existing v0.3 handoffs unchanged. When new fields exist:

- allow 1–3 continuation refs;
- require `discussions/` paths and lowercase SHA-1;
- require fidelity status in `complete|partial`;
- require empty uncovered for complete and non-empty uncovered for partial.

- [x] **Step 4: Update handoff and resume workflow**

Replace “补漏不再需要” with a fidelity sweep. Keep the 15–30 line target, add canonical refs, require High/closed topics to bypass the `<2 entries / <10 minutes` skip, and make resume read and verify refs before claiming context restored.

- [x] **Step 5: Run handoff, cleanup, and full schema tests**

Run:

```powershell
py -3.13 -m pytest tests/schema/test_handoff_v03.py tests/schema/test_handoff_cleanup.py -q
py -3.13 -m pytest tests/schema -q
```

Expected: all pass.

- [x] **Step 6: Commit Task 3**

```powershell
git add tests/schema/validate_handoff.py tests/schema/test_handoff_v03.py tests/schema/fixtures skills/cadence-handoff/SKILL.md skills/cadence-resume/SKILL.md
git commit -m "feat: resume from verified canonical pointers"
```

### Task 4: Teach domain-neutral adaptive recording behavior

**Files:**
- Create: `skills/project-discuss/references/recording-fidelity.md`
- Modify: `skills/cadence-bootstrap/SKILL.md`
- Modify: `skills/project-discuss/SKILL.md`
- Modify: `skills/project-discuss/references/recording-protocol.md`
- Create: `tests/test_recording_fidelity_contract.py`

**Interfaces:**
- Consumes: the DecisionRecord and profile semantics from Task 1.
- Produces: a shared behavior contract injected by Claude Code and discoverable by OpenCode/Codex.

- [x] **Step 1: Write failing cross-domain contract tests**

Add a test that reads the skill files and asserts:

```python
def test_bootstrap_defines_acceptance_delta_and_fidelity_separately():
    assert "承接决定是否记录" in BOOTSTRAP
    assert "持久语义增量决定是否新建 entry" in BOOTSTRAP
    assert "影响等级决定记录多详细" in BOOTSTRAP


def test_reference_is_domain_neutral():
    for dimension in ["可逆性", "影响范围", "损失风险", "持续时间", "外部承诺", "不确定性"]:
        assert dimension in FIDELITY_REFERENCE
    for domain in ["研究", "写作", "学习", "运营"]:
        assert domain in FIDELITY_REFERENCE


def test_acceptance_shorthand_captures_the_preceding_proposal():
    assert "不是承接短句本身" in PROJECT_DISCUSS
```

- [x] **Step 2: Run the contract test and confirm RED**

Run:

```powershell
py -3.13 -m pytest tests/test_recording_fidelity_contract.py -q
```

Expected: missing reference and contract markers fail.

- [x] **Step 3: Add the focused recording-fidelity reference**

Write a concise reference containing:

- three-stage decision gate;
- universal impact dimensions;
- Light/Standard/High profiles;
- acceptance-shorthand extraction;
- provenance and sensitive-data rules;
- positive examples from software, research, writing, learning, and operations;
- common mistakes and a cold-start checklist.

- [x] **Step 4: Patch L0/L1/L2 without duplicating the reference**

- Bootstrap: keep only the three-stage core and a compact profile table.
- Project-discuss: require proposal backtracking, semantic delta extraction, automatic bounded repair, and conditional reading of the fidelity reference.
- Recording protocol: replace the universal minimum with baseline plus profile-aware fidelity and point to the focused reference.

- [x] **Step 5: Verify contract, hook injection, and all tests**

Run:

```powershell
py -3.13 -m pytest tests/test_recording_fidelity_contract.py tests/test_session_start_hook.py -q
py -3.13 -m pytest -q
```

Expected: all pass.

- [x] **Step 6: Commit Task 4**

```powershell
git add skills tests/test_recording_fidelity_contract.py
git commit -m "feat: record accepted decisions with adaptive fidelity"
```

### Review-driven extension: domain-neutral project discovery

Self-review found two domain locks outside the original recording path: `cadence-init` treated code
signatures as the only evidence of an existing project, and query reliability treated code as
universally authoritative. The extension:

- makes any meaningful project material count as an existing project;
- performs generic discovery before selecting optional software / research / writing / learning /
  operations adapters;
- ranks sources by question relevance, declared authority, directness, and freshness;
- keeps software-specific scan fields as backward-compatible optional fields;
- updates public plugin descriptions to state the domain-neutral contract.

Implemented and committed as `c54591e feat: generalize cadence project discovery`.

### Task 5: Final consistency and release-readiness verification

**Files:**
- Read: `.opencode/plugin/cadence.js`
- Read: `.codex-plugin/plugin.json`
- Read: `hooks/session-start`
- Create: `tests/test_runtime_loading_contract.py`
- Modify: `tests/test_session_start_hook.py`
- Modify: `docs/superpowers/plans/2026-07-18-recording-fidelity.md`

**Interfaces:**
- Consumes: all prior tasks.
- Produces: verified shared behavior across the plugin's supported harnesses.

- [x] **Step 1: Inspect runtime loading paths**

Verify that:

- Claude Code SessionStart injects the updated bootstrap body;
- OpenCode loads the same `skills/cadence-bootstrap/SKILL.md`;
- Codex discovers root skill paths from `.codex-plugin/plugin.json`;
- no generated marketplace copy needs a separate manual patch.

- [x] **Step 2: Add runtime regression assertions**

Write failing tests that prove all three harnesses reference the shared root skill and that the Claude
hook injects the three-stage recording marker. Do not create duplicate runtime implementations when
the shared source already supplies the behavior.

- [x] **Step 3: Run complete verification**

Run:

```powershell
py -3.13 -m pytest -q
git diff --check
git status --short
```

Expected: all tests pass, no whitespace errors, and only intentional files differ.

- [x] **Step 4: Re-read the design acceptance criteria**

Confirm every design criterion maps to code, skill text, validator behavior, or a test. Record any deliberate deferral in the final report rather than silently omitting it.

Acceptance mapping:

| Criterion | Evidence |
|---|---|
| Automatic adequate recording | shorthand backtracking + bounded repair in project-discuss; fidelity sweep in handoff |
| Light stays compact / High is recoverable | profile rules + validator warnings/errors + cross-domain fixtures |
| Same model outside software | research/writing/learning/operations fixtures and domain-neutral discovery contract |
| Every archived entry covered | v0.5 consolidator `source_entries` / `coverage` validator tests |
| Handoff remains 15–30 lines | handoff compact-body contract test; detail stays in `continuation_refs` |
| Resume passes cold-start six questions | canonical ref/hash verification + resume contract test |
| Both streaming schemas remain valid | legacy and YAML parser tests |
| Three runtimes use shared rules | Claude hook, OpenCode source path, Codex manifest contract tests |
| Secrets/raw logs/unaccepted exploration excluded | recording-fidelity sensitive-data and acceptance rules |

Deliberate compatibility choice: missing Light/Standard context remains a warning rather than a hard
error so historical entries continue to parse. High omissions and archive coverage gaps remain hard
errors.

- [x] **Step 5: Commit final consistency changes**

```powershell
git add .
git commit -m "test: verify recording fidelity across runtimes"
```

Skip the commit if Task 5 produces no tracked changes.
