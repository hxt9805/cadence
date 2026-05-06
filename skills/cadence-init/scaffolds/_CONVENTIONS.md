# Cadence 项目约定

> 本文件由 cadence workflow 生成。定义本项目的讨论、记录、查询等协议。
> Claude 遇到冲突时以本文件为准。

## 目录约定

cadence 工作流的所有产物位于项目根的 `cadence/` 目录下。该目录名固定，不可自定义。

```
<project-root>/
├── cadence/                        ← 固定工作流产物目录
│   ├── _INDEX.md                   ← 纯索引（硬上限 < 800 tokens）
│   ├── _ACTIVE.md                  ← 纯活跃内容（硬上限 ~1800 tokens）
│   ├── _INDEX-DOCS.md              ← 完整文档索引
│   ├── _INDEX-HISTORY.md           ← 近 30 天完整讨论历史
│   ├── _CONVENTIONS.md             ← 本文件
│   ├── _archive/                   ← 超 30 天归档
│   │   └── YYYY-MM.md
│   ├── .handoff/                   ← handoff 管理
│   │   ├── index.json              ← 只存 pending 状态
│   │   ├── <timestamp>.md          ← pending handoff 文件
│   │   └── archived/
│   │       ├── index.json          ← resumed/ignored/过期归档条目
│   │       └── <timestamp>.md
│   ├── streaming/                  ← 流式记录域（运行时按需创建，不在 scaffold 中）
│   │   └── <YYYY-MM-DD>-<topic-slug>.md
│   └── discussions/                ← 讨论域（自由形态）
│       ├── _INDEX-ROUTING.md       ← 语义路由表（可选，文档多时）
│       ├── 00-project-snapshot.md  ← 已有项目扫描生成
│       ├── 01-inconsistencies.md   ← 文档-代码不一致清单
│       ├── incidents/              ← bug/事故/tricky fix 档案
│       └── NN-主题/                ← 讨论产出的决策文档
├── CLAUDE.md                       ← 含 cadence 引导片段
└── docs/                           ← 项目原有用途（API 文档、用户手册等）保留
```

### 子域职责

- **`cadence/discussions/`** — 讨论域。自由形态、常翻常改，承载项目决策、设计、调研、事故复盘等。
- **`cadence/_archive/`** — 超 30 天的讨论历史归档，主流程不读。
- **`cadence/.handoff/`** — session 快照管理，由 cadence-handoff / cadence-resume 维护。
- **`cadence/streaming/`** — 流式记录域。**运行时按需创建**（cadence-init scaffold 不预建空目录），第一次命中记录判据时由 `project-discuss` skill 创建。详见下方「物理结构 § streaming/」。

### 分工原则

- 讨论产物进 `cadence/`，不要污染项目原有的 `docs/`。
- `docs/` 保留给项目原生用途（API 文档、用户手册、部署文档等）。

## 文档命名

- 文件名使用英文 **kebab-case**（小写连字符分隔）。
- 讨论文档前缀推荐用**两位数字** + 主题关键词（例如 `02-auth-design.md`），数字表示创建顺序，不必强求严格递增。
- 事故档案使用 **日期前缀**：`YYYY-MM-DD-简述.md`，放在 `cadence/discussions/incidents/` 下。
- `_` 下划线前缀保留给 cadence 自身的元文档（`_INDEX.md`、`_ACTIVE.md`、`_CONVENTIONS.md` 等）。

## 状态标记(v0.4 状态机)

文档头部使用状态标记,便于识别当前阶段。v0.4 引入完整状态机:

### 决策类(活跃决策 / archive doc)

| 状态 | 含义 | 来源 |
|---|---|---|
| `accepted` | 已接受(默认初始态) | v0.3 |
| `implemented` | 已实施(git log / 用户言命中) | v0.4 新增 |
| `stale` | 长期无讨论涉及(30 天) | v0.4 新增 |
| `superseded` | 被新决策推翻 | v0.3 |

合法转换:accepted → {implemented, stale, superseded};implemented / stale / superseded 都是**终态**(无 next status)。

