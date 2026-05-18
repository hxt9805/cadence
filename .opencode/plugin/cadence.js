/**
 * Cadence plugin for OpenCode.ai
 *
 * Responsibilities:
 *   1. Register cadence skills/ directory via config.skills.paths
 *      (so OpenCode discovers /cadence-init, /cadence-handoff, /cadence-resume,
 *       /cadence-bootstrap, /project-discuss as native slash commands)
 *   2. Register 3 named subagents (recall-retriever / recall-consolidator /
 *      recall-analyzer) via config.agent[], with system prompts loaded from
 *      skills/project-discuss/agents/*.md — enables Task tool fork with context
 *      isolation, matching CC's named-subagent behavior 1:1
 *   3. Inject cadence-bootstrap content into the first user message when the
 *      current project is cadence-managed (cadence/_INDEX.md exists), mirroring
 *      CC's SessionStart hook behavior
 *
 * Design notes:
 *   - Bootstrap goes into the first user message (not system) — avoids the
 *     token bloat and multi-system-message issues superpowers documented.
 *   - The bootstrap content is cached after first read (SKILL.md does not
 *     change mid-session). The `directory` value is captured at plugin init
 *     (OpenCode re-inits the plugin when the user switches projects), but
 *     the `cadence/_INDEX.md` filesystem check runs per hook call — so if
 *     the user runs /cadence-init mid-session, subsequent agent steps will
 *     start injecting bootstrap once the index file appears.
 */

import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PLUGIN_ROOT = path.resolve(__dirname, '../..');
const SKILLS_DIR = path.join(PLUGIN_ROOT, 'skills');
const AGENTS_DIR = path.join(SKILLS_DIR, 'project-discuss', 'agents');

// --- Frontmatter parser (handles `description: >` folded scalars) ---

const extractAndStripFrontmatter = (content) => {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n([\s\S]*)$/);
  if (!match) return { frontmatter: {}, content };

  const lines = match[1].split(/\r?\n/);
  const body = match[2];
  const frontmatter = {};
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const colonIdx = line.indexOf(':');
    if (colonIdx <= 0) { i++; continue; }

    const key = line.slice(0, colonIdx).trim();
    let value = line.slice(colonIdx + 1).trim();

    if (value === '>' || value === '|') {
      const folded = [];
      const fold = value === '>';
      i++;
      while (i < lines.length && /^\s+\S/.test(lines[i])) {
        folded.push(lines[i].trim());
        i++;
      }
      value = folded.join(fold ? ' ' : '\n');
    } else {
      value = value.replace(/^["']|["']$/g, '');
      i++;
    }

    frontmatter[key] = value;
  }

  return { frontmatter, content: body };
};

// --- Bootstrap content (cached) ---

let _bootstrapCache = undefined;

const getBootstrapContent = () => {
  if (_bootstrapCache !== undefined) return _bootstrapCache;

  const skillPath = path.join(SKILLS_DIR, 'cadence-bootstrap', 'SKILL.md');
  if (!fs.existsSync(skillPath)) {
    _bootstrapCache = null;
    return null;
  }

  const fullContent = fs.readFileSync(skillPath, 'utf8');
  const { content } = extractAndStripFrontmatter(fullContent);

  const toolMapping = `**OpenCode 形态工具映射** — cadence skill 内文本若引用以下 CC 概念，按右侧 OpenCode 等价物理解：
- \`TodoWrite\` → \`todowrite\`
- \`Task\` tool fork named subagent → OpenCode \`Task\` tool，参数 \`subagent_type\` 填 "recall-retriever" / "recall-consolidator" / "recall-analyzer"（本插件已在 OpenCode 注册这 3 个 named subagent，\`prompt\` 参数传具体任务输入；agent body 已由插件预加载，无需手动读 \`agents/*.md\` 再传入）
- \`Skill\` tool → OpenCode 原生 \`skill\` tool；或直接用 \`/<skill-name>\` 触发（OpenCode 自动把 \`skills/<name>/SKILL.md\` 暴露为同名 slash command）
- \`Read\` / \`Write\` / \`Edit\` / \`Bash\` → OpenCode 原生同名工具
- \`\${CLAUDE_PLUGIN_ROOT}\` → 该变量在 OpenCode 上不展开；遇到该路径前缀时理解为「当前 plugin / skill root 的相对路径」并自行 resolve（与 Codex 形态相同的策略，详见 \`skills/project-discuss/references/codex-tools.md\` § 4）

**Slash command**：\`/cadence-init\` / \`/cadence-handoff\` / \`/cadence-resume\` 在 OpenCode 上由 skill name 自动生成，行为等价于 CC。`;

  _bootstrapCache = `<EXTREMELY_IMPORTANT>
You are in a cadence-managed project.

**The cadence-bootstrap skill content is included below. It is ALREADY LOADED — you are currently following it. Do NOT call the skill tool to load "cadence-bootstrap" again.**

${content}

---

${toolMapping}
</EXTREMELY_IMPORTANT>`;

  return _bootstrapCache;
};

// --- Subagent loader ---

const SUBAGENT_NAMES = ['recall-retriever', 'recall-consolidator', 'recall-analyzer'];

const loadSubagent = (name) => {
  const agentPath = path.join(AGENTS_DIR, `${name}.md`);
  if (!fs.existsSync(agentPath)) return null;

  const fullContent = fs.readFileSync(agentPath, 'utf8');
  const { frontmatter, content } = extractAndStripFrontmatter(fullContent);

  return {
    description: frontmatter.description || `cadence ${name} subagent`,
    mode: 'subagent',
    prompt: content,
  };
};

// --- Plugin entry ---

export const CadencePlugin = async ({ directory }) => {
  const isCadenceProject = () => {
    try {
      return fs.existsSync(path.join(directory, 'cadence', '_INDEX.md'));
    } catch {
      return false;
    }
  };

  return {
    config: async (config) => {
      // 1. Register cadence skills/ for OpenCode skill discovery
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(SKILLS_DIR)) {
        config.skills.paths.push(SKILLS_DIR);
      }

      // 2. Register 3 named subagents (skip if user has overridden any of them)
      config.agent = config.agent || {};
      for (const name of SUBAGENT_NAMES) {
        if (config.agent[name]) continue;
        const def = loadSubagent(name);
        if (def) config.agent[name] = def;
      }
    },

    'experimental.chat.messages.transform': async (_input, output) => {
      if (!isCadenceProject()) return;

      const bootstrap = getBootstrapContent();
      if (!bootstrap || !output.messages.length) return;

      const firstUser = output.messages.find(m => m.info.role === 'user');
      if (!firstUser || !firstUser.parts.length) return;

      // Guard against double injection (hook fires on every agent step)
      if (firstUser.parts.some(p => p.type === 'text' && p.text.includes('cadence-bootstrap skill content is included below'))) return;

      const ref = firstUser.parts[0];
      firstUser.parts.unshift({ ...ref, type: 'text', text: bootstrap });
    },
  };
};

export default CadencePlugin;
