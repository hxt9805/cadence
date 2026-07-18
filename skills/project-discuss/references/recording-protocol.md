# 记录协议细则（v0.4 / v0.5 incident 合并）

> project-discuss skill 的记录行为遵循本协议。本文件是 skill 的内部行为细则，
> 指导 Claude 何时、如何、记录什么。
>
> **v0.5 调整**：三段式记录判定 + profile-aware 语义保真 + 3 Phase（记 / 整 / 查）+ 共享行为 + 边界 + 历史脉络 + **incidents 附录**（v0.5 合并自 `incident-handling.md`）。
> 借口反驳 #1/#2/#4/#5 已上移 L0 `cadence-bootstrap/SKILL.md` §8；#3 上移 L1 `project-discuss/SKILL.md` §4。
> 影响分级、通用语义槽、承接短句与冷启动检查的权威源是 `recording-fidelity.md`。

## 导航

- §1 三段式记录判定 / §2 记 阶段（含信息密度正反例 + dual schema）/ §3 整 阶段 / §4 查 阶段
- §5 共享行为 / §6 边界与禁忌 / §7 历史脉络
- **§8 Incidents 附录**（bug / 事故 / tricky fix 记录细则，v0.5 合并自 `incident-handling.md`）

---

## 1. 三段式记录判定

```text
承接决定是否记录
持久语义增量决定是否新建 entry
影响等级决定记录多详细
```

### 承接

承接对象覆盖“结论 OR 中间决定”。用户明确或隐含确认过，才可能写成 accepted：

| 内容类型 | 记？ | 说明 |
|---|---|---|
| 用户对结论的承接（"嗯，就用 PostgreSQL"） | ✅ | 不变 |
| 用户对中间决定的承接（"嗯，先排除 C"） | ✅ | **v0.4 扩展** |
| LLM 推断的"这条有未来价值" | ❌ | 不能写成用户已承接 |

### 持久语义增量

承接后再判断是否出现稳定变化。目标、范围、非目标、规则、顺序、边界、状态、关系、
依赖、风险、真实否决项或下一步发生变化时新建 entry；重复确认已有记录不重复写。
判断存在合理不确定性时写 Light entry，不假设内容以后会再次出现。

### 影响等级

按可逆性、影响范围、损失风险、持续时间、外部承诺、不确定性和协作复杂度选择
**Light / Standard / High**。领域名称只可作示例，不能决定 profile 或固定 schema。
详细字段与例子见 `recording-fidelity.md`。

### 未命中 → 不记

- 闲聊 / 脱题 / 随口尝试未被用户承接
- 脑暴中未被拍板的选项（等承接再记）
- 用户明确"别记"

---

## 2. 记 阶段（Phase 1: Record）

记 阶段（流式记录）——决策承接瞬间主 session 直写。

### 触发条件

承接且形成持久语义增量（§1）→ 立即写，不等用户说“记下”。

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

### Profile-aware 保真度

- Light：至少 `context + chosen`
- Standard：Light + `rationale`，并记录真实存在的取舍、依赖和待决问题
- High：`context + chosen + rationale` + 适用的通用语义槽；明确不适用的关键槽可列入 `not_applicable`

不得为了填模板虚构理由、替代方案或外部承诺。用户仅以“可以”“方案二”等短句承接时，
必须回溯完整方案并记录其稳定语义，不能把短句本身当作 `chosen`。

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
  chosen: <选中方案及适用边界>
  rationale: <选择理由；Standard / High 必填>
  rejected:
    - <方案 B>: <原因>