**注**:`archived` **不在 status 集合**——它是"物理动作"(条目从 `_ACTIVE.md` 移出,写入 archive doc),archive doc 中的 status 仍是 implemented / stale / superseded。

### TODO

| 状态 | 含义 |
|---|---|
| `pending` | 待办(默认) |
| `done` | 已完成(v0.4 新增;完成后从 `_ACTIVE` 移除) |

合法转换:pending → done;done 是**终态**。

### 待决

| 状态 | 含义 |
|---|---|
| `open` | 待决(默认) |
| `resolved` | 得出结论 → 升级为活跃决策 |

合法转换:open → resolved;resolved 是**终态**。

### Streaming entry

`active`(流式记录中)→ `archived`(已被整合)/ `tombstone`(用户撤回)

状态变更时,建议在文档顶部记录一行 `status_changed_at`(非强制)。

## Skill 协同约定

### 核心判据

`cadence:project-discuss` 是**常驻监察层**：session 首轮涉及项目讨论时必须激活，之后整 session 持续工作，负责上下文加载、决策记录、查询路由。

**任何其他 skill**（包括但不限于下列）是**任务特定层**，用于某一具体动作的流程控制，职责与 project-discuss **不重叠**：

- `superpowers:brainstorming` / `writing-plans` / `executing-plans` — 头脑风暴、写计划、执行计划
- `cadence:cadence-handoff` / `cadence:cadence-resume` — cadence 自身的 session 管理 skill
- 未来引入的任何 skill — 按核心判据判断

### 正交叠加原则

**两类永远并行，不二选一**：

- 调用了任务 skill **不等于**可以跳过 project-discuss
- 调用了 project-discuss **不等于**不能再叠加其他任务 skill
- 一次用户发言可能同时匹配多个 skill，正确做法是**都调**（串行多次 Skill 调用）

### 常见误判（典型反例）

- 「我已经调 brainstorming 了，决策记录交给它就行」——错。brainstorming 管探索过程，project-discuss 管档案落地。
- 「cadence 自己的流程 skill 总该不用再并行 project-discuss 了吧」——仍然错。两者职责正交与 skill 是否同属 cadence 无关。

清单外的情况：按"核心判据"判断。**任何"Claude 已在做事"的状态都不替代 project-discuss**。倾向：**宁可多调一次 project-discuss，不要让决策无主落地**。

### 中途自检

若发现 project-discuss 从未在本 session 激活但已在讨论决策，立即补调，并按 `skills/project-discuss/SKILL.md` 的「中途自检」段做追溯征询。

## 记录协议（v0.4 三阶段：记 / 整 / 查）

### 设计原意

记录应该像人类老手写笔记一样**融入流程**，而不是每写一条都打断讨论举手报告。v0.2.1 回归 Trueprint 原意：**Claude 自主判断 + 自主记录 + 事后告知**；v0.3 在此基础上把"智能筛选"下移到整 阶段（ε 整合），让主 session 的记录动作更傻瓜式。

不是"什么都记"（会灌满噪音），也不是"每条都先问"（会打断讨论）——是"按单判据判断该记就记，整 阶段（ε 整合）再智能筛选"。

### 记录判据（v0.4 单判据 + 承接对象扩展）

**单判据：「已被承接」**（用户明确或隐含确认过）。**承接对象**从"结论"扩展到"结论 OR 中间决定"。

v0.2.x 的双判据（"未来价值" + "已被承接"）在 brainstorming 树状讨论里系统性漏记；v0.3/v0.4 把"未来价值"判断从记 阶段（α 流式）下移到整 阶段（ε 整合，由 `recall-consolidator` subagent 负责）——**记 阶段傻瓜式无脑记，整 阶段负责智能筛选**。

- **命中判据** → 写 streaming entry 到 `cadence/streaming/<YYYY-MM-DD>-<topic-slug>.md`（详见 `skills/project-discuss/references/recording-protocol.md` 记 阶段节）
- **未命中** → 不记（闲聊 / 脱题 / 脑暴中未被承接的选项）
- 用户信号永远优先：「记一下」必记、「别记」不记、「撤回」追加 tombstone entry

