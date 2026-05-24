# 查询行为规则

> project-discuss 在用户询问项目现状、架构、历史、决策时按本规则工作。本文件是 skill 的内部行为细则，指导 Claude 如何高效、可靠地回答查询。

## 查询优先级

### 对事实性问题（用什么版本、有哪些模块、如何配置）

优先级：**代码 > cadence 档案 > 手写文档**

```
1. 查 cadence/_INDEX.md + cadence/_ACTIVE.md 和 cadence/discussions/
2. 如果档案里有答案：
   - 来源 L1/L2（代码/自动扫描） → 直接答
   - 来源 L3（cadence 讨论） → 答 + 注明“这是档案意图”
   - 来源 L4（README、docs/） → 读一眼代码复核，再答
3. 如果档案里没有：
   - 读代码/配置回答
   - 征询是否补档
```

### 对意图性问题（为什么选 X 不用 Y、设计初衷）

优先级：**cadence 讨论记录 > 手写设计文档**

```
1. 查 cadence/discussions/（尤其最近活跃决策）
2. 查 cadence/_INDEX-HISTORY.md（历史讨论）
3. 查 cadence/_archive/（老归档）
4. 查项目 docs/（如 architecture.md），但声明“这是文档里的原始意图，
   是否仍成立需要你判断”
```

## 加载策略（防止 context 膨胀）

### 第 1 步：总是先读轻量入口

默认只读 `cadence/_INDEX.md`（纯索引，< 800 tokens）。

### 第 2 步：第一次需要活跃状态时读 `_ACTIVE.md`

`_ACTIVE.md`（~1800 tokens）含活跃决策、待决、TODO、最近讨论。
**Session 内读一次进 context 即可**（默认不重读，见下方"4 trigger 主动重读"节）。

### 第 3 步：判断是否需要更多

- 用户问的话题在「话题词典」里 → 按 pointer 直接读对应 discussion 文档
- 用户问**近 14 天**的话题 → `_ACTIVE.md` 的「最近讨论」能覆盖
- 用户问**更早**的话题 → 读 `_INDEX-HISTORY.md`
- 用户问**30 天前**的话题 → 读 `_archive/YYYY-MM.md`
- 用户需要完整文档列表 → 读 `_INDEX-DOCS.md`

### 第 4 步：需要具体文档内容时

- 从 `_INDEX-DOCS.md` 定位具体文档
- 或通过话题词典的 pointer
- 直接 Read 读

#### 查 阶段（v0.3/v0.4 升级）:档案检索派 retriever(柱 3)

- 当用户查询的内容范围**超出 `_INDEX.md` 话题词典能直接命中**的范围(如跨主题 / 历史决策 / 归档内容)
  → **不要主 session 直接 Glob/Grep 全 archive**(会膨胀 context);
  → **fork `recall-retriever`**,让它在独立 context 里检索,返回 <500 tokens 摘要 + pointers
- retriever 返回后:
  - `confidence: high` + pointers 命中 → 按 pointer Read 具体文件回答
  - `confidence: medium/low` → 先告知用户"可能相关的记录",由用户确认再深入
  - 空 pointers + high confidence → 告知"档案确实无此记录"
- **触发阈值**:查询范围跨 ≥2 discussion doc / 涉及 >14 天前决策 / 用户明说"之前" → 直接派 retriever

## 代码复核的时机

以下情况即使档案有答案也要读代码验证：

- **档案来源是 L4**（手写文档）
- **档案信息距今 > 30 天**且是关键事实
- **用户问到 inconsistencies 标记为关键的条目**（从 `01-inconsistencies.md`）
- **用户即将基于答案做决策**（比如"那我就用 X 了"）

## 冲突处理

如果档案说法和代码复核结果不一致：

```
档案说 X（来源：cadence/discussions/05-tech/database.md）
但我查代码发现是 Y（package.json）。
文档可能过时，要以代码为准更新档案吗？
```

## 新信息的补档征询

每次“现场读代码得到的结论”都是补档机会：

```
这个信息档案里没有。要记到 cadence/discussions/ 吗？下次就能直接查。
[Y/N]
```

## 历史决策遗忘场景

用户问「我们之前这个功能怎么决定的？」：

