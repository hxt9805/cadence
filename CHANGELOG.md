# Changelog

All notable changes to cadence are documented here. This project adheres to [Semantic Versioning](https://semver.org/) starting from v0.2.0.

## [0.2.1] - 2026-05-14

### Fixed
- **handoff 路径文档不一致**(自 v0.1.0 起遗留):多处 SKILL.md / agents 文档对 `.handoff/` 位置字面描述不一致(`cadence/.handoff/` vs 裸 `.handoff/`),导致不同 Claude 实例可能将 handoff 文件写到项目根而非 `cadence/.handoff/`。统一所有路径引用为 `cadence/.handoff/` + 在 `cadence-handoff` / `cadence-resume` 顶部加路径约定声明 + `cadence-resume` Step 1 加前置检测护栏(发现项目根 `.handoff/` 提示迁移)。
- **迁移**:若你的项目里 `.handoff/` 在项目根 → 一行 `mv .handoff cadence/.handoff`(参 `cadence-resume` Step 1 前置检测的提示)。沿用现有"不强迁老 handoff"策略,不提供一键脚本。

## [0.2.0] - 2026-05-08

首个正式发布版本(带 git tag 和 GitHub Release)。

### Added
- SessionStart hook gates bootstrap injection on `cadence/_INDEX.md` presence
- Codex CLI / App / IDE compatibility layer with full install docs

### Fixed
- Hook line endings pinned for cross-platform consistency (CRLF/LF)
- `cadence-handoff` validator bundled into plugin (write-time check works)
- README troubleshooting for SSH auth failures on plugin install

### Changed
- Marketplace renamed from `cadence-dev` to `cadence` (install command becomes `/plugin install cadence@cadence`)
- README repositions Claude Code as primary harness, Codex as compatibility layer
- `.claude-plugin/marketplace.json` `source` now uses object form with `ref: "v0.2.0"` (pins to git tag)

### Known Issues
- **Codex marketplace mode is blocked by [Codex issue #17066](https://github.com/openai/codex/issues/17066)** — Codex 0.129's plugin path resolver rejects marketplaces whose plugin sits at the repo root (cadence's layout). CLI `marketplace add` succeeds but plugin is never loaded into session. **Workaround**: use Symlink mode (see [`.codex/INSTALL.md`](.codex/INSTALL.md) and the Codex section in README). Once OpenAI lands a fix, marketplace mode will become recommended again.
- **CC marketplace rename is not auto-migrated** — CC binds the git URL to the old `cadence-dev` marketplace name in `known_marketplaces.json`. Users who installed v0.1.x must clear that entry manually before the new `cadence` marketplace can register. See "从早期版本迁移" in README.

### Note
v0.1.0 was a pre-tag stage release (no git tag, no formal release notes). Starting from v0.2.0, cadence enforces strict SemVer with immutable tags and proper release notes.
