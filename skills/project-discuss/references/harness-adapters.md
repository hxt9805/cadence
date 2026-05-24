# Harness 适配（CC / OpenCode / Codex）

> 合并 `codex-tools.md` + `opencode-tools.md`（v0.5）。各 harness 上 LLM 应使用的等价机制。
> **本文档仅在非 CC 形态下相关**；CC 形态用 Task tool / SessionStart hook / `${CLAUDE_PLUGIN_ROOT}` 等原生机制即可。

## § 1. LLM 自适应原则

cadence 最初为 Claude Code 设计，依赖 SessionStart hook、Task tool 自主 fork named subagent、`${CLAUDE_PLUGIN_ROOT}` 路径变量、`/slashcommand` 等 CC harness 能力。OpenCode 通过 `.opencode/plugin/cadence.js` 提供 1:1 等价支持；Codex 通过 `spawn_agent` 5 件套替代。

**原则**：行为契约（输出 contract / token 硬限 / Plan-only / 主 session 唯一写者）跨 harness 一致；仅 fork 机制与路径变量解析需要适配。

## § 2. 6×3 适配表

| 维度 | Claude Code | OpenCode | Codex |
|---|---|---|---|
| Bootstrap 注入 | `hooks/session-start` 脚本 `additionalContext` JSON | plugin `experimental.chat.messages.transform` 注入第一条 user message | 原生 skill discovery（LLM 看 frontmatter 触发调用） |
| Subagent fork | Task tool fork named subagent，CC 自动加载 `agents/<name>.md` | Task tool（plugin `config` hook 预注册 agent），语法与 CC 一致 | `spawn_agent` 5 件套（详 § 3-4） |
| Slash command | `commands/*.md` routing layer | OpenCode 自动从 skill name 生成（`/<skill-name>`） | `$cadence:<skill-name>` 命名空间形式 |
| `${CLAUDE_PLUGIN_ROOT}` | CC 注入 | 无环境变量；按 skill root 相对路径理解 | 无环境变量；symlink 模式下实际路径 `~/.codex/cadence/` |
| Context 上限 | Opus 4.7: **1M** | 取决于底层 LLM（200K–1M） | CLI: 400K（可 clamp 到 272K）；Desktop: 258K |
| `rg` sandbox | 默认允许 | 默认允许 | **默认拒绝**（必须 spawn_agent，不能 fallback `Select-String` / `findstr`） |

## § 3. Codex 调度铁律（强祈使句保留）

Codex 默认 session policy 偏保守（官方："Codex only spawns subagents when you explicitly ask it to"）。**下列三类操作必须走 spawn_agent，禁止主 session 直接读 cadence 档案**：

1. **历史检索 query**（"上次 X 我们怎么定的" / "XX 确定了吗"）→ 必须 `spawn_agent(explorer, message=<wrapped recall-retriever prompt>)`
2. **整合归档**（话题收尾 / context ≥80% / `_ACTIVE.md` 段达阈值 / handoff 兜底）→ 必须 `spawn_agent(worker, message=<wrapped recall-consolidator prompt>)`
3. **决策前回忆分析**（5+ 轮 / 多档案 / 冲突风险）→ 必须 `spawn_agent(worker, message=<wrapped recall-analyzer prompt>)`

**为什么是铁律**：

- Codex App 默认 context ≤400K（CC Opus 4.7 是 1M 的 40%），主 session 直读 cadence 累积必撞顶
- 走 subagent 才能保持 cadence「暗仓库 + context 不膨胀」契约
- subagent 与主 session 共享 filesystem 但 conversation 隔离，输出 consolidated（非全文转录）

**反例（禁止）**：

- ❌ 主 session 直接 `Read cadence/streaming/...md` 或 `cadence/discussions/...md` 答历史检索
- ❌ 主 session 用 PowerShell `Select-String` / `findstr` / bash `grep` 搜 cadence/ 内容（即使 sandbox 拒 `rg` 也不能 fallback — 应改用 `spawn_agent(explorer)`）
- ❌ "刚刚没有 spawn subagent，我只是本地读了几个 cadence 文档" — 这就是协议违例

## § 4. Codex XML message wrapping 模板（必须完整保留）

spawn_agent 调度 cadence subagent 时使用以下 XML 包裹格式（**不压缩为伪代码**）：

