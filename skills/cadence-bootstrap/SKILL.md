---
name: cadence-bootstrap
description: Use when starting any conversation in a cadence-managed project (project root contains cadence/_INDEX.md or cadence/_ACTIVE.md). Establishes cadence workflow conventions — 记 / 整 / 查 三阶段记录协议, _ACTIVE.md / _INDEX.md state contract, recording criterion 单判据「已被承接」, session start behaviors, and subagent dispatch rules. CC harness reads this skill via SessionStart hook injection (automatic). Codex / other harnesses match this description on session start (progressive disclosure trigger) — LLM should load skill body on first cadence-related user turn.
---

## Cadence 工作流

本项目使用 cadence 工作流管理讨论和决策档案。本文是 L0 协议精炼摘要；细则单一权威源在 `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/`。冲突时以 L2 为准。

### § 1. ASSUME INTERRUPTION

context 随时可能被 `/compact` 或重置。**新 session / `/compact` 后必须重做 § 10「session 启动行为」**，不假设"上次读过的还在"。

### § 2. 目录约定

- 讨论产物在 `cadence/`（不在 `docs/`）。`docs/` 保留给项目原有用途。
- **事项真实状态以 `cadence/_ACTIVE.md` 为准**（活跃决策、待决、TODO、最近讨论）。

### § 3. 项目档案落点

- 决策结论 → `_ACTIVE.md` 活跃决策（一行摘要 + pointer）
- 待决问题 → `_ACTIVE.md` 待决清单
- TODO → `_ACTIVE.md` TODO
- 完整 reasoning / trade-off → `discussions/<date>-<slug>.md`（整 阶段产物）
- 流式 entry → `streaming/<YYYY-MM-DD>-<topic-slug>.md`(记 阶段，append-only)

### § 4. 单判据「已被承接」

**承接对象覆盖"结论 OR 中间决定"**：用户明确或隐含确认过即记；未命中则不记。

**强信号（视为已承接）**：

- 接受性表态（「嗯」「好」「OK」「可以」）
- 用户基于此推进后续讨论（"那下一步 Y 怎么办" → 说明 X 已是既定前提）
- 用户在新决策中引用已讨论的 X

**弱信号（不算承接）**：

- 沉默 / 反问质疑（"确定吗？"还在讨论）

**倾向漏记 > 噪音**：档案膨胀比漏记一条成本更高；重要决策会反复出现、届时补记。

完整正反例 + 4 trigger 主动重读详见 L2 `recording-protocol.md`。

### § 5. 记录动作（happy path）

命中判据 → append entry 到 `cadence/streaming/<YYYY-MM-DD>-<topic-slug>.md` → 告知一行 `📝 已记：<摘要> → streaming/...`（不索取确认）。

#### § 5a. Recommended entry format (YAML frontmatter + markdown body)

````markdown
---
id: e1
created: 2026-05-21T12:30:00+08:00
status: accepted
chosen: 显式「开始学习」按钮触发
context: 教学模式 UX 设计访谈中讨论"首次进入"入口形态；担心自动触发误启动 session
options:
  - 显式按钮触发
  - 自动进入教学
  - 弹窗询问
rejected:
  - 自动进入: 用户路过页面就启动 session，缺乏控制感
  - 弹窗询问: 多一步骤打断流程
---

## E1: 教学入口用「开始学习」按钮触发

用户点击 → 创建 session + AI 发开场白
后续进入：自动恢复 active session，不重发开场白
````

> 📌 **非强制** — Markdown 段落格式也合法，**只要信息密度达到 `(chosen + context + options/rejected 三选二)` minimum 组合**。

#### § 5b. 信息密度对照（一眼看反差）

```
❌ 过简（下游 LLM 看不懂 — resume 失血）：
   ## E1: 教学入口
   - 用「开始学习」按钮触发
   - 已承接

✅ 充分（含 chosen + context + rejected，下游可独立理解）：
   ## E1: 教学入口用「开始学习」按钮触发
   讨论 UX 入口形态（自动 / 弹窗 / 按钮 3 方案）
   chosen: 显式按钮 — 用户点击后创建 session
   rejected: 自动进入（误启动）/ 弹窗（打断流程）
```

完整正反例详见 L2 `recording-protocol.md` § 2。

#### § 5c. 写完 entry 立即自检（L0 简版）

`chosen / context / (options 或 rejected)` 三项 minimum 是否齐？任一关键缺失 → **append 补充段**（append-only，不重写已有 entry）。完整 6 项 checklist 见 L1 `project-discuss/SKILL.md` § 2 Phase 1。

