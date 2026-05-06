---
decision_id: D21
status: accepted
source_streaming_file: streaming/2026-04-22-cache-choice.md
references:
  - referenced_doc.md
---

# 决策:cache 方案选 Redis (D21)

## Context

需要兼顾 rate limiting 和 cache。

## Decision

采用 Redis(同时作为 rate limiting backing)。

## Rationale

单一 backing 降低运维复杂度;Redis 原生 INCR + EXPIRE 支持 rate limit。

## Alternatives Considered

- **Memcached**
    - rejected_because: "不原生支持 rate limiting"
    - from_source: true
- **Dragonfly**
    - rejected_because: "生态成熟度尚未达 Redis,团队经验少"
    - from_source: false
    - source: ^entry-20260422-05
- **Do Nothing**(保持当前无 cache 状态)
    - rejected_because: "现有数据库压力已超阈值"
    - from_source: true
    - source: ^entry-20260422-01
