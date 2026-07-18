# Cadence 通用语义保真记录设计

## 状态

- 日期：2026-07-18
- 状态：已获方向性批准，等待书面规格复核
- 适用版本：Cadence 0.6 preview 后续版本

## 背景

Cadence 当前用“记 / 整 / 查”三阶段把项目讨论外化到文件：

1. `project-discuss` 把已被用户承接的决定追加到 streaming。
2. `recall-consolidator` 把成熟 streaming 整合为 canonical discussion。
3. handoff 保存短游标，resume 通过索引、哈希和检索恢复上下文。

现有规则已经要求 entry 包含 `chosen + context + options/rejected`，但这个要求主要依赖
模型自检。结构校验只强制 `chosen`，canonical discussion 的 rationale 等正文也允许
缺失。真实 dogfood 因而出现两个相反风险：

- 记录全部讨论会产生大量重复内容、工具日志和无效存储。
- 只保存一句“采用方案二”又无法让新 session 独立理解决定。

本设计解决的是语义保真度，不把 Cadence 变成聊天备份工具。

## 核心约束

### 通用性

Cadence 是通用项目讨论插件，不限定于软件开发、前端、后端或任何技术栈。规则必须
同样适用于：

- 软件、硬件和数据项目；
- 研究、调研和知识整理；
- 写作、内容创作和出版；
- 产品、设计、运营和市场活动；
- 学习计划、课程设计和个人长期项目；
- 其他使用 AI 推进的结构化工作。

任何领域名称都只能作为示例，不能成为固定 schema、唯一触发条件或必填字段。

### 记录边界

- 不保存完整聊天记录。
- 不保存可由产物引用替代的工具日志、测试输出和长文原文。
- 不把尚未被用户承接的探索方案写成既定决定。
- 不因项目属于某个领域而套用固定模板。
- 不依赖用户主动提醒“刚才没有记录详细”。
- 不保存凭证、验证码、令牌、密钥和不必要的个人敏感信息。

### 兼容性

- 旧 `^entry-...` Markdown streaming entry 继续可读。
- 推荐 YAML entry 继续可读。
- 历史档案不要求批量迁移。
- handoff 继续是 15–30 行书签，不扩展为完整档案。
- Claude Code、OpenCode 和 Codex 使用同一套核心语义。

## 设计原则

### 三段式记录判定

#### 1. 承接判定

用户明确确认、选择、继续执行或隐含承接某个方案时，决定进入候选记录范围。用户明确
要求“不记录”时不写入。

#### 2. 持久语义增量判定

只有形成新的稳定项目事实才创建 entry。稳定项目事实包括：

- 目标、范围、非目标或完成标准变化；
- 方案、规则、约束、阈值、顺序或责任变化；
- 状态、关系、依赖、风险或待决问题变化；
- 某个会影响后续讨论的方案被否决；
- 既有决定被实施、撤回、替代或失效。

重复确认、寒暄、过程性推测、未影响最终结论的中间步骤和原始工具输出不创建 entry。
如果是否构成持久增量存在合理不确定性，写 Light entry，而不是要求用户判断。

#### 3. 保真等级判定

承接决定“是否记录”，持久增量决定“是否新建 entry”，影响等级决定“记录多详细”。

保真等级不能由项目类型决定，而由以下通用影响维度决定：

| 维度 | 低影响信号 | 高影响信号 |
|---|---|---|
| 可逆性 | 可轻易撤回 | 难以撤回或不可逆 |
| 影响范围 | 单点、局部 | 跨阶段、跨参与者或跨产物 |
| 损失风险 | 失败代价很低 | 可能造成数据、资金、信誉、隐私或大量时间损失 |
| 持续时间 | 临时选择 | 会约束未来多个 session |
| 外部承诺 | 纯内部 | 涉及用户、客户、公众、法规或合同 |
| 不确定性 | 已知路径 | 假设多、失败模式复杂 |
| 协作复杂度 | 单人单步骤 | 多角色、多系统或多依赖 |

领域示例可帮助模型理解风险，但不得替代上述维度。

## 保真等级

### Light

适用于低影响、可逆、局部的稳定决定。

必需语义：

- `context`：为什么需要这个决定；
- `chosen`：最终决定及其适用边界。

示例：

- 调整一个按钮文案；
- 选择某篇文章的小标题；
- 把一次学习任务从周二移到周三。

### Standard

适用于会影响一个工作阶段、多个产物或后续讨论的决定。

必需语义：

