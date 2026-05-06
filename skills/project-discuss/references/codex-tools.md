# Codex CLI 形态下的工具映射

> 本文档**仅在 Codex CLI 形态下相关**。
> CC 形态请直接使用 Task tool / SessionStart hook / `${CLAUDE_PLUGIN_ROOT}` 等机制，无需读本文档。

## 为什么有这份文档

cadence 最初为 Claude Code 设计，依赖 4 类 CC harness 能力：SessionStart hook、Task tool 自主 fork named subagent、`${CLAUDE_PLUGIN_ROOT}` 路径变量、`/slashcommand`。Codex CLI（2026-03 起的 plugin 体系）的 paradigm 不同——本文档列出**当主 session 在 Codex 形态下运行时**应使用的等价机制。

## 1. SessionStart 注入 → Codex 原生 skill discovery

**CC 行为**：`hooks/session-start` 脚本通过 `additionalContext` JSON 把 `cadence-bootstrap` SKILL.md body 注入 LLM 上下文。

**Codex 等价物**：无 SessionStart hook（Codex 只有 lifecycle `onInstall`/`onUpdate` 钩子）。改用 Codex 的**原生 skill 发现机制**——LLM 在每个 session 启动时看到所有已注册 skill 的 frontmatter（`name` + `description`），由 `cadence-bootstrap` 的 description 字段（强触发词 "Use when starting any conversation in a cadence-managed project..."）触发 LLM 主动调用 skill 取全文。

**含义**：Codex 形态下 description 字段是**触发词的载体**，不是纯描述。

## 2. Subagent 自主 fork → Codex `spawn_agent` 5 件套

**CC 行为**：主 session 用 Task tool 直接 fork named subagent（`recall-retriever` / `recall-consolidator` / `recall-analyzer`）；CC 自动加载对应 `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/agents/<name>.md` 的 frontmatter + body 作为 subagent context。

**Codex 等价物**：Codex 没有 named agent registry——只有 `default` / `worker` / `explorer` 三个内置 role；自定义 `~/.codex/agents/<name>.toml` 路线在 plugin 形态下不被 sync（参见 `superpowers/scripts/sync-to-codex-plugin.sh:74` 把 `/agents/` 加入 EXCLUDES 的实证）。改用以下流程：

### Codex 形态下 fork recall-* subagent 的步骤

```
主 session：
  1. Read ${PLUGIN_ROOT}/skills/project-discuss/agents/recall-retriever.md
     → 提取 frontmatter 下方的 body（即 subagent 的指令体）
  2. 用 spawn_agent 工具:
       spawn_agent(
         agent: "explorer",   # 只读型用 explorer，写型/分析型用 worker
         message: <XML wrapped prompt>
       )
  3. 用 wait_agent 工具等待结果
  4. 接收 consolidated output（已结构化精简，非全文转录）
  5. close_agent 关闭
```

> **PLUGIN_ROOT 解析**：Codex 没有 `${CLAUDE_PLUGIN_ROOT}` 等价物。symlink 安装下，cadence 的实际路径是 `~/.codex/cadence/`，通过 `~/.agents/skills/cadence/` 暴露给 Codex skill discovery。主 session 在 Codex 形态下应按"当前 skill root 的相对路径"理解 SKILL.md 中的 `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/...` 引用——即 `agents/recall-retriever.md` 在该 skill root 下。

### XML message wrapping 模板

```xml
<agent-instructions>
[recall-retriever.md 的 body 原文（去掉 frontmatter）]
</agent-instructions>

<task-input>
user_query: <用户原话或主 session 提炼的 query>
current_session_context: <轻量；≤2k tokens；session 内已讨论主题 / 最近 N 轮摘要>
</task-input>

<output-contract>
请按照 recall-retriever.md 中「输出 schema(硬性 <500 tokens)」段定义的 yaml 格式返回。
返回 summary + pointers 两段，总 token 数硬性 <500。
</output-contract>
```

### 三个 recall-* subagent 在 Codex 形态下的 agent 选型

| Subagent | Codex agent role | 理由 |
|---|---|---|
| `recall-retriever` | `explorer` | 只读、read-heavy、结构化输出符合 explorer 设计 |
| `recall-consolidator` | `worker` | Plan-only 但需扫多个 streaming/discussion 文件 + 综合 reasoning |
| `recall-analyzer` | `worker` | Plan-only，多档案 + 冲突分析重任务 |

> **filesystem 共享**：spawn_agent 派出的 subagent 跟 parent thread **共享 filesystem**（实证来源：`superpowers/docs/superpowers/specs/2026-03-23-codex-app-compatibility-design.md:27`），但 conversation context 隔离 + 输出 consolidated → cadence 的「**主 session context 不膨胀**」契约在 Codex 上成立且**比 CC 更必要**。