> v0.1 每条 Y/N 征询 → v0.2.1 Trueprint 自主三态 → v0.2.2 "快速/完整通路"双通路 → v0.3 单判据二元（命中 / 不命中）+ 记/整/查三阶段（α/ε/ρ）→ v0.4 沿用 + 简化命名。
> 演化脉络保留，现行以 v0.4 为准。

### 三阶段通路关系（v0.4）

v0.4 沿用 v0.3 三阶段，命名简化为记/整/查（α/ε/ρ）（详见 `skills/project-discuss/references/recording-protocol.md` 的「通路关系」节）：

| 阶段 | 谁做 | 何时 | 产物 |
|---|---|---|---|
| **记 阶段（α 流式）** | 主 session 直写 | 每次命中判据 | `cadence/streaming/<date>-<slug>.md` 追加 entry（append-only） |
| **整 阶段（ε 整合）** | `recall-consolidator` subagent（Plan-only） | 两层触发（手动 `/cadence-consolidate` 或 Phase B 自动条件） | `cadence/discussions/<date>-<slug>.md` ADR-like doc |
| **查 阶段（ρ 检索）** | `recall-retriever` subagent | 主 session 查跨 session 历史时 | summary + pointers（<500 tokens 硬限），主 session 按需 Read |

此外 v0.2.x 的 **决策前回忆分析**（`recall-analyzer`）保留：明确信号（5+ 轮 / 多档案 / 冲突风险）触发时 fork，产三分类事实（你说的 / 档案有的 / 我推断的）呈现用户确认。

### 征询图景（v0.2.2 → v0.4）

主 session 可能触发用户征询的主要情景（v0.4 下，v0.2.x 的"记录三态 C 时机征询"已去，改为记 阶段（α 流式）单判据直接二元判定 + streaming append-only，不再征询）：

① **决策前 recall-analyzer 回忆分析**（v0.2.2 引入，v0.3/v0.4 保留）—— 明确信号触发（5+ 轮 / 多档案 / 冲突风险）时，fork recall-analyzer 产三分类事实（你说的 / 档案有的 / 我推断的），呈现给用户确认。

② （v0.2.2 的"记录三态 C 时机征询"在 v0.3 已去，v0.4 沿用：改为记 阶段（α 流式）单判据直接二元判定 + streaming append-only；不再征询）

③ **归档去向征询**（v0.2.2 引入，v0.3 保留）—— 活跃决策 8 条上限达到时，孤立决策的归档去向由用户选择（a/b/c）。

**其他被动触发**（保留 v0.2.2 语义）：

| # | 场景 | 措辞示例 |
|---|---|---|
| ④ | **结构变更类**（迁移 / 拆文件 / 推翻既有决策） | "迁移 _INDEX.md，影响 ...。继续？" |
| ⑤ | **对象判据抽象**（"改下代码"但不明确对象） | "指哪部分？Auth / DB / 前端？" |
| ⑥ | **冲突检测**（subagent 回忆分析发现冲突） | "发现和 D5 冲突（理由 X），要推翻 D5 / 合并 / 先不记？" |

**风格原则**：一次一事 / 一行轻量 / 多选题优先 / 不追问。

### 隐含确认（典型信号，非穷举）

**强信号（一般视为已承接）**：
- 用户接受性表态（「嗯」「好」「可以」「OK」「没问题」）
- 用户基于此前提推进后续讨论（"那下一步 Y 怎么办"——说明 X 已是既定前提）
- 用户提后续行动（"我去把 X 写了"/"Y 也按这个来"）
- 用户在新决策中引用已讨论的 X

**弱信号或反信号（不算承接）**：
- 沉默（可能在思考 / 转向别话题）
- 反问质疑（"确定吗？"——还在讨论）
- 只听不评（中性）
- 转话题（可能是搁置）

清单外的情况：综合上下文判断"用户是否已经把这条当成既定前提"。不确定时倾向**不记**。

### 决策被推翻

用户改主意 → 直接**覆盖**活跃决策 + 对应 discussion 文档留一行变更原因。
**不必**留旧版归档（决策是活的，不是史料；归档是给超过 30 天的历史讨论用的）。

