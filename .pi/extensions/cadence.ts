/**
 * Cadence Pi extension (OMP / Pi-compatible harnesses)
 *
 * Mirrors CC's SessionStart hook and OpenCode's plugin injection: when the
 * current project is cadence-managed (cadence/_INDEX.md exists), inject the
 * cadence-bootstrap skill body into the first user message of each agent
 * turn, so the LLM follows the 记/整/查 protocol and activates
 * project-discuss without relying on progressive disclosure.
 *
 * Design (same as superpowers/.pi/extensions/superpowers.ts + cadence's own
 * .opencode/plugin/cadence.js):
 *   - Bootstrap goes into a user message (not system) — avoids token bloat.
 *   - Re-injected after session_start / session_compact; suppressed after the
 *     first agent_end so it is not repeated on every tool round-trip.
 *   - Guarded against double injection via BOOTSTRAP_MARKER.
 *   - Project check (cadence/_INDEX.md) runs per context event so switching
 *     projects mid-session is honoured (Pi has no plugin-init `directory`
 *     param like OpenCode, so process.cwd() is the project root source).
 */
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const EXTREMELY_IMPORTANT_MARKER = "<EXTREMELY_IMPORTANT>";
const BOOTSTRAP_MARKER = "cadence:cadence-bootstrap bootstrap for pi";

const extensionDir = dirname(fileURLToPath(import.meta.url));
const packageRoot = resolve(extensionDir, "../..");
const skillsDir = resolve(packageRoot, "skills");
const bootstrapSkillPath = resolve(skillsDir, "cadence-bootstrap", "SKILL.md");

let cachedBootstrap: string | null | undefined;

export default function cadencePiExtension(pi: ExtensionAPI) {
  let injectBootstrap = true;

  pi.on("resources_discover", async () => ({
    skillPaths: [skillsDir],
  }));

  pi.on("session_start", async () => {
    injectBootstrap = true;
  });

  pi.on("session_compact", async () => {
    injectBootstrap = true;
  });

  pi.on("agent_end", async () => {
    injectBootstrap = false;
  });

  pi.on("context", async (event) => {
    if (!injectBootstrap) return;
    // cadence-managed project gate: only inject when the cwd has a cadence
    // skeleton (process.cwd() is the Pi project root; existsSync may throw on
    // unreachable paths, so guard it).
    let cadenceManaged = false;
    try {
      cadenceManaged = existsSync(join(process.cwd(), "cadence", "_INDEX.md"));
    } catch {
      cadenceManaged = false;
    }
    if (!cadenceManaged) return;

    if (event.messages.some(messageContainsBootstrap)) return;

    const bootstrap = getBootstrapContent();
    if (!bootstrap) return;

    const bootstrapMessage = {
      role: "user" as const,
      content: [{ type: "text" as const, text: bootstrap }],
      timestamp: Date.now(),
    };

    const insertAt = firstNonCompactionSummaryIndex(event.messages);
    return {
      messages: [
        ...event.messages.slice(0, insertAt),
        bootstrapMessage,
        ...event.messages.slice(insertAt),
      ],
    };
  });
}

function getBootstrapContent(): string | null {
  if (cachedBootstrap !== undefined) return cachedBootstrap;

  try {
    if (!existsSync(bootstrapSkillPath)) {
      cachedBootstrap = null;
      return null;
    }
    const skillContent = readFileSync(bootstrapSkillPath, "utf8");
    const body = stripFrontmatter(skillContent);
    cachedBootstrap = `${EXTREMELY_IMPORTANT_MARKER}
${BOOTSTRAP_MARKER}

You are in a cadence-managed project.

The cadence-bootstrap skill content is included below and is already loaded for this Pi session. You are currently following it. Do not try to load cadence-bootstrap again — it is already in context.

${body}

---

${piToolMapping()}
</EXTREMELY_IMPORTANT>`;
    return cachedBootstrap;
  } catch {
    cachedBootstrap = null;
    return null;
  }
}

function stripFrontmatter(content: string): string {
  const match = content.match(/^---\r?\n[\s\S]*?\r?\n---\r?\n([\s\S]*)$/);
  return (match ? match[1] : content).trim();
}

function piToolMapping(): string {
  return `## Pi tool mapping

Pi has native skills but does not expose Claude Code's \`Skill\` tool. When a cadence instruction says to invoke a skill (e.g. \`Skill("project-discuss")\`), use Pi's native skill system instead: load the relevant \`SKILL.md\` via \`read\` (e.g. \`read skill://project-discuss\`), or let a human invoke \`/skill:name\` explicitly.

Pi's built-in coding tools are lowercase: \`read\`, \`write\`, \`edit\`, \`bash\`, plus optional \`grep\`, \`find\`, and \`ls\`. Use those for the corresponding actions.

Pi does not ship a standard subagent tool. cadence defines 3 named subagents (recall-retriever / recall-consolidator / recall-analyzer). If a subagent tool such as \`subagent\` from \`pi-subagents\` is available, dispatch them through it; otherwise perform recall/consolidation work in the main session (the cadence protocol degrades gracefully — the main session is the sole writer regardless of harness).

Pi does not ship a standard task-list tool. If an installed todo/task tool is available, use it. Otherwise track cadence TODOs in \`cadence/_ACTIVE.md\` directly.

\`\${CLAUDE_PLUGIN_ROOT}\` does not expand on Pi. When a cadence document references it, treat it as a relative path from the cadence plugin/skill root and resolve accordingly (same strategy as Codex, see \`skills/project-discuss/references/harness-adapters.md\`).

Slash commands \`/cadence-init\`, \`/cadence-handoff\`, \`/cadence-resume\` map to Pi native skills of the same name.`;
}

// --- Message-shape guards (narrow unknown pi event payloads safely) ---

function messageContainsBootstrap(message: unknown): boolean {
  if (typeof message !== "object" || message === null || !("content" in message)) {
    return false;
  }
  const content = message.content;
  if (typeof content === "string") return content.includes(BOOTSTRAP_MARKER);
  if (!Array.isArray(content)) return false;
  return content.some((part) => textOf(part)?.includes(BOOTSTRAP_MARKER) === true);
}

function textOf(part: unknown): string | undefined {
  if (
    typeof part !== "object" ||
    part === null ||
    !("type" in part) ||
    !("text" in part)
  ) {
    return undefined;
  }
  return part.type === "text" && typeof part.text === "string" ? part.text : undefined;
}

function firstNonCompactionSummaryIndex(messages: unknown[]): number {
  let index = 0;
  while (index < messages.length) {
    const msg = messages[index];
    if (
      typeof msg !== "object" ||
      msg === null ||
      !("role" in msg) ||
      msg.role !== "compactionSummary"
    ) {
      break;
    }
    index += 1;
  }
  return index;
}
