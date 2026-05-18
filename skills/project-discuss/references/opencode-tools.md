# OpenCode 形态下的工具映射

> 本文档**仅在 OpenCode 形态下相关**。
> CC 形态请直接使用 Task tool / SessionStart hook / `${CLAUDE_PLUGIN_ROOT}` 等机制，无需读本文档。
> Codex 形态另见 [`codex-tools.md`](codex-tools.md)。

## 为什么有这份文档

cadence 最初为 Claude Code 设计，依赖 4 类 CC harness 能力：SessionStart hook、Task tool 自主 fork named subagent、`${CLAUDE_PLUGIN_ROOT}` 路径变量、`/slashcommand`。OpenCode 通过 `.opencode/plugin/cadence.js` 提供 first-class 等价支持——本文档列出**当主 session 在 OpenCode 形态下运行时**应使用的等价机制，以及与 CC 行为的少数差异。

> **简短版**：OpenCode 上 cadence 跟 CC 体验几乎 1:1 对齐，只在路径变量解析（§ 4）和 bootstrap 注入位置（§ 1）上有实现细节差异，LLM 调度行为完全一致。

## 1. SessionStart 注入 → OpenCode plugin message transform

**CC 行为**：`hooks/session-start` 脚本通过 `additionalContext` JSON 把 `cadence-bootstrap` SKILL.md body 注入 LLM 上下文。

**OpenCode 等价物**：`.opencode/plugin/cadence.js` 使用 OpenCode 的 `experimental.chat.messages.transform` hook，把 cadence-bootstrap 内容注入到**第一条 user message 的 parts[0]**（不进 system message，避开多 system 兼容性问题）。注入条件与 CC 相同：项目根存在 `cadence/_INDEX.md` 才注入。

**含义**：行为对 LLM 透明；主 session 启动后即可直接进入 cadence 协议，**不需要 LLM 主动调 skill tool 加载 bootstrap**。bootstrap 末尾会附一段 OpenCode 形态的工具映射提示（即本文档要点的精简版），LLM 直接读到。

## 2. Subagent 自主 fork → OpenCode Task tool（与 CC 几乎一致）

**CC 行为**：主 session 用 Task tool fork named subagent（`recall-retriever` / `recall-consolidator` / `recall-analyzer`）；CC 自动加载对应 `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/agents/<name>.md` 作为 subagent context。

