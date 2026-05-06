---
name: cadence-bootstrap
description: Use when starting any conversation in a cadence-managed project (project root contains cadence/_INDEX.md or cadence/_ACTIVE.md). Establishes cadence workflow conventions — 记 / 整 / 查 三阶段记录协议, _ACTIVE.md / _INDEX.md state contract, recording criterion 单判据「已被承接」, session start behaviors, and subagent dispatch rules. CC harness reads this skill via SessionStart hook injection (automatic). Codex / other harnesses match this description on session start (progressive disclosure trigger) — LLM should load skill body on first cadence-related user turn.
---

## Cadence 工作流

本项目使用 cadence 工作流管理讨论和决策档案。

### 核心约定

- **讨论产物在 `cadence/` 目录**(不在 `docs/`)。`docs/` 保留给项目原有用途(API 文档、用户手册等)。
- **事项真实状态以 `cadence/_ACTIVE.md` 为准**(活跃决策、待决、TODO、最近讨论)。`_INDEX.md` 是纯索引(项目简述、话题词典、导航),不放变化高频内容。
- **记录分文件**:
  - 当前活跃内容(决策、待决、TODO、最近讨论)→ `cadence/_ACTIVE.md`
  - 索引(项目简述、话题词典、快速导航)→ `cadence/_INDEX.md`
  - 完整 reasoning / trade-off → `cadence/discussions/NN-主题/`
- **文档可信度分级**(L1-L4,见 `cadence/_CONVENTIONS.md`):
  - 事实性问题以代码/配置为准
  - 意图性问题以 cadence 讨论记录为准
  - 手写文档(README、docs/)低可信,查询前需代码复核

### 记录行为(v0.4 — 记 / 整 / 查 三阶段)

- **单判据「已被承接」**:用户明确或隐含确认过即记;未命中则不记。v0.2.x 的"未来价值 + 已被承接"双判据在 brainstorming 树状讨论里系统性漏记,v0.3/v0.4 把"未来价值"下移到整 阶段(ε 整合)。
- **记 阶段(α 流式)**(主 session 直写):命中判据 → append streaming entry 到 `cadence/streaming/<YYYY-MM-DD>-<topic-slug>.md`,一行告知"📝 已记:... → streaming/..."(不索取确认)。
- **整 阶段(ε 整合)**(`recall-consolidator` subagent,Phase B 启用):阶段性把 streaming 条目整合为 ADR-like `discussions/<date>-<slug>.md`(Plan-only 产出,主 session 写入)。
- **查 阶段(ρ 检索)**(`recall-retriever` subagent,跨 session):主 session 查历史档案时派 retriever,只读 + <500 tokens 硬限 + 返回 summary + pointers。
- **决策前回忆分析**(`recall-analyzer`,v0.2.x 保留):明确信号(5+ 轮 / 多档案 / 冲突风险)触发时 fork,产三分类事实呈现用户。
- **倾向漏记 > 噪音**:档案膨胀比漏记一条成本更高;重要决策会反复出现、届时补记也不迟。
- 用户信号永远优先:「记一下」必记、「别记」不记、「撤回」追加 tombstone。
- 详细协议见 `cadence/_CONVENTIONS.md` 的「记录判据(v0.4)」+「三阶段通路关系(v0.4)」+「征询图景」节。

### Codex 形态调度铁律（CC 形态可忽略本节）

> 仅适用于 Codex CLI / App / IDE 形态；CC 形态有 SessionStart hook + Task tool 自动覆盖，本节无效。

Codex 默认 session policy 偏保守，倾向"主 session 本地解决"。**下列三类操作必须走 subagent，禁止主 session 直接读 cadence 档案**：

1. **历史检索 query**（"上次 X 我们怎么定的" / "XX 确定了吗" / "之前讨论过 Y 吗"）→ 必须 `spawn_agent(explorer, message=<wrapped recall-retriever prompt>)`
2. **整合归档**（话题收尾 / context ≥80% / `_ACTIVE.md` 段达阈值 / handoff 兜底）→ 必须 `spawn_agent(worker, message=<wrapped recall-consolidator prompt>)`
3. **决策前回忆分析**（5+ 轮 / 多档案 / 冲突风险）→ 必须 `spawn_agent(worker, message=<wrapped recall-analyzer prompt>)`

**为什么是铁律**：
- Codex App 默认 context ≤400K（CC Opus 4.7 是 1M 的 40%），主 session 直读 cadence 档案累积必撞顶
- 走 subagent 才能保持 cadence 「暗仓库 + context 不膨胀」契约
- subagent 与主 session 共享 filesystem 但 conversation 隔离，输出 consolidated（非全文转录）