```
1. 查 cadence/discussions/ 相关文档
2. 若无，查 _INDEX-HISTORY.md
3. 若还无，查 _archive/
4. 若还无，查 git log + commit messages
5. 整合后回答
6. 提议："这个过程似乎没完整记档，要补上吗？"
```

## 查询行为的克制

**不记录查询本身**。用户问完就完了，除非产生新信息或修正既有档案。

## 修改/扩展类动作前的查询前置（v0.2.2）

### 核心判据

用户发言的**主体对象**（名词，不是动词）是否可能已在项目档案里？
是 → 查询前置；不是（纯技术 / 外部 / 无关）→ 不查。

### 典型场景（非穷举）

**应查（对象是项目内资产）**：

- 提到具体技术栈 / 模块 / 功能名："改 Auth"、"优化 Postgres 查询"
- 提到可能关联已有决策的新动作："加刷新 token"（关联 Auth）
- 提到项目概念的泛化："聊聊我们的认证方案"
- 对话上下文已指向具体模块的泛指："这里重构一下"

**不查（对象不在项目域内）**：

- 纯技术问答："React hooks 怎么用"
- 外部知识："K8s 学习路径"
- 明显闲聊

**边缘（靠 judgment）**：

- 抽象主体："代码重构一下"——看对话上下文，有具体对象就查，没有就**反问澄清**

### 清单外的情况

按"对象 × 是否项目内"两维判断。注意是**对象判据**（名词），不是动词清单——清单死板匹配会丢失"用户提到 Auth 但用动词'看看'"这类合法触发。

### 倾向

**宁可多查一次（确认"没有就没有"）> 漏查（把已有当新的处理）**。多查成本 ≤ 2000 tokens；漏查成本 = 丢失历史 + 重复讨论 + 决策冲突。

## 4 trigger 主动重读（v0.2.2）

默认：**不重读**（读一次进 context，session 内 Claude 自己知道它写了什么）。

### 触发主动重读的 4 种信号

① **用户明确问状态 / 历史**（"XX 确定了吗"、"我们之前怎么决定的"）
② **Session 轮数 > 100 / 跨越时间长**（context 可能模糊）
③ **检测到文件被外部修改**（git status / modified time 变化 / 用户告知"我刚改了 X"）
④ **Claude 自觉"记忆模糊"**（允许自判）

### 重读策略

**优先 diff**（git diff 或 context 内比对），**不读全文**。
仅 ③ 外部修改才可能需要重读全文（diff 显示大段变化时）。

### 不要的

- 每轮都重读 `_INDEX.md` / `_ACTIVE.md`（context 已有，重读浪费 token）
- 没有明确 trigger 主动重读（焦虑驱动而非价值驱动）

---

## 路由表管理

> 当项目 discussion 文档数量增多时，用语义路由表帮 Claude 快速定位。

### 何时引入路由表

- 0-10 个 discussion 文档 → **不需要**路由表，`_INDEX.md` 话题词典足够
- 10+ 个文档 → 建议创建 `cadence/discussions/_INDEX-ROUTING.md`

### 路由表格式

`cadence/discussions/_INDEX-ROUTING.md`：

```markdown
# 语义路由表

> 按主题标签分组，Claude 根据用户提问快速定位文档。

## 架构与设计
- database-choice.md — 数据库选型
- api-design.md — API 设计规范
- deployment-strategy.md — 部署策略

## 技术栈选型
- frontend-stack.md — 前端技术栈
- backend-stack.md — 后端技术栈

## 业务逻辑
- user-flow.md — 用户流程
- billing-logic.md — 计费逻辑

## Incidents 档案
见 incidents/ 子目录（按日期）

## 历史归档
见 _archive/ 目录（按月）
```

### 生成与维护

**自动生成（Claude 行为）**：文档数超过 10 后，首次触发 project-discuss 时提议：

```
你有 X 个讨论文档了，要不要生成一份语义路由表？
我可以根据文档表格的标签列自动分组，写入 _INDEX-ROUTING.md。
[Y/N]
```

用户同意 → 从 `_INDEX-DOCS.md` 读取所有文档的 tag 列，分组生成。

**手动维护**：用户可随时手动编辑 `_INDEX-ROUTING.md`，Claude 读取它作为权威分组。

