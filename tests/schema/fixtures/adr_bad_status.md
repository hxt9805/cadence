---
decision_id: D20
status: draft
source_streaming_file: streaming/2026-04-21-handoff-redesign.md
references: []
---

# 决策:handoff 从"备份"改为"书签" (D20)

## Context

handoff v0.2.2 流水账膨胀,新 session 难续。

## Decision

handoff 改为 15-30 行 schema,游标 + soft context。

## Rationale

streaming 已持久化讨论内容,handoff 只需游标。

## Alternatives Considered

- **保持 v0.2.2 五类提取**
    - rejected_because: "体量不可控"
    - from_source: true
    - source: ^entry-20260421-03