```

- **基础必填**：entry id（seq 从 01 起两位递增）、ISO-8601 带时区时间戳、摘要（≤60 字符建议）、`context`、`chosen`
- **按 profile 必填**：Standard / High 的 `rationale`；High 还需适用的语义槽或 `not_applicable`
- **按事实选填**：options / rejected / dependencies / open_questions / provenance
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

### Schema 兼容性（v0.5 dual schema）

新 entry 推荐使用 YAML frontmatter + markdown body 格式（详 L0 `cadence-bootstrap/SKILL.md` §5a）；旧 markdown 段落格式（本节上方 `^entry-` 行首形式）**仍然合法**。LLM 是 polyglot reader，两种格式都能被下游消费者（`recall-consolidator` / `recall-retriever`）正确读取。

**dogfood 实证**：profile-aware 语义保真度比 schema 形式更重要；两种格式都必须满足
`recording-fidelity.md` 的 Light / Standard / High 要求。

### 记阶段绝不做的事

- 未被承接的未来价值判断（留整合阶段）
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
| 「记一下」/「记录」 | **必记**；仍按持久语义增量选颗粒度、按影响等级选 profile |
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

## 7. 历史脉络

| 版本 | 核心变化 |
|---|---|
| **v0.2.1** | 取消"每条征询 Y/N"，回归自主记录 + 事后告知（Trueprint 原意） |
| **v0.2.2** | 引入快速通路 / 完整通路双通路 + `recall-analyzer` fork 契约 + 三分类措辞契约 |
| **v0.3** | 双判据降为单判据（删"未来价值"）；快速/完整通路 → 三阶段（α/ε/ρ）；recall-* 扩为三 subagent |
| **v0.4** | α/ε/ρ → 直白命名（记/整/查）；散装 13 节 → 8 节 Phase 化骨架；承接对象扩展（覆盖中间决定）；强 schema 降建议（status 仍必填）；借口反驳表新增 |

v0.3 design doc（`docs/design/2026-04-21-project-discuss-v0.3-design.md`）保留 α/ε/ρ 原命名作历史脉络，v0.4 起协议层统一使用"记 / 整 / 查"。

---

## 8. Incidents 附录（v0.5 合并自 incident-handling.md）

> Incidents = bug / 事故 / tricky fix 等需要留档的"意外事件"。本节是 §2-§4 三阶段在 incident 场景的特化模板。
> v0.5 起 `incident-handling.md` 已合并入本附录；主体协议（三段式判定 / 三阶段 / recall-analyzer）见 §1-§6。

### 触发条件

以下场景下应考虑 incident 记录：

- 用户修复了一个 bug
- 发生了生产事故 / 回归
- Performance 问题被解决
- Tricky 的代码修改（修复逻辑非显而易见）
- 揭示了既有架构或设计问题的修改

### 三段式判定 + 承接信号（incident 特化）

按 §1 先判断承接，再判断是否形成值得独立记录的持久语义增量，最后选择 profile。
incident 场景的承接典型信号：

- 用户说"修好了" / "问题解决了" / "可以了"
- 用户基于修复推进后续工作（"那我接着做 X"）
- 修复 commit 已落盘 + 用户转向新话题

**根因未明时**：先记简版 entry，`context` 标"根因待查"，后续讨论继续 append 新 entry 补全（append-only 铁律 — 不修改已有条目）。

**通常不形成独立语义增量的 bug**：纯 typo、显而易见的一次性修正、或现有产物引用已足够恢复语义且没有新增规则/风险/约束。这类不必新建 incident entry；如果存在合理不确定性则写 Light。已写入 streaming 的低影响修复可由整阶段决定不产出独立 incident doc。

### 记 / 整 / 查 在 incident 场景的特化

- **记 阶段（§2）**：写 streaming entry 到 `cadence/streaming/<YYYY-MM-DD>-<incident-slug>.md`，`context` 记症状 + 根因（若已明），`chosen` 记修复方案，`rejected` 记被排除的候选修复（若有）
- **整 阶段（§3）**：consolidator 判定是否产出独立 incident doc。有留档价值（涉及候选 / trade-off / 改动大 / 揭示架构 / 可能复发）→ `cadence/discussions/incidents/YYYY-MM-DD-简述.md`；低价值（typo / 一次性）→ 不产出独立 doc，只保留 streaming entry
- **查 阶段（§4）**：用户问"上次类似 incident 怎么处理" → fork `recall-retriever` 检索 `discussions/incidents/` + `_archive/`

架构级 incident 除 incidents/ doc 外，consolidator 可能在 `_ACTIVE.md` 活跃决策追加修正条目。

### Incident doc 模板

#### 完整模板（涉及候选方案 + trade-off / 改动大 / 揭示架构问题）

````markdown
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
````

#### 摘要模板（单一修复 / 改动小 / 备忘性质）

````markdown
# [YYYY-MM-DD] 简短描述

## 症状
...

## 修复
- 改动文件：...
- 关键逻辑：...
````

### 整合后的 archive 维护

整 阶段（§3）产出 incident doc 后，同一两阶段写流程中：

1. 更新 `cadence/_ACTIVE.md` 的「最近讨论」表格，添加一行：

   ```
   | YYYY-MM-DD | [incident] 简述 | 根因+修复一句话 | incidents/YYYY-MM-DD-xxx.md |
   ```

2. 架构问题 → 可能在 `_ACTIVE.md`「当前活跃决策」追加修正
3. 值得让 Claude 今后警示 → 加到 `_INDEX.md` 话题词典

### 不记录的情况

- 用户还在处理中（未被承接 → 等承接）
- 用户明确说「这个太琐碎，不记」
- 同一天内已记过类似（**不修改已有 entry**，append 新 entry 注明"关联 ^entry-xx"；整 阶段时合并）