**spawn 流程详见** `${CLAUDE_PLUGIN_ROOT}/skills/project-discuss/references/codex-tools.md` § 2。

**反例（禁止 — 任何一条命中即协议违例）**：
- ❌ 主 session 直接 `Read cadence/streaming/...md` 或 `cadence/discussions/...md` 来回答历史检索 query
- ❌ 主 session 用 PowerShell `Select-String` / `findstr` / bash `grep` 搜 cadence/ 内容（即使 sandbox 拒 `rg` 也不能 fallback 本地 grep — 应改用 `spawn_agent(explorer)`）
- ❌ "刚刚没有 spawn subagent，我只是本地读了几个 cadence 文档" — 这就是协议违例

### 核心命令(用户主动触发)

- `/cadence-init` — 初始化或补全 cadence 目录结构
- `/cadence-handoff` — 整理当前 session 到档案(长 session 换新 session 前用)
- `/cadence-resume` — 继续之前某次 session 的讨论

### 不要自动做的事

- **不自动执行 handoff / resume / init**。这些由用户显式命令触发。
- 可以在用户明显 session 终止信号(「今天到这」「改天聊」等)时**提醒命令存在**,但不执行,且同一 session 只提醒一次。
- 新 session 启动时**不主动读取 .handoff/ 纸条**。用户需要时自己跑 `/cadence-resume`。

### Session 启动时的行为(必须执行)

首次看到用户发言**与本项目相关**时(不限于技术或架构。判据见 `_CONVENTIONS.md` 的「修改/扩展类动作前的查询前置」段;**边界模糊时倾向触发**——多触发一次成本低,漏触发成本高。反例:纯外部知识问答(「React hooks 怎么用」)/ 纯学习问题 / 明显闲聊不触发):

1. **必须触发** `cadence:project-discuss` skill — 即使同时运行**任何其他 skill**(无论是 `superpowers:*` 流程 skill、`cadence:*` 自身的 handoff/resume skill、还是未来引入的任何 skill),本步骤仍需执行。两者**正交并行,不互斥**。
2. **先列目录再决定读什么**(view directory first):
   - 第一步: `ls cadence/` 或 Glob `cadence/*.md`,看有哪些文件
   - 第二步: 按用户发言话题决定读哪个:
     - 用户问当前状态 / 活跃决策 / 待决 / TODO → 读 `cadence/_ACTIVE.md`
     - 用户问项目简述 / 话题词典 / 导航 → 读 `cadence/_INDEX.md`
     - 用户提到具体话题(在文件名 / 词典命中)→ 读对应 `discussions/...md`
     - 用户问历史(> 14 天前)→ 读 `_INDEX-HISTORY.md`
     - 用户问 cadence 协议本身(怎么记 / 怎么查)→ 读 `_CONVENTIONS.md`
   - **兜底**: 首次涉及项目讨论但话题不明确时,至少读 `_INDEX.md` 建立全局上下文(800 tokens 起步可接受;不无脑读 `_ACTIVE.md` 全文)
3. **ASSUME INTERRUPTION**: context 随时可能被 `/compact` 或重置。新 session 启动 / `/compact` 后**必须重新执行步骤 2**,不假设"上次读过的还在"。

**关键区分: 激活 skill ≠ 每句都记**

- **Gate 1(激活)**: 项目相关就激活,让 skill 进场监察(**宽**)
- **Gate 2(写 streaming)**: 激活后,单条发言过"已被承接"判据,命中才记(**严**)
  - 闲聊 / 脱题 / 脑暴中未被承接的选项 / 反问质疑 → 不记
  - 已被承接的结论 OR 中间决定 → 记

**两个 gate 倾向相反但各有道理**:
- Gate 1: 漏触发 < 多触发(漏触发 = 决策无主落地)
- Gate 2: 漏记 > 噪音(噪音 = 档案膨胀)
- 监察要广,记录要精

**核心判据**(遇到清单外的 skill 时靠此判断):`project-discuss` 是**常驻监察层**,管项目档案的加载与落地;其他 skill 是**任务特定层**,管具体动作的流程。两类职责**不重叠**,永远并行。

**反例警告**:调用了 brainstorming 就以为可以跳过 project-discuss,是最常见误判。典型误判场景包括但不限于:
- brainstorming / writing-plans / executing-plans 已激活 → 误以为档案由它们负责
- 未来的任何流程 skill 激活时 → 同类误判

清单外的情况:**任何"Claude 已在做事"的状态都不能替代 project-discuss**。

**中途自检**:session 进行中若发现 project-discuss 未被触发(已产生决策但从未记录 / 从未读 `_INDEX.md`),立即补调并做追溯征询,不要等用户质问。
