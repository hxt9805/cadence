# Changelog

All notable changes to cadence are documented here. This project adheres to [Semantic Versioning](https://semver.org/) starting from v0.2.0.

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

### Note
v0.1.0 was a pre-tag stage release (no git tag, no formal release notes). Starting from v0.2.0, cadence enforces strict SemVer with immutable tags and proper release notes.
