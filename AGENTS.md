# cadence

This repository develops the **cadence** plugin — a domain-neutral, discussion-driven project workflow plugin that records / consolidates / retrieves AI session decisions into project archives.

The cadence plugin is itself developed using cadence conventions. See `skills/cadence-bootstrap/SKILL.md` for the active workflow contract (`记 / 整 / 查` 三阶段, `_INDEX.md` / `_ACTIVE.md` state contract, and the three-stage recording decision: acceptance / durable semantic delta / impact profile).

When working in this repo with any AI agent (Claude Code / Codex CLI / Cursor / etc.), the cadence-bootstrap protocol applies. CC harness reads it via SessionStart hook injection; Codex / other harnesses match it via skill description on session start.
