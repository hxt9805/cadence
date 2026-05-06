---
name: project-discuss
description: >
  ⚠️ 本 skill 与 brainstorming / writing-plans / executing-plans 等流程 skill **正交、可并行**触发，不互斥。
  已调用流程 skill 不等于可以跳过本 skill；只要涉及项目讨论/决策/查询，都需要额外激活本 skill。
  项目讨论管理协议。管理讨论上下文、决策记录、查询行为。
  触发：用户讨论项目方向/设计/技术选型/需求分析/功能规划时；
  用户问"我们讨论到哪了"/"XX 确定了吗"；
  用户想修改已确定的内容；用户提供外部文档；
  用户询问项目现状/架构/实现细节/历史决策（含 debug 揭示架构问题时）；
  当 bug 修复涉及决策、揭示架构问题、或修复逻辑非显而易见时。
  本质上任何涉及项目讨论、决策、查询的场景都应触发。
---

# Project Discuss

管理项目讨论、记录决策、处理查询、记录 incidents。Cadence 工作流阶段 A 的核心 skill。

本 SKILL.md 是主入口（动作骨架 + Phase 化导航 + 借口反驳表）。细则分散在 `references/` 下，按需读取：

- `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/recording-protocol.md` — 记录行为细则（判据 / 三 Phase 协议 / schema / 借口反驳表）
- `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/query-behavior.md` — 查询行为规则（加载策略 / 4 trigger 主动重读 / retriever 调用 / 路由表管理）
- `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/doc-reliability-protocol.md` — 文档可信度协议（L1-L4 分级）
- `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/incident-handling.md` — incident 记录规则（触发条件 / 模板）
- `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/codex-tools.md` — **Codex CLI 形态专用**：SessionStart 注入 / subagent fork / slash command / context 预算的等价机制映射（CC 形态可忽略）

## § 1 讨论开始前（必做）

### 第 1 步：检查 cadence 骨架是否存在

读 `cadence/_INDEX.md`：

- 不存在 → **不自己 scaffold**，告诉用户：

  ```
  看起来这是新项目，还没初始化 cadence。我可以先跑 /cadence-init
  建好骨架，然后我们继续讨论。要开始吗？
  ```

  - 用户同意 → 调 `Skill("cadence-init")`，初始化后继续
  - 用户拒绝 → 正常讨论，不记录

- 存在 → 继续第 2 步

### 第 2 步：建立全局上下文

1. **读 `cadence/_INDEX.md`**（纯索引，< 800 tokens）——项目简述 / 话题词典 / 快速导航
2. **Session 内第一次需要活跃状态时，读 `cadence/_ACTIVE.md`**（~1800 tokens）——活跃决策 / 待决 / TODO / 最近讨论
3. **判断是否需要加载更多**（按 `references/query-behavior.md` 的加载策略）：
   - 用户提到的话题在词典里 → 读指向的文档
   - 用户问历史话题（> 14 天前）→ 读 `_INDEX-HISTORY.md`
4. **不全量加载**：每次最多加载 2-4 个相关文档；默认不重读，4 trigger 时重读（见 `references/query-behavior.md`）

## § 2 Phase 化协议骨架（记 / 整 / 查）

完整细则见 `references/recording-protocol.md`。

### Phase 1：记（流式记录）

**触发**：单判据「已被承接」命中（用户明确或隐含确认，含中间决定）→ 立即写 streaming entry，不等用户说"记下"。

**落点**：`cadence/streaming/<YYYY-MM-DD>-<topic-slug>.md`（append-only，按主题分文件）

**告知**：写入后一行输出 `📝 已记：<摘要> → <path>#<entry-id>`

**铁律**：append-only，永不编辑已有 entry；撤回追加 tombstone（详见 `references/recording-protocol.md` § 2）

### Phase 2：整（整合）

**触发**：LLM 自判（话题收尾 / context ≥80% / ADR 结构已全）或 `/cadence-handoff` 兜底扫描。

**流程**：派 recall-consolidator subagent（Plan-only）→ 接收 yaml plan → 主 session 执行三步写（Write → Validate → Archive）。Phase 2 是 gate：Validate 未通过绝不进入 Archive。

**完整流程与失败降级见** `references/recording-protocol.md` § 3

### Phase 3：查（跨 session 检索）

**触发**：用户问历史决策 / 主 session 不确定某历史是否有记录 / 4 trigger 主动重读。

**流程（强制）**：**必须** fork retriever subagent — CC 用 Task tool / Codex 用 `spawn_agent(explorer, message=<XML wrapped recall-retriever prompt>)`（详见 `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/codex-tools.md` § 2）→ 传入 `user_query` + 轻量 context（≤2K tokens）→ 接收 `summary` + `pointers[]`（**总 <500 tokens 硬限**）→ 主 session 向用户呈现。

