# ADR-002: Bootstrap (L0) must inline happy-path recording protocol

**Status**: Accepted (v2 修订)
**Date**: 2026-05-22
**Deciders**: hxt9805
**Context**: Architecture review 2026-05-22 (Candidate A grilling round 6, 8 + deepseek hostile review)

## Context

cadence-bootstrap/SKILL.md 在 SessionStart 时被 hook 注入到 LLM context。
设计上有两种倾向：
- 极简（类似 superpowers' using-superpowers，~118 行，0 协议内容）
- 自包含（inline happy path 协议）

## Decision

L0 (cadence-bootstrap/SKILL.md) **必须 inline 以下内容**（目标 110-130 行）：

1. 单判据「已被承接」摘要（L2 recording-protocol §1 的精炼）
2. 记录动作 happy path（entry 落点 + minimal schema + 信息密度强制引用）
3. `project-discuss` 激活规则（精简到 anchor 示例，详表指向 L2）
4. 三阶段名字 + subagent 调度 meta-rules
5. 借口反驳表 4 项（#1/#2/#4/#5，#3 依赖段管理概念下移 L1）

## Rationale (v2 重写 —— "鸡生蛋"论证)

cadence 的核心 paradox：**要正确记录决策就需要 `project-discuss` 的协议规则，
但 `project-discuss` 的规则需要在「已被承接」判据命中时才能加载到 context**。

如果 L0 极简（只含 meta-protocol），LLM 在首条用户发言时：
- 没看到记录协议 → 不知道该不该记
- 没 invoke project-discuss → 看不到完整协议
- 完成响应 → 决策已经过去，后续 invoke project-discuss 也救不回

L0 inline happy-path 协议直接解决这个鸡生蛋：LLM 在 session 启动后已经
"自带"了核心记录规则，即使没 invoke project-discuss 也能记录关键决策。

### 区分两种 failure mode (v2 加)

ADR-002 实际防备两种不同的失败模式，各自有不同的论证：

| Failure Mode | 描述 | 防御机制 | 概率 |
|---|---|---|---|
| **Mode A** | 首发言未被识别"项目相关"，`project-discuss` 未激活 | L0 inline happy path 协议（单判据 + 记录动作） | 未知（需 dogfood） |
| **Mode B** | `project-discuss` 已激活，但 LLM 在单条决策时 rationalize 不记录 | L0 inline 借口反驳表 4 项 | 显然高于 Mode A |

借口反驳表放 L0 的真正价值是 **Mode B 防御**：即使 project-discuss 已激活，
LLM 在决策瞬间 rationalize 时**不会去翻 L2 recording-protocol.md 的 §7**。
L0 让反驳表始终在 context 里，LLM 在做"记不记"判断时**零延迟匹配**。

## Consequences

**正向**：
+ 鸡生蛋问题被打破，首发言决策不再可能完全漏记
+ Mode B 防御零延迟（LLM 看到借口立即匹配反驳）
+ Gate 1 漏触发的代价从"灾难"降为"边界用法缺失"

**负向**：
- bootstrap 注入比 superpowers using-superpowers 长（~110-130 行 vs 118 行，
  cadence 多了 happy path 协议）
- 每个 cadence session ~25-40 行的"always-injected"协议开销

## (v2 新加) Precautionary Design 声明

本 ADR 的 Mode A 防御论证缺少 dogfood telemetry 支持 — "首发漏激活会导致
失血"是 hypothesis 不是 fact。在 cadence 当前无遥测的前提下，本设计是
**precautionary design**（预防性设计）：

- 缺数据时倾向保守（L0 inline 协议）而非冒险（L0 极简）
- 当 dogfood 数据可得时，重新评估 Mode A 实际频率
- 如 Mode A 频率 <1%，可考虑把 happy path 协议从 L0 下移 L1，只保留 Mode B
  防御（借口反驳表）

## Considered Alternatives

- **L0 极简（纯 meta-protocol，0 协议）**：拒绝 — 鸡生蛋问题不解决，
  Mode A silent loss UX 不可接受
- **session 启动强制 invoke project-discuss**：拒绝 —
  · LLM 可能在 invoke 完成前就响应用户首条发言
  · 一旦 invoke，把 ~249 行 L1 内容全部吞进 context，对"轻量闲聊"
    场景是浪费
- **不要 L0，只 inject project-discuss/SKILL.md 全文**：拒绝 —
  project-discuss/SKILL.md 含大量 edge case 内容，每 session 注入浪费 context

## L0 是 L2 精炼摘要的关系契约 (v2 加)

L0 inline 的协议内容是 L2 细则的**精炼版**，**不是平行定义**：
- 单一权威源 = L2
- L0 写错时以 L2 为准
- L0/L2 修改时，L2 优先 → L0 同步精炼
- 这不是"重复"，这是"summary↔detail"

## When to Revisit

1. 如 dogfood 数据（主动收集或 issue 报告）显示 LLM Gate 1 激活率 > 99%
   → 考虑把 happy path 协议从 L0 下移 L1
2. 如 LLM 实测在 L0 借口反驳 4 项之外发现新的高频 rationalization
   → L0 借口反驳表扩充
