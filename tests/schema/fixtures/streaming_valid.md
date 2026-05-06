---
topic: 测试主题
started: 2026-04-21T14:30:00+08:00
status: active
last_entry: ^entry-20260421-02
---

^entry-20260421-01 [2026-04-21T14:30:22+08:00] cache 方案选 Redis
  context: 需要兼顾 rate limiting 和 cache
  options: [Redis, Memcached]
  chosen: Redis
  rejected:
    - Memcached: 不原生支持 rate limiting

^entry-20260421-02 [2026-04-21T14:35:00+08:00] 加 TTL 限 5 min
  context: Redis key 无限堆积
  chosen: TTL=300s
