# Installing cadence for Codex CLI

Enable cadence's discussion-driven workflow skills in OpenAI Codex CLI via native skill discovery.

> Codex CLI **v0.117.0+** required (March 2026 plugin system release).

## Installation

### 1. Clone the cadence repository

```bash
git clone https://github.com/hxt9805/cadence.git ~/.codex/cadence
```

> Symlink mode is the developer / fallback installation path. For end users, prefer marketplace mode (see [`README.md`](../README.md#codex-cli--app--ide)).

### 2. Create the skills symlink

**macOS / Linux:**

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/cadence/skills ~/.agents/skills/cadence
```

**Windows (PowerShell as Administrator):**

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.agents\skills" | Out-Null
New-Item -ItemType SymbolicLink -Path "$HOME\.agents\skills\cadence" -Target "$HOME\.codex\cadence\skills"
```

> Windows non-admin: with **Developer Mode** enabled, `mklink /D %USERPROFILE%\.agents\skills\cadence %USERPROFILE%\.codex\cadence\skills` from `cmd.exe` works without admin.

### 3. Enable multi-agent (recommended)

cadence's "暗仓库" UX relies on subagent dispatch (recall-consolidator / recall-retriever / recall-analyzer). Codex CLI documents `multi_agent = true` as default, but double-check `~/.codex/config.toml`:

```toml
[features]
multi_agent = true
```

### 4. Restart Codex CLI

Quit and relaunch the CLI. Codex will discover the cadence skills under `~/.agents/skills/cadence/`.

## Verification

Run the 4 acceptance tests in [`RUNBOOK.md`](./RUNBOOK.md). All four should pass to verify the installation.

## Uninstall

```bash
rm ~/.agents/skills/cadence
rm -rf ~/.codex/cadence
```

(On Windows, `Remove-Item -Recurse` or Explorer.)

## Status

**Marketplace mode available (since 2026-05-06).**

- ✅ `.codex-plugin/plugin.json` written — Codex plugin manifest with `skills` pointer + `interface` block
- ✅ `.agents/plugins/marketplace.json` written — repo-scoped marketplace entry (`cadence`)
- ⏸ `scripts/sync-codex-marketplace.sh` still stub — only needed for syncing to external curated marketplace (e.g. `prime-radiant-inc/openai-codex-plugins`); local marketplace mode does not need it

The symlink steps in this file remain valid as a **fallback / developer mode** for users who want to skip marketplace registration. For end-user installation, prefer the marketplace mode in [`README.md`](../README.md#codex-cli--app--ide).