例外：用户明确说"留个档" → 按用户意图处理。

### 撤销

用户说「刚才那条别记 / 撤回 / 删了 / 忘掉 X」：
1. 立即撤销最近一次记录或删除指名条目
2. 一行告知"已撤"
3. 本 session 内不再就同一话题主动提起

### 告知（简约不简陋 — v0.2.2）

**原则**：
- 一句话摘要（核心是什么）
- 路径 pointer（记到哪）
- **仅当有结构级动作**（新建目录 / 推翻决策 / 跨文档）才加第三行

**简约示例（默认）**：
```
📝 已记：Redis 做 cache（备选 Memcached）→ `_ACTIVE.md` 活跃决策
```

**完整示例（有结构动作时）**：
```
📝 已记：Redis 做 cache → `_ACTIVE.md` + `discussions/03-cache/...`
  ↳ 新建 `03-cache/` 主题目录（存完整 trade-off）
  ↳ 话题词典新增 3 条 pointer（Cache / Redis / Memcached）
```

**短时连续多条**（合并汇报）：
```
📝 已记 3 条：
- 选 Postgres → `_ACTIVE.md`
- Auth 用 JWT → `_ACTIVE.md`
- rate limiting trade-off → `discussions/03-auth/rate-limit.md`
```

**禁用事项**：
- 长篇复述已记内容（用户看得到 diff）
- 索取确认式追认（"这样记可以吗？"——自主模式已经记了）
- 缺 pointer（用户找不到记到哪）

**告知颗粒度**：**明示超出原授权范围的部分**。用户说"记一下 X"但你顺手整理了 pointer Y/Z → 告知时应明示 "+ 顺便补齐 Y/Z 两条 pointer"，让用户有知情权。

### 授权扩张分级（记录时顺手做相邻整理的边界）

| 级别 | 典型场景 | 处理 |
|---|---|---|
| 低风险 | 补齐话题词典 pointer；格式一致性；关联 pointer；修错别字 | 顺手做 + **事后明示超额范围** |
| 中风险 | 修改用户已写内容；跨多文档大改动；删除档案 | **事前征询** |
| 高风险 | 改源代码；改 `.env` / 配置；越出 `cadence/` 的文件（`CLAUDE.md` 的 cadence fragment 管辖域除外） | **完全禁止** |

清单外：按"影响半径 + 可逆性"两维判断。

### 用户显式信号优先

用户的显式信号**永远覆盖**以上所有规则：

- **「记一下」** → 必记，不判断单判据
- **「别记」/「不用记」** → 不记，本 session 内不再就同一话题主动提起
- **「撤回」/「忘掉 X」** → 立即撤 + 一行告知
- **「改 X 为 Y」** → 覆盖记录 + 一行变更原因

### 记录颗粒度

**写什么**：决策结论（一句话进 `_ACTIVE.md` 活跃决策）；关键理由（1-3 句进 discussion 完整版）；必要上下文（涉及哪些文件/模块）；失败的候选（如有明确拒绝，写 discussion 文档）

**不写什么**：逐句对话；Claude 自己的推理过程；用户的犹豫反复（保留结论即可）

### 分流原则（重要，不要倒退）

- **_ACTIVE.md 活跃决策 = 摘要 + pointer**，不堆 trade-off 细节
- **discussion 文档 = 完整 reasoning**（候选方案、被拒理由、deferred 项）
- **_INDEX.md = 纯索引**（项目简述、话题词典、快速导航），不放变化高频内容

这是 v0.1.1 验证通过的分流 pattern，v0.2.2 在拆分文件后保留并强化。

### 记录位置分流表（v0.2.2）

| 内容类型 | 写入位置 |
|---|---|
| 决策结论 | **`_ACTIVE.md` 活跃决策** |
| 硬约束 | `_INDEX.md` 项目简述（**推翻时双写 `_ACTIVE.md`**）|
| 待决问题 | **`_ACTIVE.md` 待决清单** |
| TODO | **`_ACTIVE.md`** |
| 详细设计 | `discussions/NN-主题/xxx.md`（新建） |
| Bug/incident | `discussions/incidents/YYYY-MM-DD-xxx.md` |
| 讨论记录（表格） | **`_ACTIVE.md` 最近讨论**（14 天内）/ `_INDEX-HISTORY.md`（14-30 天）|
| 话题词典 | `_INDEX.md`（不变）|

