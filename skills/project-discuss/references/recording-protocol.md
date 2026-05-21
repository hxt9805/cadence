# 记录协议细则（v0.4）

> project-discuss skill 的记录行为遵循本协议。本文件是 skill 的内部行为细则，
> 指导 Claude 何时、如何、记录什么。
>
> **v0.4 现状**：单判据「已被承接」+ 3 Phase（记 / 整 / 查）+ 共享行为 + 边界。
> 散装 13 节 → 8 节骨架，瘦身 30%。

---

## 1. 记录单判据

**唯一判据：「已被承接」**（用户明确或隐含确认过）。

### v0.4 承接对象扩展

判据本身不变，但**承接对象**从"结论"扩展到"结论 OR 中间决定"：

| 内容类型 | 记？ | 说明 |
|---|---|---|
| 用户对结论的承接（"嗯，就用 PostgreSQL"） | ✅ | 不变 |
| 用户对中间决定的承接（"嗯，先排除 C"） | ✅ | **v0.4 扩展** |
| LLM 推断的"这条有未来价值" | ❌ | 不引入"未来价值"判据 |

**关键**：仍只判**用户承接信号**，不判未来价值。未来价值留给整合阶段（Phase 2）consolidator 处理。

### 未命中 → 不记

- 闲聊 / 脱题 / 随口尝试未被用户承接
- 脑暴中未被拍板的选项（等承接再记）
- 用户明确"别记"

---

## 2. 记 阶段（Phase 1: Record）

记 阶段（流式记录）——决策承接瞬间主 session 直写。

### 触发条件

判据命中（§1）→ 立即写，不等用户说"记下"。

隐含承接信号（详见 §5 共享行为）：
- **强信号**：「嗯」「好」「OK」+ 跟在决定后；用户基于此前提推进后续；用户引用此决定推后续行动
- **弱信号（不算）**：沉默、反问、只听不评、转话题

### 落点

| 内容类型 | 写到哪 |
|---|---|
| 用户承接的结论级决策 | `_ACTIVE.md` 活跃决策 |
| 用户承接的中间决定（暂时性、待推进的） | `streaming/<YYYY-MM-DD>-<topic-slug>.md` |
| 用户承接的"先放着"话题 | `_ACTIVE.md` 待决 |
| 大任务跨 session 进度点 | `streaming/<topic>.md` |
| 完整 reasoning / trade-off | `discussions/<date>-<slug>.md` |
| Bug/incident | `discussions/incidents/YYYY-MM-DD-简述.md` |

### 写入原则：假设读者无上下文

entry 会被下游 session（另一个 LLM、另一个讨论话题）读取。写入时假设读者对本次 session 的讨论内容**一无所知**：

- `chosen` 包含足够特异性，读者无需猜测即可理解决策
- 涉及技术规格时，写出类型/签名/约束——不依赖"项目其他文件里有"
- 如果决策依赖某现有系统约束，在 `context` 中注明该约束

特异性 ≠ 冗长：一行含类型签名的 `chosen` 优于一段散文式 reasoning。

#### 信息密度正反例

下面是**同一个决策**在不同密度下的写法。下游读者（另一个 LLM）只能看到 entry 本身——没有本 session 的上下文。

❌ **密度过低**（下游无法理解决策意图）：

```
^entry-20260521-01 [2026-05-21T12:33:00+08:00] 教学入口按钮
  chosen: 用「开始学习」按钮
```

读者看到这条 entry 无法回答：哪个产品？为什么是按钮？讨论中排除了什么？

✅ **密度足够**（下游可独立理解）：

```
^entry-20260521-01 [2026-05-21T12:33:00+08:00] 教学入口用「开始学习」按钮（非自动触发）
  context: 教学模式 UX 设计访谈中讨论"首次进入"入口形态；担心自动触发导致用户误启动 session
  options: [显式按钮触发, 自动进入教学, 弹窗询问]
  chosen: 显式「开始学习」按钮 — 用户点击后创建 session + AI 发开场白
  rejected:
    - 自动进入教学：用户路过页面就启动 session
    - 弹窗询问：多一步骤打断流程
```