**铁律 — Codex 形态特别强调**：**禁止主 session 直接 Read / Grep / `Select-String` / `findstr` cadence 档案** 来回答历史检索 query。即使 LLM 判断"本地一两次 grep 就够"、即使 sandbox 拒 `rg` 让人想 fallback 本地工具，**仍必须走 `spawn_agent(explorer)` 路径**。理由：
1. **context 不膨胀契约** — 主 session 直读会把档案全文吞进上下文；Codex App 默认 ≤400K，长期累积必撞顶
2. **行为一致性** — CC 与 Codex 形态行为不能分叉，cadence "暗仓库" UX 失守即是协议违例
3. **sandbox 兼容** — explorer agent 有内置 search 能力，不依赖主 session 的 sandbox policy

**反例（禁止）**：「刚刚没有 spawn subagent，我只是本地读了几个 cadence 文档和用 PowerShell 搜了一下」—— 这就是协议违例。

**完整触发路径与失败降级见** `references/query-behavior.md` 查阶段节

### recall-analyzer（v0.2.x 保留）

5+ 轮 / 多档案 / 冲突风险时 fork `agents/recall-analyzer.md`，产三分类事实（你说的 / 档案有的 / 我推断的）呈现用户。主 session 写，subagent 不写。

## § 3 主 session 工作记忆（v0.4 lifecycle 支持）

主 session 在对话上下文中（**不落盘**）维护以下项，仅用于 fork consolidator 时传入：

| 项 | 维护方式 | 用途 |
|---|---|---|
| `n_rounds_counter` | 每用户发言 +1 / 触发 lifecycle 时归零 / session 启动初始化为 0（**用户第一发言前**） | 冷启动兜底 trigger（每 N=20 轮触发一次 consolidator） |
| `recent_user_turns` | FIFO buffer 容量 10 / 每用户发言提炼摘要 ≤50 字（**含**）推入 / **超出时丢最旧** | consolidator 检测"用户言命中"信号（如"X 写完了"） |

> **说明**：表中 2 项是**主 session 持续维护**的工作记忆。另有 1 项 `git_log_window` 是**按需 collect**（fork consolidator 前用 Bash 收集），见下方"不维护"块。完整 3 项详见 `agents/recall-consolidator.md` § 主 session 工作记忆约定。

**不维护**（每次按需 collect）：
- `git_log_window`：fork consolidator 前用 Bash 跑 `git log --since=30.days ...`
  - **Fallback**：如 Bash 不可用（permission 限制 / git 不存在等）→ 主 session 传入 `git_log_window: []`，consolidator 仅依赖其他 5 类信号判断（仍可工作，detection 精度略降）

**重启行为**：session 重启 / context reset 时所有工作记忆归零——这是 acceptable trade-off（接受 reset 是 cadence v0.4 设计哲学，源自 Anthropic harness-design 文章的 "ASSUME INTERRUPTION" 原则，详见 design doc § 9 Attribution 节引用）。重启后第一次冷启动 N 轮 trigger 自然回归正常节奏。

完整 fork 输入 schema 详见 `agents/recall-consolidator.md` § 输入 schema。

## § 4 _ACTIVE.md 段独立管理

### 段独立触发归档（v0.4）

每次写入 `_ACTIVE.md` 某段后，**仅检查该段的条数上限**，不评估其他段：

> **触发动作**：满时派 consolidator 静默判断，仅对该段（不波及其他段）。

| 段 | 条数上限 | 满时 trigger |
|---|---|---|
| 活跃决策 | 8 | 第 9 条到来 |
| 待决 | 10 | 第 11 条到来 |
| TODO | 10 | 第 11 条到来 |
| 最近讨论 | 5 | 第 6 行到来 → 把第 1 行（最旧）移到 `_INDEX-HISTORY.md` |

**总上限 `<1800 tokens`** 作**最终兜底**：日常归档由段独立 trigger 处理，总上限不再是归档主入口。

### 软硬阈值切换（v0.4）

**软警告（上限 -2 条 / -1 行）**——任一段命中即触发：
- 各段阈值：活跃决策 6/8、待决 7/10、TODO 7/10、最近讨论 4/5
- 主 session 静默 fork consolidator（`trigger_reason=section_70`）
- 接收 yaml plan → 自动 Edit `_ACTIVE.md` + Write archive doc → **一行通知**

通知格式（按 `docs/design/2026-04-27-cadence-v0.4-design.md` § 5.1.2 完整示例 — 含 commit sha + paths 证据）：

```
📝 自动整理 N 条 → archive/<doc>.md
   - D5 (git log 命中已实施 commit 8dc1a91 paths: src/styles/)
   - D8 (30 天无讨论标 stale)
   - TODO[#3] (用户言"搞定"已删)
   不同意可说："撤回归档 D5" / "恢复 TODO[#3]"
```

**100% 硬阈值**（兜底）：
- 任一段达上限（活跃决策 8/8 / 待决 10/10 / TODO 10/10 / 最近讨论 5/5）
- 主 session **回退询问用户**（v0.3 行为，详见下方「补救路径」）
- 实践中软警告应处理掉绝大多数情况；100% 触发应**罕见**

如观察到 100% 频繁触发 → dogfood 信号告知阈值需调整或 lifecycle 检测信号不全（详见 design doc § 5.1.3 末尾说明）。

### Undo 协议