清单外的内容类型按"变化频率 + 索引性"两维判断：高频变化进 `_ACTIVE.md`，索引/导航进 `_INDEX.md`，完整 reasoning 进 `discussions/`。

### 修改/扩展类动作前的查询前置（v0.2.2）

**核心判据**：用户发言的**主体对象**（名词，不是动词）是否可能已在项目档案里？是 → 查询前置；不是（纯技术 / 外部 / 无关）→ 不查。

**典型场景（非穷举）**：

应查（对象是项目内资产）：
- 提到具体技术栈 / 模块 / 功能名："改 Auth"、"优化 Postgres 查询"
- 提到可能关联已有决策的新动作："加刷新 token"（关联 Auth）
- 提到项目概念的泛化："聊聊我们的认证方案"
- 对话上下文已指向具体模块的泛指："这里重构一下"

不查（对象不在项目域内）：
- 纯技术问答："React hooks 怎么用"
- 外部知识："K8s 学习路径"
- 明显闲聊

边缘（靠 judgment）：
- 抽象主体："代码重构一下"——看对话上下文，有具体对象就查，没有就反问澄清

**清单外的情况**：按"对象 × 是否项目内"两维判断。

**倾向**：**宁可多查一次（确认"没有就没有"）> 漏查（把已有当新的处理）**。多查成本 ≤ 2000 tokens；漏查成本 = 丢失历史 + 重复讨论 + 决策冲突。

### 4 trigger 主动重读（v0.2.2）

默认：**不重读**（读一次进 context，session 内 Claude 自己知道它写了什么）。

**触发主动重读的 4 种信号**：

① 用户明确问状态 / 历史（"XX 确定了吗"）
② Session 轮数 > 100 / 跨越时间长
③ 检测到文件被外部修改（modified time 变化 / git status）
④ Claude 自觉"记忆模糊"（允许自判）

**重读策略**：优先 diff（git diff 或 context 内比对），不读全文。仅 ③ 外部修改才可能需要重读全文。

### 并发写缓解（v0.3）

`_ACTIVE.md` 写入前 mtime 乐观检测（见 `skills/project-discuss/SKILL.md`「`_ACTIVE.md` 并发写检测」节）。
不引入 lock。冲突 → ⚠️ 用户决断。

## 文档可信度协议

### 信息分级

不同来源的信息可信度不同，查询时按分级判断：

| 级别 | 来源 | 可信度 | 说明 |
|---|---|---|---|
| L1 | 代码、配置文件、package manifest | 最高（事实） | 运行时真实状态 |
| L2 | cadence 自动扫描生成（如 `00-project-snapshot.md`） | 高 | 扫描时刻的事实，之后的变化会丢失 |
| L3 | cadence 讨论记录（`discussions/` 下） | 高 | 决策意图，但代码可能已偏离 |
| L4 | 项目内手写文档（`README.md`、`docs/`） | 低 | 可能过时，写作时可能只是初稿 |

### 查询行为

- **事实性问题**（「当前用什么数据库？」「登录接口返回什么？」）：
  - 优先 L1 > L2
  - 不盲信 L4；必要时读代码复核
- **意图性问题**（「当初为什么选 Postgres？」「Auth 模块的设计初衷？」）：
  - 优先 L3 > L4
  - 注意：当前代码可能已偏离初衷
- **冲突时**：
  - 如果 L1（代码）和 L3/L4（文档）不一致，提示用户选择以哪边为准
  - 如果冲突涉及既有决策，建议更新对应文档

## 并发约定

本工作流 **MVP 版本未实现并发写保护**。同一项目多 session 并行工作时：

- **读操作始终安全**
- **写操作可能出现后写覆盖先写**（概率极低，但存在）

建议：