读者通过 `context` 知道场景；通过 `options` + `rejected` 知道决策路径；通过 `chosen` 的细节知道实现意图。

### Schema

#### 文件 front-matter（每文件一份）

```yaml
---
topic: <人类可读主题>
started: <ISO-8601 TZ>
status: active | archived
superseded_by: discussions/<date>-<slug>.md   # 整合后写入
last_entry: ^entry-<id>                        # 每次追加时更新
---
```

#### Entry schema（必守）

每条 entry 从行首 `^entry-` 开始，不可缩进：

```markdown
^entry-<YYYYMMDD>-<seq> [<ISO-8601 TZ>] <一句摘要>
  context: <前提/场景>
  options: [A, B, C]
  chosen: <选中方案>
  rejected:
    - <方案 B>: <原因>
```

- **必填**：entry id（seq 从 01 起两位递增）、ISO-8601 带时区时间戳、摘要（≤60 字符建议）、`chosen`
- **选填**：context / options / rejected
- **options 硬约束**：必须 inline flow 形式 `options: [A, B, C]`，不支持多行 list

#### Tombstone（撤回用）

**append-only 铁律**：永不修改已有条目。撤回追加 tombstone：

```markdown
^entry-20260421-04 [2026-04-21T14:35:00+08:00] 撤回 ^entry-20260421-03
  ref: ^entry-20260421-03
  reason: 用户重新审视后改用 Dragonfly
```

tombstone 必有 `ref` + `reason`。订正（错字等）同理：追加新 entry + 注明"订正 ^entry-xx"。

### 输出（告知格式）

写入后立即一行告知：

```
📝 已记：<摘要> → streaming/<file>.md#<entry-id>
```

详细告知格式见 §5 共享行为。

### 记阶段绝不做的事

- 未来价值判断（留整合阶段）
- 合并 / 去重（留整合阶段）
- ADR 化（留整合阶段）
- 修改已有条目（铁律 append-only）

---

## 3. 整 阶段（Phase 2: Consolidate）

整 阶段（整合）——把 streaming 条目整理为 archive，清理 `_ACTIVE.md`。

### 触发条件（v0.4）

**主触发**（v0.4 = spec § 5.1.2 列 3 类 + v0.3 兼容 2 类，共 5 类）：
- `trigger_reason: section_70` — 任一段达 70% 软警告 *(v0.4 新增)*
- `trigger_reason: section_100` — 任一段达 100% 硬阈值（v0.3 行为兜底）*(v0.4 新增)*
- `trigger_reason: mtime_change` — 文件 mtime 异常变化（外部 edit）*(v0.4 新增)*
- `trigger_reason: handoff_sweep` — handoff 兜底（v0.3 兼容）
- `trigger_reason: llm_initiated` — LLM 自判时机（话题收尾 / 30min 停滞 / context ≥80% / ADR 结构已全 — v0.3 兼容）

**冷启动兜底**（低优先）：
- `trigger_reason: cold_n_rounds` — 主 session 每 N=20 轮无主触发命中时触发一次
- 用途：`_ACTIVE.md` 没满但条目老化（如已实施的决策半年无动静）也能被清理

**触发流程**：
1. 主 session 检测 trigger 条件
2. 收集 lifecycle_params（轮数计数器 / recent_user_turns / git log window）
3. Fork consolidator 传入
4. 接收 yaml plan + 执行（详见下方「流程（主 session 视角）」节）

> 完整 lifecycle_params 传入约定见 `SKILL.md` § 3「主 session 工作记忆」 及 `agents/recall-consolidator.md` § 输入 schema。

### 流程（主 session 视角）

1. Fork `recall-consolidator`（Plan-only；见 `agents/recall-consolidator.md`）
2. 接收 yaml plan
3. **Step 1 — Write**：Write `discussions/<date>-<slug>.md`
4. **Step 2 — Validate**：读回校验（gate：通过才继续）
5. **Step 3 — Archive**：Edit streaming front-matter（`status: archived`）+ Append tombstone
6. 下次用户发言前输出整合完成通知

**关键不变量**：streaming tombstone 只在 discussion doc 验证存在后追加。Step 2 是 gate，未通过绝不进入 Step 3。