用户对自动归档不满意时：
- "撤回归档 D5" → 主 session 按 plan 中 `undo_hint` 反向操作（Edit `_ACTIVE.md` 还原 + Edit archive 移除条目）
- 如 plan 已丢失（session 重启 / context reset）→ 主 session 凭 git log 找到对应 archive commit + 反向 Edit
- 详见 `agents/recall-consolidator.md` § 输出 plan 增量字段 `undo_hint`

### 补救路径（各段通用）

1. 有对应 discussion 文档 → 追加"已归档决策"节
2. 无文档但关联主题明确 → 建新 discussion 文档
3. 孤立决策 → 按 `_CONVENTIONS.md` 的「征询图景」③ 询用户

→ 归档完成 → 从 `_ACTIVE.md` 移除最老那条 → 再 Write 新决策 → 📝 告知含"归档了 X → Y"

**关键**：永远不让写入失败。所有路径失败时退化为"用户手动决定 + 新决策暂不写入"。

### 归档策略

- 超过 14 天的讨论记录 → 移到 `_INDEX-HISTORY.md`
- 超过 30 天的 `_INDEX-HISTORY.md` 记录 → 按月分组移到 `_archive/YYYY-MM.md`

## § 5 记录位置分流

| 内容类型 | 写入位置 |
|---|---|
| 决策结论 | `_ACTIVE.md` 活跃决策 |
| 硬约束 | `_INDEX.md` 项目简述（推翻时双写 `_ACTIVE.md`）|
| 待决问题 | `_ACTIVE.md` 待决清单 |
| TODO | `_ACTIVE.md` |
| 详细设计 | `cadence/discussions/<date>-<slug>.md` |
| Bug/incident | `cadence/discussions/incidents/YYYY-MM-DD-xxx.md` |
| 讨论记录 | `_ACTIVE.md` 最近讨论（14 天内）/ `_INDEX-HISTORY.md`（14-30 天）|
| 话题词典 | `_INDEX.md`（不变）|

## § 6 借口反驳表

| # | 借口 | 反驳 |
|---|---|---|
| 1 | "这个 session 已经在用 brainstorming，project-discuss 应该被覆盖" | brainstorming 管探索过程，project-discuss 管档案落地，**两者职责正交**，必须并行 |
| 2 | "用户没明确说要记，我先不记" | 单判据"已被承接"的承接对象已扩展（覆盖中间决定）——只要用户有承接信号（如"嗯，先排除 C"），**不用等用户说"记下"** |
| 3 | "上限到了再问用户怎么归档" | 70% 软警告时 consolidator 已经静默处理了，**不要等到 100%** |
| 4 | "概念太多，我先简化执行" | 协议**已经简化到 3 Phase**——如果还觉得难记，回头读 SKILL.md，不要凭印象执行 |
| 5 | "这条决策不重要，先不写 archive" | archive 是 LLM 暗仓库，写多写少用户无感——**漏写的代价远大于写了不读** |

## § 7 中途自检

本 skill 与 `superpowers:brainstorming` / `writing-plans` / `executing-plans` 等流程 skill **正交、可并行**——调用了流程 skill 不等于可以跳过本 skill。

**Session 进行中若发现本 skill 未被触发**（典型信号：已在讨论/决策但从未加载 `_INDEX.md`、从未记录任何条目），必须：

1. 立即激活本 skill（补调 `Skill("project-discuss")`）
2. 做追溯征询：列出本 session 已产生的决策点，一次性问用户"要全记 / 选记（指出编号）/ 都别记？"
3. 按用户选择补写，汇报时说明"追溯记录"

宁可多自检一次，不要等用户质问。

## § 8 特殊场景处理

### 查询类

- **"我们讨论到哪了" / "目前确定了什么"** → 读 `_INDEX.md` + `_ACTIVE.md`，综合总结
- **"XX 确定了吗"** → 查活跃决策 + 历史讨论 + 代码实际状态，综合引用来源
- **用户问历史决策过程** → 查 `_archive/` 对应月份归档文件

### 修改类

- **用户想修改已确定内容** → 确认意图后更新文档 + `_ACTIVE.md`；重大变更归档旧版到 `_archive/`
- **开发中发现设计与现实不一致** → 更新设计文档 + `_ACTIVE.md` 活跃决策记录变更原因

### 导航类

- **讨论主题不在话题词典中** → 用 Grep 搜 `cadence/` 目录找相关文档
- **用户提供新外部文档** → 整理关键内容到对应 discussion 文档

## § 9 话题词典维护

每次写入决策到 `_ACTIVE.md` 后，顺手更新 `_INDEX.md` 底部的「话题词典」：

```markdown
## 话题词典
- 数据库选型 → discussions/05-tech/database.md
```

文档数超过 10 时，建议维护 `cadence/discussions/_INDEX-ROUTING.md`（见 `references/query-behavior.md` §「路由表管理」节）。

## § 10 Session 结束提醒（克制版）

识别到明显终止信号（「今天到这」「改天」「换个项目」）时，可**一次性、克制地**提醒：

```
看起来告一段落了。如果想把本 session 内容保留到档案，可以用 /cadence-handoff。
```

**同一 session 只提醒一次**。不基于长度触发。