**OpenCode 等价物**：**直接照搬**——OpenCode 的 Task tool 接受相同参数 `subagent_type` + `prompt` + `description`。3 个 cadence subagent 由 plugin 在启动时通过 `config` hook 注册到 `cfg.agent[]`，agent 的 system prompt（agents/*.md body）已由 plugin 预加载，**LLM 调用时只传 task input，不需要手动读 agents/*.md 再传**。

```
Task tool:
  subagent_type: "recall-retriever"   # 或 recall-consolidator / recall-analyzer
  prompt: "<具体任务输入>"             # 不需要把 agent body 塞进来
  description: "<3-5 字短描述>"
```

OpenCode 通过 `sessions.create({ parentID })` 创建独立子 session，**context 隔离与 CC 等价**：subagent 在独立 message history 里跑、独立 LLM context、独立 permission ruleset，完成后输出 consolidated 返回主 session。

### 三个 recall-* subagent 在 OpenCode 形态下的调用

| Subagent | 调用方式 | 与 CC 差异 |
|---|---|---|
| `recall-retriever` | `Task(subagent_type="recall-retriever", ...)` | 无 |
| `recall-consolidator` | `Task(subagent_type="recall-consolidator", ...)` | 无 |
| `recall-analyzer` | `Task(subagent_type="recall-analyzer", ...)` | 无 |

> **filesystem 共享 + conversation 隔离**：与 CC 一致；subagent 跟 parent session 共享 filesystem，但 conversation context 隔离 + 输出 consolidated → cadence「主 session context 不膨胀」契约成立。

## 3. Slash command → OpenCode 自动从 skill name 生成

**CC 行为**：`commands/cadence-init.md`（带 frontmatter `description`）让用户敲 `/cadence-init` 触发对应 skill。

**OpenCode 等价物**：**零额外配置**——OpenCode 扫描 `skills/<name>/SKILL.md` 后自动把每个 skill 暴露为 `/<skill-name>` slash command。`.opencode/plugin/cadence.js` 通过 `config.skills.paths.push(...)` 注册 cadence 的 skills 目录，所有 5 个 skill 自动出现在 `/` 命令列表里：

| CC slash | OpenCode 触发 |
|---|---|
| `/cadence-init` | `/cadence-init`（同名） |
| `/cadence-handoff` | `/cadence-handoff`（同名） |
| `/cadence-resume` | `/cadence-resume`（同名） |
| `/cadence-bootstrap` | `/cadence-bootstrap`（同名；一般不需手动触发） |
| —（CC 无显式 slash） | `/project-discuss` |

差异：OpenCode 上 `commands/` 目录里的 .md routing layer **不被使用**（OpenCode 直接加载 SKILL.md），但保留这些文件不影响 OpenCode 行为——它们只对 CC 生效。

## 4. `${CLAUDE_PLUGIN_ROOT}` → 相对路径 + skill root 推断

**CC 行为**：plugin 内文件用 `${CLAUDE_PLUGIN_ROOT}/skills/.../SKILL.md` 引用，CC 在 hook/command 执行时注入此变量。

**OpenCode 等价物**：与 Codex 形态相同的策略——**无环境变量展开**。OpenCode 通过 `git+https://` 安装时 plugin 实际路径在 `~/.config/opencode/node_modules/cadence/`（或类似），skills 通过 `config.skills.paths` 暴露给 skill discovery。

主 session 在 OpenCode 形态下读 SKILL.md 看到 `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/agents/...` 时，应理解为「当前 skill root 下的相对路径 `agents/...`」——LLM 自行解析。**Python 脚本调用同理**（`python ${CLAUDE_PLUGIN_ROOT}/skills/cadence-handoff/scripts/validate_handoff.py` 应解析为相对当前 skill root 的实际路径）。

## 5. context 预算约束

| Harness | 默认 context 上限 |
|---|---|
| Claude Code (Opus 4.7) | **1M** |
| OpenCode | 取决于底层 LLM 与用户配置（GLM-5.1 / GPT-5.x / Claude 4.x 等），通常 200K–1M 区间 |
| Codex CLI (GPT-5.5 默认) | 400K（可被 catalog clamp 到 272K） |

**含义**：OpenCode 上 subagent 隔离仍然是 cadence 的核心契约（与 CC 一致），但**触发紧迫度低于 Codex**——`recall-retriever` 的 <500 tokens 硬限、`recall-consolidator` 的 plan ≤200 行硬限继续遵守即可，无需像 Codex 形态那样设「调度铁律」强制 spawn。

## 6. cadence 三个 phase 在 OpenCode 形态下的对应

| cadence Phase | CC 实现 | OpenCode 实现 |
|---|---|---|
| **Phase 1 记**（α 流式）| 主 session 直写 streaming entry | 同 CC（无 subagent 涉及） |
| **Phase 2 整**（ε 整合）| Task tool fork `recall-consolidator` → 接收 yaml plan → 主 session Write/Validate/Archive | 同 CC（Task tool 调用语法一致） |
| **Phase 3 查**（ρ 检索）| Task tool fork `recall-retriever` → 接收 summary+pointers | 同 CC（Task tool 调用语法一致） |

**三个 phase 在 OpenCode 形态下与 CC 完全一致**——`.opencode/plugin/cadence.js` 已经把 named subagent 注册到 OpenCode runtime，LLM 端调度逻辑无需任何分支。

---

## 调试 tips

- 若 OpenCode 报 `Unknown agent type: recall-retriever`：plugin `config` hook 没生效。检查：
  1. `opencode.json` 的 `plugin` 数组是否含 `cadence@git+https://...`
  2. `opencode run --print-logs "hello" 2>&1 | grep -i cadence` 看 plugin 加载日志
  3. 仓库 clone 是否完整（特别是 `.opencode/plugin/cadence.js` 和 `skills/project-discuss/agents/*.md`）
- 若 subagent 跑起来但行为不对（如 retriever 写文件 / 超 500 tokens）：检查 `skills/project-discuss/agents/<name>.md` 内容是否被正确加载——让 subagent 自我介绍其硬边界、输入输出 schema，对照 .md 原文核验。
- 若 `/cadence-*` 命令在 `/` 列表里看不到：确认 plugin `config.skills.paths` 注入成功——OpenCode 启动日志会列出扫描的 skill 目录。
- 若 bootstrap 没自动注入（主 session 不知道 cadence 协议）：确认项目根有 `cadence/_INDEX.md`（gating 条件）；未 init 项目需要先跑 `/cadence-init`。