- `context`
- `chosen`
- `rationale`
- `alternatives_or_rejected`（仅在真实讨论过时）
- `dependencies`
- `open_questions`

示例：

- 确定产品功能的默认行为；
- 确定研究样本的选择范围；
- 确定一本书的章节结构；
- 确定营销活动的渠道组合；
- 确定课程的阶段顺序。

### High

适用于高影响、难逆、长周期、外部承诺明显或失败代价高的决定。

High 不使用领域专属大模板，而从以下通用语义槽选择适用项：

- `scope_and_non_goals`
- `actors_and_responsibilities`
- `artifacts_or_entities`
- `rules_and_invariants`
- `states_and_transitions`
- `sequence_and_dependencies`
- `resources_and_limits`
- `access_and_boundaries`
- `failure_and_recovery`
- `retention_and_exit`
- `external_commitments`
- `evidence_and_acceptance`
- `alternatives_considered`
- `open_questions`
- `supersedes`

每个 High entry 必须：

1. 包含 `context`、`chosen` 和 `rationale`；
2. 根据影响维度选择适用语义槽；
3. 用 `not_applicable` 明确列出容易被误认为遗漏、但确实不适用的槽；
4. 不为填满模板而虚构内容。

High 的跨领域示例：

- 软件项目的数据迁移、权限或同步策略；
- 研究项目的伦理边界、样本排除规则和证据门槛；
- 出版项目的版权授权、引用规范和撤稿流程；
- 运营活动的预算上限、审批责任和中止条件；
- 学习项目的考试目标、长期节奏和失败后的调整规则；
- 个人项目涉及隐私、付费、外部承诺或不可逆资源投入的决定。

## 承接式确认

当用户只说“可以”“认可”“方案二”“按你推荐的来”时，记录对象是其承接的最近完整
候选方案，不是这句短回复。

处理步骤：

1. 找到短回复明确指向的最近候选方案；
2. 提取该方案相对于现有档案产生的持久语义增量；
3. 按影响维度选择保真等级；
4. 保存具体规则、边界和理由；
5. 只保存真正讨论过的替代方案，不从方案编号臆测内容。

如果短回复可能指向多个候选方案，先询问用户，不得自行选择。

## 来源与推断

高影响记录应区分内容来源：

- `explicit`：用户或已承接方案中明确表达；
- `synthesized`：对明确内容进行不改变含义的结构化整理；
- `inferred`：模型推断，不能作为用户已确认事实。

`chosen` 不允许仅来自 `inferred`。推断内容应进入 `open_questions` 或明确标注为待确认。

## Streaming Entry

两种表面格式统一解析为内部 `DecisionRecord`：

```text
Legacy Markdown ─┐
                 ├─> DecisionRecord ─> fidelity checks
YAML Entry ──────┘
```

建议的语义模型：

```yaml
entry_id: ^entry-YYYYMMDD-NN
status: accepted
detail_profile: standard
context: ...
chosen: ...
rationale: ...
semantic_slots:
  rules_and_invariants: [...]
alternatives_considered: [...]
dependencies: [...]
open_questions: [...]
supersedes: []
not_applicable: []
provenance:
  chosen: explicit
  rationale: synthesized
```

表面格式可以不同，语义检查必须一致。

## Canonical Discussion 与覆盖关系

每个持续主题应有一个 canonical discussion。Streaming 保存演化历史，canonical
discussion 保存当前稳定真相。

整合器支持：

- `create_new`
- `merge_into_existing`

每次整合必须为所有未撤回 entry 生成 coverage：

```yaml
coverage:
  - source: streaming/topic.md#entry-01
    disposition: incorporated
    section: "Decision"
  - source: streaming/topic.md#entry-02
    disposition: superseded
    superseded_by: streaming/topic.md#entry-05
```

合法 disposition：

- `incorporated`
- `superseded`
- `duplicate`
- `deferred`
- `out_of_scope`

只有所有 entry 都有 disposition，streaming 才能归档。

## 主动整合触发

保留现有话题收尾、上下文阈值和 handoff 触发，并增加：

- 用户明确表达“这块就这样”“继续下一项”等收尾语义；
- 首条 High 决定被承接；
- canonical discussion 已存在且新 entry 改变其当前真相；
- handoff fidelity sweep 发现尚未进入 canonical 的已承接决定。

“entry 少于 2 条”或“文件生成不足 10 分钟”只能跳过未收尾的 Light/Standard 主题，
不能跳过 High 或显式收尾主题。

## Handoff Fidelity Sweep

Handoff 保持短小，但生成前执行：

