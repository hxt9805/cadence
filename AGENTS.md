# cadence

This repository develops the **cadence** plugin — a discussion-driven software development workflow plugin that records / consolidates / retrieves Claude Code & Codex CLI session discussions to project archives.

The cadence plugin is itself developed using cadence conventions. See `skills/cadence-bootstrap/SKILL.md` for the active workflow contract (`记 / 整 / 查` 三阶段, `_INDEX.md` / `_ACTIVE.md` state contract, recording criterion 单判据「已被承接」).

When working in this repo with any AI agent (Claude Code / Codex CLI / Cursor / etc.), the cadence-bootstrap protocol applies. CC harness reads it via SessionStart hook injection; Codex / other harnesses match it via skill description on session start.
