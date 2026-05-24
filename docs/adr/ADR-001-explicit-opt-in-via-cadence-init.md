# ADR-001: Explicit opt-in via cadence-init

**Status**: Accepted
**Date**: 2026-05-22
**Deciders**: hxt9805
**Context**: Architecture review 2026-05-22 (Candidate A grilling Q2)
**Reviewers**: deepseek-V4-Pro (hostile review, 2026-05-22)

## Context

cadence 是一个 session-scoped 的讨论记录 / 整合 / 检索工作流插件。当用户全局
安装 cadence 后，问题是 cadence 何时在某个具体项目中激活。

可能的策略：
- A. **explicit opt-in**：用户必须显式跑 `/cadence-init`，创建
  `cadence/_INDEX.md` marker；SessionStart hook 据此守门
- B. **auto-on**：全局安装即在所有项目生效
- C. **首发激活**：LLM 在 session 首条用户发言时主动询问"要激活吗"

## Decision

采用 A — **explicit opt-in via `cadence-init`**。

## Rationale

1. **不污染非 cadence 项目**：全局插件的最大风险是被不想用的项目误激活。
   显式 marker 把"是否启用"明确成单一信号。
2. **可预测性**：用户/团队清楚知道某项目是否启用 cadence，不依赖 LLM
   启发式判断（C 方案的非确定性）。
3. **零代价沉默**：对未 init 项目，plugin 跟没装一样。
4. **(v2 新加) Context budget 节约**：全局安装但只在部分项目用 cadence 的
   常见 case 下，explicit opt-in 让未启用项目每次 session 启动节省 ~110-130 行
   bootstrap 注入开销 + 后续可能的 project-discuss 加载开销。

## Consequences

**正向**：
+ cadence 不污染非 cadence 项目
+ 是否启用信号清晰（单文件存在性）
+ 没有 false positive 触发
+ context budget 在未启用项目中归零

**负向**：
- 全局安装但忘 init 的用户体验为"插件不工作"（silent）
- 用户须为每个想用 cadence 的项目显式 init

## Considered Alternatives

- **auto-on**：拒绝 — 污染所有项目
- **首发激活**（LLM 主动询问）：拒绝 —
  · LLM 非确定性触发，用户没控制感
  · 触发时机难预测，可能在用户敲第一条话后才询问，体验割裂
  · 已激活项目和未激活项目混在一起，认知负担

## When to Revisit

如 dogfood 数据显示大量用户全局安装后忘 init（silent failure 频发），重新
考虑增加一次性"首次进入未 init 项目时静默提示"机制（不改 opt-in 本质，
只增加发现性，如 SessionStart hook 检测到非 cadence 项目时追加一行
`[cadence 已安装但未在此项目激活。运行 /cadence-init 开始使用。]`）。

**(v2 加) 数据收集 gap**: cadence 当前无遥测。Revisit trigger 暂以
"用户主动反馈"为准。
