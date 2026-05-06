#!/usr/bin/env bash
# scripts/sync-codex-marketplace.sh
#
# Sync cadence skills to a Codex plugin marketplace repo
# (target candidate: prime-radiant-inc/openai-codex-plugins).
#
# STATUS: STUB — currently documents only the EXCLUDES contract.
# Actual sync logic to be implemented in a future release.
#
# When activated, this script will:
#   1. Clone the target marketplace repo into a temp dir
#   2. Copy skills/ + .codex-plugin/ + relevant docs to <marketplace>/plugins/cadence/
#   3. Skip everything in EXCLUDES (CC-only / dev-only resources)
#   4. Commit + push (or open PR)

set -euo pipefail

# Files / directories that should NEVER be shipped to a Codex plugin marketplace.
# Modeled on superpowers/scripts/sync-to-codex-plugin.sh EXCLUDES contract.
EXCLUDES=(
  "/.git"
  "/.github"
  "/.claude-plugin"     # CC-only manifest
  "/.pytest_cache"
  "/.gitignore"
  "/.gitattributes"
  "/agents"             # if present at top-level — CC-format named subagent registry
  "/commands"           # CC slash commands; Codex uses \$skillname directly
  "/hooks"              # CC SessionStart hook; Codex has no equivalent event
  "/scripts"            # dev tooling (this script itself)
  "/tests"              # dev tooling
  "/cadence"            # this dev project's own cadence/ archive — not for end users
  "/docs"               # dev docs
  "/AGENTS.md"          # this dev project's own AGENTS.md — not for end users
  "/CLAUDE.md"          # CC-form (if present in future)
  "/RELEASE-NOTES.md"   # if present in future
)

echo "STUB: sync-codex-marketplace.sh — not yet implemented."
echo
echo "Planned EXCLUDES (will not be shipped to Codex plugin marketplace):"
for e in "${EXCLUDES[@]}"; do
  echo "  - $e"
done
exit 0