### 触发强度

Codex 默认 session policy 偏保守（官方 features 页："Codex only spawns subagents when you explicitly ask it to"）。SKILL.md 文本里调用 subagent 的描述应使用**强祈使句**（"Dispatch retriever subagent" 而非 "consider forking a retriever"），让模型把 spawn 当成 task 必经步骤而非可选。

## 3. Slash command → Codex `$skillname` 直接调用

**CC 行为**：`commands/cadence-init.md`（带 frontmatter `description`）让用户敲 `/cadence-init` 触发对应 skill。

**Codex 等价物**：Codex 用户敲 `$cadence:cadence-init` 直接触发 skill（**plugin 命名空间冒号分隔**；UI 标签则显示为 `Cadence: Cadence Init`）。

| CC slash | Codex 触发（plugin 命名空间形式） |
|---|---|
| `/cadence-init` | `$cadence:cadence-init` |
| `/cadence-handoff` | `$cadence:cadence-handoff` |
| `/cadence-resume` | `$cadence:cadence-resume` |

主 session 在 Codex 形态下不应假设 commands/ 文件存在；应直接调 skill（用户输入是 `$plugin:skill` 形式，主 session 内部引用 skill 时按 skill name `cadence-init` 即可）。

## 4. `${CLAUDE_PLUGIN_ROOT}` → 相对路径 + skill root 推断

**CC 行为**：plugin 内文件用 `${CLAUDE_PLUGIN_ROOT}/skills/.../SKILL.md` 引用，CC 在 hook/command 执行时注入此变量。

**Codex 等价物**：无等价环境变量。Symlink 安装下 skills 实际路径是 `~/.codex/cadence/skills/...`，通过 `~/.agents/skills/cadence/...` symlink 暴露。

主 session 在 Codex 形态下读 SKILL.md 看到 `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/agents/...` 时，应理解为"当前 skill root 下的相对路径 `agents/...`"——LLM 自行解析。

## 5. context 预算约束

| Harness | 默认 context 上限 |
|---|---|
| Claude Code (Opus 4.7) | **1M** |
| Codex CLI (GPT-5.5 默认) | 400K（可被 catalog clamp 到 272K） |
| Codex Desktop | 258K |

**含义**：subagent 隔离在 Codex 形态下**比 CC 更必要**。`recall-retriever` 的 <500 tokens 硬限、`recall-consolidator` 的 plan ≤200 行硬限，在 Codex 形态下都是关键 budget 守门员，**不可放松**。

## 6. cadence 三个 phase 在 Codex 形态下的对应

| cadence Phase | CC 实现 | Codex 实现 |
|---|---|---|
| **Phase 1 记**（α 流式）| 主 session 直写 streaming entry | 同 CC（无 subagent 涉及） |
| **Phase 2 整**（ε 整合）| Task tool fork `recall-consolidator` → 接收 yaml plan → 主 session Write/Validate/Archive | 按 § 2 流程 spawn_agent(worker) → wait_agent → 主 session 三步写 |
| **Phase 3 查**（ρ 检索）| Task tool fork `recall-retriever` → 接收 summary+pointers | 按 § 2 流程 spawn_agent(explorer) → wait_agent → 主 session 呈现 |

**Phase 1 不变**（与 harness 无关）；Phase 2/3 仅 fork 机制不同，**输出契约（plan-only / 只读 / token 硬限）完全一致**。

---

## 调试 tips

- 若 LLM 不主动 spawn subagent，检查：
  1. `~/.codex/config.toml` 是否设 `[features].multi_agent = true`
  2. SKILL.md 里 spawn 指令是否用强祈使句（参见 cadence-bootstrap 「Codex 形态调度铁律」段）
  3. 当前模型是否支持 multi-agent（GPT-5.5 / GPT-5.4 都支持）
- 若 spawn 后 subagent 输出超 500 tokens，检查 message 里 `<output-contract>` 段是否清晰传达硬限
- **Codex App sandbox 默认拒 `rg`（ripgrep）** — 主 session 调用 rg 会被拒绝。这不是 retriever 走捷径用 `Select-String` 的借口；正确做法是 `spawn_agent(explorer)` 让 explorer agent 用其内置 search 能力（不依赖主 session 的 sandbox policy）。若观察到 LLM 自报"刚刚没有 spawn subagent，我只是本地读了几个 cadence 文档和用 PowerShell 搜了一下"，是 cadence-bootstrap 「Codex 形态调度铁律」段未被加载或被忽略，需要让 LLM 自检 skill body
- 若 Codex 报"agent role not found"，检查 agent 名拼写（必须是 `default` / `worker` / `explorer` 之一）
