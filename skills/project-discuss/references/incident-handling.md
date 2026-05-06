# Incident 记录规则

> incidents = bug / 事故 / tricky fix 等需要留档的"意外事件"。本文件是 skill 的内部行为细则，指导 Claude 何时、如何记录 incidents。
>
> **v0.4 现状**：单判据「已被承接」+ 记 阶段（α 流式）写入 streaming/ + 整 阶段（ε 整合）到 discussions/incidents/（或合并到主题 discussion）+ 查 阶段（ρ 跨 session 检索）recurring incident。
>
> **演化脉络**：v0.2.2 的「快速/完整通路」二分在 v0.3 演化为记/整/查三阶段分工（α/ε/ρ，见 `recording-protocol.md`「三阶段通路关系」节），v0.4 简化命名沿用，incident 场景沿用同一三阶段模型。

## 触发条件

以下场景下 project-discuss 应考虑 incident 记录：

- 用户修复了一个 bug
- 发生了生产事故 / 回归
- Performance 问题被解决
- Tricky 的代码修改（修复逻辑非显而易见）
- 揭示了既有架构或设计问题的修改

## 判断是否值得记录（v0.4 单判据）

按 `recording-protocol.md` 的**单判据「已被承接」**（用户明确或隐含确认修复完成 / 问题已解决）。

v0.2.x 的"未来价值"判断（根因 / 修复模式会再次遇到）在 v0.3/v0.4 **下移到整 阶段（ε 整合）**（由 `recall-consolidator` 筛选），记 阶段（α 流式）只看是否已被承接——承接即写 streaming entry，不预判价值。

**承接的典型信号**：
- 用户说"修好了" / "问题解决了" / "可以了"
- 用户基于修复推进后续工作（"那我接着做 X"）
- 修复 commit 已落盘 + 用户转向新话题

**弱信号 / 不算承接**：
- 用户还在 debug 中、根因未明 → 先记一条简版 streaming entry（见 记 阶段在 incident 场景的落地）
- 用户沉默 / 转话题但未确认修复

**仍可不记的 bug**（即便承接也低价值）：
- Typo、null check 漏了、边界条件
- 一次性小问题
- git commit message 足够说清楚的

注：这类低价值 bug 的筛选由整 阶段（ε 整合）`recall-consolidator` 在整合时处理（可能不生成独立 incident doc，只留 streaming entry）。记 阶段（α 流式）若拿不准、倾向记。

## 记 / 整 / 查 三阶段在 incident 场景的分工（v0.4，原 α/ε/ρ）

Incident 的记录沿用 project-discuss v0.3/v0.4 的三阶段模型：

### 记 阶段（α 流式，承接瞬间写 streaming entry）

修复被用户承接时，**主 session 直接 Write** 一条 streaming entry 到 `cadence/streaming/<YYYY-MM-DD>-<incident-slug>.md`：

- 单判据「已被承接」命中即写，不预判价值
- Entry schema 同 `recording-protocol.md` 记 阶段节；`context` 字段记症状 + 根因（若已明），`chosen` 记修复方案，`rejected` 记被排除的候选修复（若有）
- **根因未明时**：先记简版 entry，`context` 标"根因待查"，后续讨论继续 **append 新 entry** 补全（append-only 铁律——不修改已有条目）
- 写完一行告知：`📝 已记 incident：<简述> → streaming/<file>.md#<entry-id>`

### 整 阶段（ε 整合，决策后由 consolidator 判定是否产出 incident doc）

触发条件同 `recording-protocol.md` 整 阶段节（话题收尾 / LLM 自判 / handoff 兜底）。由 `recall-consolidator` subagent 产出 Plan-only yaml，主 session 执行两阶段写：

- **有留档价值的 incident**（涉及多候选 / trade-off / 改动大 / 揭示架构问题 / 可能复发）→ 整合到 `cadence/discussions/incidents/YYYY-MM-DD-简述.md`（完整模板或摘要模板，见下文）
- **低价值 incident**（typo / 一次性小问题）→ 不产出独立 doc，只保留 streaming entry
- **架构级 incident** → 除 incidents/ doc 外，可能在 `_ACTIVE.md` 活跃决策里追加修正条目

整合完成后 streaming 前置标 `status: archived` + append tombstone（同标准整 阶段流程）。

### 查 阶段（ρ 跨 session 检索，recurring incident）

用户问"上次类似 incident 怎么处理" / "这个 bug 之前遇到过吗" → 主 session fork `recall-retriever`（只读 <500 tokens）检索 `discussions/incidents/` + `_archive/` → 回传 summary + pointers → 按需 Read 具体 incident doc。

详见 `recording-protocol.md` 查 阶段节与 `references/query-behavior.md` retriever 节。

### recall-analyzer（决策前分析，v0.2.x 保留）

修复前若出现多档案对照 / 多候选修复方案 trade-off / 与已有架构决策冲突风险 → 主 session 在决策前 fork `recall-analyzer`（Plan-only），详见 `agents/recall-analyzer.md`。不 fork 的默认场景：单一修复 + 无冲突。

### 用户显式信号

- 用户说"这个太琐碎别记" → 不记
- 用户说"记一下 incident" → 必记（单判据强制满足）

## 完整模板（整 阶段，ε 整合产出）

文件：`cadence/discussions/incidents/YYYY-MM-DD-简述.md`

```markdown
# [YYYY-MM-DD] 简短描述

## 症状
用户/系统观察到什么

## 根因
真正的问题在哪

## 修复
- 改动的文件：
  - `src/auth/login.ts:42-58`
  - `src/middleware/auth.ts:new`
- 关键逻辑：[1-3 句说明]

## 为什么这么修（非显然时写）
- 候选方案 A：...
- 候选方案 B：...
- 选 A 的理由：...

## 防止复发
- 需要的测试：
- 需要的监控：
- 需要的约定：
```

## 摘要版模板（整 阶段，ε 整合产出）

```markdown
# [YYYY-MM-DD] 简短描述

## 症状
...

## 修复
- 改动文件：...
- 关键逻辑：...
```

**模板选择判据**（整 阶段，ε 整合时）：
- 完整模板：涉及候选方案 + trade-off / 改动范围大 / 揭示架构问题
- 摘要模板：单一修复 + 逻辑清晰 / 改动小 / 备忘性质

## 更新 _ACTIVE.md / _INDEX.md（整 阶段，ε 整合后）

整 阶段（ε 整合）产出 incident doc 后，同一两阶段写流程中：

1. 更新 `cadence/_ACTIVE.md` 的「最近讨论」表格，添加一行：
   ```
   | YYYY-MM-DD | [incident] 简述 | 根因+修复一句话 | incidents/YYYY-MM-DD-xxx.md |
   ```
2. 如果 incident 揭示了架构问题 → 可能需要在 `_ACTIVE.md`「当前活跃决策」里添加修正
3. 如果 incident 值得让 Claude 今后警示 → 加到 `_INDEX.md` 的话题词典

## 不记录 incident 的情况

- 用户还在处理中（未被承接 → 不记，等承接后再写记 阶段 streaming entry）
- 用户明确说「这个太琐碎，不记」
- 同一天内已记过类似（**不修改已有 entry**，而是 append 新 entry 注明"关联 ^entry-xx"；整 阶段（ε 整合）时合并）