> ⚠️ 本 session 未 Read 过 L2 `recording-protocol.md` § 2「信息密度正反例」时，**先 Read 一次后续复用**（不每次 entry 重读 — context 膨胀）。

### § 6. project-discuss 激活规则

session 首条"项目相关"发言 → **必须** `Skill("project-discuss")`。

- ✅ 必激活：「用 Postgres」、「改 Auth」
- ❌ 不激活：「React hooks 怎么用」（纯技术问答）
- 🟡 边界模糊 → **倾向触发**（多触发成本低，漏触发代价高）
- ⚠️ **中途自检**：已产生决策但 `_ACTIVE/streaming` 空 → 立即补调追溯征询

完整正反例详表见 L2 `query-behavior.md`「修改/扩展类查询前置」节。

### § 7. 三阶段（记/整/查）+ subagent 调度

| 阶段 | 谁做 | 何时 | 产物 |
|---|---|---|---|
| **记（α 流式）** | 主 session 直写 | 命中判据 | `streaming/<date>-<slug>.md` append entry |
| **整（ε 整合）** | `recall-consolidator`（Plan-only） | 手动 `/cadence-consolidate` 或 Phase B 自动条件 | `discussions/<date>-<slug>.md` ADR-like doc |
| **查（ρ 检索）** | `recall-retriever` | 跨 session 历史查询 | summary + pointers（<500 tokens 硬限） |

**决策前回忆分析**（`recall-analyzer`，5+ 轮 / 多档案 / 冲突风险触发）fork 产三分类事实呈现用户。

**铁律**：subagent 只读 / Plan-only / 主 session 唯一写者。**Codex 形态额外要求 `spawn_agent` 强制调度**；OpenCode 形态 Task tool 即可（Codex XML wrapping 模板 + OpenCode 差异详见 L2 `harness-adapters.md`）。

### § 8. Skill 正交并行 + 借口反驳表

`project-discuss` 是**常驻监察层**；其他 skill（`brainstorming` / `writing-plans` / `executing-plans` / `cadence-handoff` / `cadence-resume` / 未来任何 skill）是**任务特定层**，职责不重叠，**永远并行不互斥**。

**最常见误判**：调了 brainstorming 就以为可以跳 project-discuss。

#### 借口反驳表（Mode B 防御：rationalize 不记录的瞬间）

| # | 借口 | 反驳 |
|---|---|---|
| 1 | "流程 skill 已激活，project-discuss 可跳过" | **错** — 两者正交，brainstorming 管探索、project-discuss 管档案落地 |
| 2 | "用户没明确说要记" | **错** — 单判据扩展到"中间决定"，承接信号一命中就记 |
| 4 | "概念太多，简化执行" | **错** — 已简化到 3 阶段（记/整/查），不要凭印象判断"这次例外" |
| 5 | "这条不重要，先不写 archive" | **错** — 判断标准是"是否被承接"，不是主观重要性 |

> #3「上限到了再问归档」依赖段管理概念，见 L1 `project-discuss/SKILL.md`。

### § 9. 指向 L1/L2

- **完整协议**：`Skill("project-discuss")`
- **细则单一权威源**：
  - `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/recording-protocol.md` — 记 阶段细则 + 信息密度正反例 + entry schema + incidents 附录（§8）
  - `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/query-behavior.md` — 查询前置 + 4 trigger 重读 + 文档可信度 L1-L4（§11）
  - `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/harness-adapters.md` — Codex `spawn_agent` + OpenCode 工具映射（v0.5 合并 codex-tools + opencode-tools）
- **关系契约**：L0 是 L2 细则的**精炼摘要**，不是平行定义。L0/L2 冲突时以 L2 为准。

### § 10. Session 启动时的行为（必做）

首条"项目相关"发言时（判据见 § 6）：

1. **必须触发** `Skill("project-discuss")`（即使同时运行其他 skill，正交并行）。
2. **先列目录再决定读什么**：
   - 第一步：`ls cadence/` 或 Glob `cadence/*.md`，看有哪些文件
   - 第二步：按用户话题决定：
     - 状态 / 活跃 / 待决 / TODO → 读 `_ACTIVE.md`
     - 项目简述 / 话题词典 / 导航 → 读 `_INDEX.md`
     - 具体话题命中 → 读对应 `discussions/...md`
     - 历史（> 14 天）→ 读 `_INDEX-HISTORY.md`
     - 协议本身 → 读 L2 `recording-protocol.md` / `query-behavior.md`
   - **兜底**：话题不明确时至少读 `_INDEX.md`（不无脑读 `_ACTIVE.md` 全文）。
3. **`/compact` 或新 session 后必须重做步骤 2**（§ 1 ASSUME INTERRUPTION）。