```xml
<agent-instructions>
[recall-retriever.md / recall-consolidator.md / recall-analyzer.md 的 body 原文（去掉 frontmatter）]
</agent-instructions>

<task-input>
user_query: <用户原话或主 session 提炼的 query>
current_session_context: <轻量；≤2k tokens；session 内已讨论主题 / 最近 N 轮摘要>
</task-input>

<output-contract>
请按照 agent 文件中「输出 schema（硬性 <500 tokens）」段定义的 yaml 格式返回。
返回 summary + pointers 两段，总 token 数硬性 <500。
</output-contract>
```

### Codex 形态下 3 个 recall-* subagent 的 agent role 选型

| Subagent | Codex agent role | 理由 |
|---|---|---|
| `recall-retriever` | `explorer` | 只读、read-heavy、结构化输出符合 explorer 设计 |
| `recall-consolidator` | `worker` | Plan-only 但需扫多个文件 + 综合 reasoning |
| `recall-analyzer` | `worker` | Plan-only，多档案 + 冲突分析重任务 |

### Codex 命名空间触发语法

| CC slash | Codex 触发 |
|---|---|
| `/cadence-init` | `$cadence:cadence-init` |
| `/cadence-handoff` | `$cadence:cadence-handoff` |
| `/cadence-resume` | `$cadence:cadence-resume` |

> **filesystem 共享 + conversation 隔离**：spawn_agent 派出的 subagent 跟 parent thread 共享 filesystem，但 conversation context 隔离 + 输出 consolidated → cadence「主 session context 不膨胀」契约在 Codex 上比 CC 更必要。

## § 5. OpenCode 形态差异（避免 LLM 误用 Codex 铁律）

OpenCode 跟 CC behavior **1:1 对齐**，**无 Codex 级保守策略**：

- bootstrap 由 plugin `experimental.chat.messages.transform` hook 自动注入到第一条 user message（行为对 LLM 透明；gating 同 CC：项目根有 `cadence/_INDEX.md` 才注入）
- Task tool 语法与 CC 一致；`subagent_type` 字段直接传 `recall-retriever` / `recall-consolidator` / `recall-analyzer`（plugin `config` hook 预注册到 `cfg.agent[]`，agent body 已预加载，**LLM 调用时只传 task input**）
- 不需要"调度铁律" — OpenCode 默认允许 LLM 自主决定何时 fork
- 但 cadence 的"输出 contract（token 硬限 / Plan-only / 只读）"在 OpenCode 上**仍然适用**
- Slash command：OpenCode 扫描 `skills/<name>/SKILL.md` 后自动暴露为 `/<skill-name>`，无需额外配置（`commands/` 目录在 OpenCode 上 not used，保留不影响行为）

**反例（OpenCode 形态下不要套用 Codex 铁律）**：把 Codex 形态的"必须 spawn_agent"祈使句误读为 OpenCode 行为模板 → 错。OpenCode 用 Task tool 即可。

## § 6. 调试 tips

### Codex 形态

- LLM 不主动 spawn → 检查 `~/.codex/config.toml` 是否 `[features].multi_agent = true`；当前模型是否支持 multi-agent（GPT-5.5 / GPT-5.4 支持）
- spawn 后超 500 tokens → 检查 message `<output-contract>` 是否清晰传达硬限
- Codex App sandbox 拒 `rg` → 这不是走捷径用 `Select-String` 的借口，正确做法 `spawn_agent(explorer)`
- "agent role not found" → 检查名拼写（必须是 `default` / `worker` / `explorer` 之一）

### OpenCode 形态

- `Unknown agent type: recall-retriever` → plugin `config` hook 没生效。检查 `opencode.json` `plugin` 数组、`opencode run --print-logs` 看 plugin 加载日志
- subagent 行为不对（如 retriever 写文件 / 超 500 tokens）→ 让 subagent 自我介绍硬边界、对照 `agents/<name>.md` 核验
- `/cadence-*` 命令不可见 → 确认 plugin `config.skills.paths` 注入成功（启动日志列出扫描的 skill 目录）
- bootstrap 没自动注入 → 确认项目根有 `cadence/_INDEX.md`（gating 条件）；未 init 需先跑 `/cadence-init`