- 同一项目的主要工作在**单 session** 进行
- 若必须并行，让**讨论 session 主导记录，代码 session 不记录**
- 长期并行场景请用 **git branch 隔离 `cadence/` 目录**

（小圈子阶段可能会加简单的 lock 机制；MVP 不做。）

## Handoff 可信度

- handoff 是**当时的快照**，**不是实时状态**
- **事项真实状态以 `_ACTIVE.md` 为准**（活跃决策 / 待决 / TODO / 最近讨论）。handoff 只是辅助视图。
- `cadence-resume` 时 Claude 会自动做差异对比，标记「仍未决 / 已解决 / 已变更」
- 用户可主动推翻现状，重启已被标记为「已解决」的讨论

## Handoff 生命周期

handoff 条目的四种状态：

- **pending** — 新创建，存于 `.handoff/index.json`，文件在 `.handoff/<timestamp>.md`
- **resumed** — 被 `/cadence-resume` 拉起继续。文件移到 `.handoff/archived/`，条目从 `index.json` 移除、追加到 `archived/index.json`
- **ignored** — 用户在 resume 列表中显式忽略。处理同 resumed
- **archived**（过期） — 创建超 **30 天** 未 resumed，自动移到 archived/

归档后：`archived/index.json` 永久保留作历史审计用，主流程（cadence-resume 的列表）不读。

## Incident 记录

当 bug 修复、tricky 修复、生产事故发生，且符合六维判断（通常命中「风险关联」+「重复性」）时：

- 写入 `cadence/discussions/incidents/YYYY-MM-DD-简述.md`
- 使用以下最小模板：

```markdown
# [YYYY-MM-DD] 简述

## 症状
用户/系统观察到的现象

## 根因
为什么会发生

## 修复
涉及的文件、关键代码位置

## 为什么这么修（非显然时写）
候选方案、trade-off、被拒的方案

## 防止复发
需要的测试 / 监控 / 约定
```

- 同时在 `_ACTIVE.md` 的「最近讨论」区块加一行指针
- incident 触发条件、完整处理流程详见 project-discuss skill 的 `references/incident-handling.md`

## 物理结构

### streaming/（v0.3 新增）

- 路径：`cadence/streaming/<YYYY-MM-DD>-<topic-slug>.md`
- 语义：讨论流式记录，一场讨论一文件
- 约束：append-only；撤回追加 tombstone 条目，不物理删；物理归档改 front-matter `status: archived`，文件不移
- 写入方：`project-discuss` skill（主 session 直写，不派 subagent）
- 读入方：`recall-consolidator`（整 阶段，ε 整合）、`recall-retriever`（查 阶段，跨 session 检索）
- 详见 `skills/project-discuss/references/recording-protocol.md` 记 阶段节

### discussions/<date>-<slug>.md（v0.3 ADR-like）

- 路径：`cadence/discussions/<YYYY-MM-DD>-<topic-slug>.md`
- 语义：整 阶段（ε 整合）产物（ADR-like），单文件 = 一个决策
- Front-matter 必填（Phase B）：`status`（accepted | implemented | stale | superseded）、`source_streaming_file`
- Body 四节（h2）：`## Context` / `## Decision` / `## Rationale` / `## Alternatives Considered`
- 产出者：`recall-consolidator` subagent（Plan-only）→ 主 session 写入
- 详见 `skills/project-discuss/references/recording-protocol.md` 整 阶段节

**旧目录约定保留**：`discussions/NN-主题/` 老目录不动，不做迁移。

### 跨讨论血缘（references，v0.3 Phase C）

- ADR doc front-matter 的 `references` 字段列出本 doc 参考的其他 discussion / streaming
- consolidator 扫描时只记"明确提及"的，不做语义推断（宁漏勿误判）
- retriever 检索时跟随 references 做第二跳

### 跨 session 检索（recall-retriever，v0.3 Phase C）

- 主 session 查历史档案时派 `recall-retriever`（见 `skills/project-discuss/agents/recall-retriever.md`）
- 只读 + <500 tokens 硬限 + 返回 summary + pointers
- 主 session 按需 Read 具体 pointer 文件