### ADR doc 结构（建议级）

front-matter：
- `status: accepted | superseded`（**必填**）
- `decision_id`（建议）
- `source_streaming_file`（建议）
- `references`（建议）

body（建议四节）：`## Context` / `## Decision` / `## Rationale` / `## Alternatives Considered`

**v0.4 调整**：status 仍必填，其他字段从"必填"降为"建议"。现有 v0.3 ADR doc 仍合法。

### 失败模式

- Step 1/2 失败 → 日志告知 + streaming 保持 active（下次触发重试）
- subagent 返回 `failed` → 日志告知 + 不破坏档案
- 不做自动恢复

---

## 4. 查 阶段（Phase 3: Retrieve）

查 阶段（跨 session 检索）——新 session 或需要历史时，派 retriever 只读检索，**主 session context 不膨胀**。

### 触发条件

- 用户问历史决策 / 之前讨论过的话题
- 主 session 不确定某历史是否有记录
- 4 trigger 主动重读（详见 `references/query-behavior.md`）

### 流程

1. Fork `recall-retriever`（只读；见 `agents/recall-retriever.md`）
2. 传入：`user_query` + 轻量 `current_session_context`（≤2K tokens）
3. 接收输出：`summary`（1-3 句）+ `pointers[]` + `confidence`（**总 <500 tokens 硬限**）
4. 主 session 向用户呈现 summary + pointers；需深入时主动 Read 对应 pointer 文件

### 失败模式

- 无匹配 → 明确告知"未找到相关历史记录"，`confidence: high`（确认没有，不是找不到）
- `failed` → 告知用户 + 建议手工关键词复查
- **绝不基于空返回瞎编**

---

## 5. 共享行为

### 隐含确认

隐含确认是"用户没显式说'定了'但实质上已承接"的情况。这是自主记录的核心判据。

**强信号（一般可视为已承接）**：
- 接受性表态：「嗯」「好」「可以」「没问题」「OK」
- 基于此前提推进后续（说明 X 已当既定前提）
- 提出基于此决策的后续行动
- 在新决策中引用已讨论的 X

**弱信号或反信号（不算承接）**：沉默、反问质疑、只听不评、转话题。

清单外：综合上下文判断"用户是否已把这条当既定前提在推进"。不确定时倾向**不记**，等更明确信号再补。

### 决策被推翻

用户改主意（"刚才 X 我想改"）：

1. 直接覆盖活跃决策（不留两条并存）
2. 对应 discussion 文档留一行变更原因
3. 不必留旧版归档（归档是给超 30 天历史用的，不是版本控制）

例外：用户明确说"把旧版留个档" → 按用户意图处理。

### 撤销

用户说「刚才那条别记 / 撤回 / 删了 / 忘掉 X」：

1. 立即撤销：streaming 中追加 tombstone entry（append-only，不物理删）
2. 一行告知"已撤"
3. 本 session 内不再就同一话题主动提起

### 用户显式信号优先

用户显式信号**永远覆盖**以上所有规则：

| 信号 | 行为 |
|---|---|
| 「记一下」/「记录」 | **必记**，不判断单判据 |
| 「别记」/「不用记」 | 不记，本 session 不再主动提 |
| 「撤回」/「忘掉 X」 | 立即撤 + 一行告知 |
| 「改 X 为 Y」 | 覆盖记录 + 一行变更原因 |

### 告知格式

- 一句话摘要 + 路径 pointer
- 仅当有结构级动作（新建目录 / 推翻决策 / 跨文档）才加第三行
- 告知让用户有知情权，不是请求确认

**简约示例（默认）**：
```
📝 已记：Redis 做 cache（备选 Memcached）→ `_ACTIVE.md` 活跃决策
```

**完整示例（有结构动作时）**：
```
📝 已记：Redis 做 cache → `_ACTIVE.md` + `discussions/03-cache/...`
  ↳ 新建 `03-cache/` 主题目录（存完整 trade-off）
```

**短时连续多条**：合并汇报（"`📝 已记 3 条：...`"）。

**禁用**：长篇复述已记内容；索取确认式追认；缺 pointer；每次同一模板。