1. 对账当前 session 中已承接的稳定决定与新 streaming entry；
2. 自动补写范围明确的漏记；范围有歧义时才询问用户；
3. 检查 High entry 的适用语义槽；
4. 确保 canonical discussion 已创建或更新；
5. 验证 coverage；
6. 生成包含 1–3 个 `continuation_refs` 的短 handoff。

新增字段：

```yaml
continuation_refs:
  - path: discussions/topic.md
    sha1: <40 hex>
fidelity:
  status: complete
  uncovered: []
```

## Resume

Resume 在宣布恢复完成前：

1. 验证 `_INDEX.md` 和 `_ACTIVE.md` 哈希；
2. 验证并读取 `continuation_refs`；
3. 使用档案回答冷启动六问：
   - 已决定什么；
   - 为什么；
   - 否决过什么；
   - 哪些约束不能破坏；
   - 哪些问题仍未决定；
   - 下一步是什么；
4. `fidelity.status=partial` 时明确报告缺口，不自行补推；
5. 成功恢复后再清理 pending handoff。

## 校验策略

### 硬错误

- ID、时间戳或状态非法；
- 非墓碑 entry 缺少 `chosen`；
- High 缺少 `context`、`chosen` 或 `rationale`；
- High 的适用槽既未记录，也未列入 `not_applicable`；
- coverage 引用不存在的 entry；
- 归档时仍有 entry 未覆盖；
- `continuation_refs` 路径或哈希非法。

### 警告

- Standard 缺少 rationale；
- 真实讨论过替代方案但没有记录；
- 使用“方案二”但没有具体内容；
- canonical discussion 没有来源引用；
- High 没有 evidence/acceptance。

校验器不使用固定字数判断质量，也不判断某个领域必须出现某个技术字段。

## 测试策略

### 结构测试

- Legacy Markdown 和 YAML 解析为等价 `DecisionRecord`；
- 三种 profile 的必需语义检查；
- coverage 完整性；
- `merge_into_existing`；
- lifecycle trigger 与 validator 一致；
- handoff continuation refs 和 fidelity 字段；
- resume 哈希与降级路径。

### 通用行为 fixtures

至少包含：

1. 软件：详细权限方案后用户只说“认可方案二”；
2. 研究：用户确认样本排除规则和证据门槛；
3. 写作：用户确认章节结构，但未确认具体标题；
4. 学习：用户确认长期节奏和中断恢复规则；
5. 运营：用户确认预算上限、审批人和中止条件；
6. 重复确认不产生重复 entry；
7. 推翻决定产生 supersedes；
8. 未承接 brainstorming 不成为 accepted decision；
9. 长工具输出只记录结论和产物路径；
10. 新 session 只依赖 cadence 档案通过冷启动六问。

### 多运行时矩阵

| 运行时 | Bootstrap 规则 | project-discuss | handoff/resume |
|---|---:|---:|---:|
| Claude Code | ☐ | ☐ | ☐ |
| OpenCode | ☐ | ☐ | ☐ |
| Codex | ☐ | ☐ | ☐ |

不能用一个运行时的结果推断其他运行时。

## 文件范围

预计修改：

- `skills/cadence-bootstrap/SKILL.md`
- `skills/project-discuss/SKILL.md`
- `skills/project-discuss/references/recording-protocol.md`
- 新增 `skills/project-discuss/references/recording-fidelity.md`
- `skills/project-discuss/agents/recall-consolidator.md`
- `skills/cadence-handoff/SKILL.md`
- `skills/cadence-resume/SKILL.md`
- streaming、consolidator 和 handoff validators
- 对应 fixtures 和 tests

不在本批处理：

- 保存原始聊天记录；
- 网络遥测或上传档案内容；
- 批量迁移所有历史项目档案；
- 为不同项目类型建立互斥的专用 schema；
- 新增独立 runtime subagent；
- 改变 Cadence 显式 opt-in 原则。

## 验收标准

1. 用户不再需要提醒“刚才记录得不够详细”。
2. 简单决定保持简洁，高影响决定能够被新 session 独立理解。
3. 非编程 fixtures 与编程 fixtures 使用同一套影响维度和核心流程。
4. Streaming 归档前，每条决定都有明确 coverage。
5. Handoff 保持 15–30 行。
6. Resume 只依靠 cadence 文件即可通过冷启动六问。
7. 两种 streaming entry 格式继续兼容。
8. 三种运行时分别通过验证。
9. 不保存秘密、原始长日志和未承接的探索内容。