### 话题词典 vs 路由表

| 项目 | 存在位置 | 维护方式 | 覆盖范围 |
|---|---|---|---|
| 话题词典 | `_INDEX.md` 底部 | 每次记录后 Claude 顺手维护 | 少量核心话题 |
| 路由表 | `discussions/_INDEX-ROUTING.md` | 文档多时生成，定期更新 | 全部讨论文档 |

两者并存不冲突。话题词典是轻量优先通路，路由表是完备兜底通路。

### 使用路由表（4 步查找）

按以下优先级定位档案文件，**先查命中即停**：

1. **话题词典**（`_INDEX.md` 末尾）— 直接列出关键词 → 文档路径，精确高频词命中
2. **路由表**（`discussions/_INDEX-ROUTING.md`）— 按分组列文件，词典未覆盖时按主题大类查
3. **按分组定位** — 从路由表分组找到目标分组目录后，看分组下文件列表
4. **Read 对应文件** — 命中文件后直接读取（必要时按章节定位）

> 4 步是兜底序列。日常 90% 的查询应在步骤 1 命中（话题词典覆盖足够）；路由表是步骤 1 失效时的二级索引。

### 何时不使用路由表

- 项目小（< 10 文档）
- 文档全部在近 14 天内（`_ACTIVE.md` 的「最近讨论」能覆盖）
- 用户明确问某个有具体文件名的文档

---

## 11. 文档可信度协议（v0.5 合并自 doc-reliability-protocol.md）

> 帮 Claude 在回答查询时正确处理不同来源的信息。

### 信息分级

| 级别 | 来源 | 可信度 | 举例 |
|---|---|---|---|
| **L1** | 代码、配置文件、package manifest | 最高（事实） | `package.json`、`.env.example`、`src/` 代码 |
| **L2** | cadence 自动扫描生成 | 高（扫描时刻事实） | `cadence/discussions/00-project-snapshot.md` 标 `[来源:xxx]` 的字段 |
| **L3** | cadence 讨论记录 | 高（决策意图） | `cadence/discussions/05-tech/database.md` |
| **L4** | 项目内手写文档 | 低（可能过时） | `README.md`、`docs/architecture.md`、`docs/api.md` |

### 查询行为规则

**事实性问题**（"用什么 X"）：

- **L1 > L2，不盲信 L4**
- 档案来源是 L4（如某字段标"[来源：README.md]"），读一眼代码复核
- 答复时可声明"根据代码"（不需说"L1"内部术语）

**意图性问题**（"为什么选 X"）：

- **L3 > L4**
- 当前代码可能已偏离初衷，答复时声明"这是当时的意图，具体实现可能已调整"

**冲突时**：

- 提示用户选择以哪边为准
- 默认倾向 L1（代码）为准更新 L3/L4

### 标注可信度

#### cadence 自动扫描生成的档案

每个事实字段**必须**标注来源：

```markdown
## 技术栈
- 前端：React ^18.2.0  [来源：package.json]
- 后端：Express ^4.18  [来源：package.json]
```

来源 L4 时加警示：

```markdown
## 设计意图（来源：docs/architecture.md，2024-06 撰写）
⚠️ 以下内容来自手写文档，可能与当前代码不一致，查询时请验证
- ...
```

#### 不标来源的情况

- 纯从对话产生的决策（L3）不需每条标来源
- 整个文档的顶部可加日期（"本文于 YYYY-MM-DD 记录"）

### 实际举例

**用户问**："后端用的什么框架？"

1. 读 `_INDEX.md` 看「项目简述」/「话题词典」
2. 找到「后端：Express ^4.18 [来源：package.json]」→ L1 来源 → 直接答
3. 只看到 L4 来源（如"根据 README 说是 Express"）→ 读 `package.json` 复核
4. 复核一致 → 直接答；不一致 → 提示用户选择

**用户问**："为什么选 Express 而不是 Fastify？"

1. 读 `cadence/discussions/05-tech/backend-framework.md`（若存在）
2. 找到理由，声明"这是当时的决策意图"
3. 档案没有 → 查 `_INDEX-HISTORY.md` 或 `_archive/`
4. 还没有 → 说"没有记录具体理由，要现在讨论一下吗？"