**颗粒度**：明示超出原授权范围的部分（如"顺便补齐 Y/Z 两条 pointer"）。顺手整理须事后明示。

### 三分类措辞契约（反 Hallucination）

决策前回忆分析呈现必须明确区分三类信息：

| 分类 | 措辞 | evidence 要求 |
|---|---|---|
| **你说的** | "你在 [session 第 N 轮] 说过 ..." | **必带对话编号** |
| **档案有的** | "档案里 [文件路径] 写了 ..." | **必带文件路径** |
| **我推断的** | "我推断 ...（依据：[第 M 轮你说 X] + [档案 Y 有 Z]）" | **必带依据 pointer** |

禁用：「可能」「应该」「大概」「似乎」等模糊认知声明；不带 evidence 的补全。

---

## 6. 边界与禁忌

### 授权扩张分级

**低风险（顺手做 + 事后明示）**：补齐话题词典 pointer；格式一致性整理；关联决策 pointer 链接；修正明显错别字。

**中风险（事前征询）**：修改用户已写内容；跨多个 discussion 文档的大改动；删除档案条目。

**高风险（完全禁止）**：改源代码；改 `.env` / 配置；写越出 `cadence/` 的文件（`CLAUDE.md` cadence fragment 管辖域除外）。

清单外：按"影响半径 + 可逆性"两维判断。影响半径大 / 不可逆 → 升一级。

### Subagent 写档案禁令

**不允许** subagent 直接写档案。三个 recall-* subagent 共享 **Plan-only / 只读输出契约**，主 session 是唯一写入者。

### 通路关系

| Phase | subagent | 时机 | 写权限 |
|---|---|---|---|
| 记（Phase 1，主 session 直写） | 无 | 决策承接瞬间 | 主 session 写 streaming/ |
| 整（Phase 2，Phase B 启用） | `recall-consolidator`（Plan-only） | LLM 自判 / handoff 兜底 | 主 session 执行写 |
| 查（Phase 3） | `recall-retriever`（只读） | 跨 session 查询 | 只读 |
| 决策前回忆分析（v0.2.x 保留） | `recall-analyzer`（Plan-only） | 5+ 轮 / 多档案 / 冲突风险 | 主 session 执行写 |

---

## 7. 借口反驳表

| # | 借口 | 反驳 |
|---|---|---|
| 1 | "这个 session 已经在用 brainstorming，project-discuss 应该被覆盖" | brainstorming 管探索过程，project-discuss 管档案落地，**两者职责正交**，必须并行 |
| 2 | "用户没明确说要记，我先不记" | 单判据"已被承接"的承接对象已扩展（覆盖中间决定）——只要用户有承接信号（如"嗯，先排除 C"），**不用等用户说"记下"** |
| 3 | "上限到了再问用户怎么归档" | 70% 软警告时 consolidator 已经静默处理了，**不要等到 100%** |
| 4 | "概念太多，我先简化执行" | 协议**已经简化到 3 Phase**——如果还觉得难记，回头读 SKILL.md，不要凭印象执行 |
| 5 | "这条决策不重要，先不写 archive" | archive 是暗仓库——但判断"不重要"的标准是是否有承接信号，而非主观感觉；真有噪音风险，整合阶段会处理 |

---

## 8. 历史脉络

| 版本 | 核心变化 |
|---|---|
| **v0.2.1** | 取消"每条征询 Y/N"，回归自主记录 + 事后告知（Trueprint 原意） |
| **v0.2.2** | 引入快速通路 / 完整通路双通路 + `recall-analyzer` fork 契约 + 三分类措辞契约 |
| **v0.3** | 双判据降为单判据（删"未来价值"）；快速/完整通路 → 三阶段（α/ε/ρ）；recall-* 扩为三 subagent |
| **v0.4** | α/ε/ρ → 直白命名（记/整/查）；散装 13 节 → 8 节 Phase 化骨架；承接对象扩展（覆盖中间决定）；强 schema 降建议（status 仍必填）；借口反驳表新增 |

v0.3 design doc（`docs/design/2026-04-21-project-discuss-v0.3-design.md`）保留 α/ε/ρ 原命名作历史脉络，v0.4 起协议层统一使用"记 / 整 / 查"。
