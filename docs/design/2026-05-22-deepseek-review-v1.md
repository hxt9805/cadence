# 架构改造方案 — Hostile Review (DeepSeek)

**Reviewer**: hxt9805 (委托 DeepSeek-V4-Pro 执行 hostile review)
**Model**: DeepSeek-V4-Pro
**Date**: 2026-05-22
**Blueprint under review**: `2026-05-22-candidate-A-blueprint.md` (Candidate A: 协议单一来源化)

---

## Executive Summary

这份 blueprint 的核心方向（删 `_CONVENTIONS.md` scaffold、收敛协议到 plugin 内 3 层）是对的，但**协议分层模型存在自我矛盾**（声称"不染色"实则多处渗透），且**实施风险被低估**（Phase A 到 B 之间 bootstrap 引用会短暂断裂、handoff-writer.md 在 Candidate C 前留下 2 个 stale 引用）。建议 **Ship with conditions**：修正 3 个 blocking issues + 2 个 strong suggestions 后再执行。

---

## 1. 9 项核心决策的合理性

### D1 — 删除 `_CONVENTIONS.md` scaffold

**结论**: 同意
**Confidence**: high
**理由**: grilling 第 1 轮的论证充分——`skills/cadence-bootstrap/SKILL.md:18` 指向 `cadence/_CONVENTIONS.md` 取文档可信度分级，但用户项目中的 frozen copy 从未随 plugin 升级而更新。`CHANGELOG.md` 显示 v0.3.0→v0.3.1→v0.3.2→v0.4.0 协议快速迭代（5 天内 4 个版本），用户项目里的 455 行副本必然过时。3 个声明角色（bootstrap 引用源 / 升级检查基 / 用户可读约定文档）互相矛盾——作为引用源时它需要跟 plugin 同步，作为用户可读文档时它需要稳定。该 scaffold 从第一天起就是"双主"问题。

### D2 — cadence-init 形态 = (b) marker + 可选 (c) scanner

**结论**: 同意
**Confidence**: high
**理由**: 跟 superpowers 的 init 行为一致（marker 文件守门）。`hooks/session-start` 已通过 `cadence/_INDEX.md` 存在性 gating bootstrap 注入——这个机制自 v0.2.0 起运行，不需要额外改造。

### D3 — 补全模式删除，改为友好提示 `[r/n]`

**结论**: 同意
**Confidence**: high
**理由**: 补全模式的"self-healing"假设（LLM 自动检测缺失并补全）在实际使用中的触发频率极低。当前 `skills/cadence-init/SKILL.md:25-35` 的补全模式逻辑复杂（文件存在性检查 + 内容结构检查 + 空壳判断），但实际场景几乎不会触发——因为 `cadence/_INDEX.md` + `_ACTIVE.md` 都存在时，骨架就是完整的。改为简洁的 `[r/n]` 提示减少约 12 行。

### D4 — 删除 Step 1a.4 `_CONVENTIONS.md` 升级检查

**结论**: 同意
**Confidence**: high
**理由**: 直接 consequence of D1。`skills/cadence-init/SKILL.md:69-93` 的 25 行升级检查逻辑依赖 scaffold `_CONVENTIONS.md` 存在——一旦 D1 删除该 scaffold，这段逻辑的比对基准就消失了。

### D5 — C3 inline 迁移，删除 `scaffold-upgrader.md`

**结论**: 同意
**Confidence**: medium
**理由**: `skills/cadence-init/agents/scaffold-upgrader.md` (128 行实际,非 blueprint 声称的 123 行) 的职责是"`_INDEX.md` → `_INDEX.md` + `_ACTIVE.md` 拆分"——这是单次 O(N) 的简单操作：Read 一个文件、解析 4 个 section、Write 两个文件。用一个独立 subagent + Plan-only 契约 + 主 session 写入的 3 层抽象来处理这个操作确实是过度工程。Inline 到 SKILL.md 主流程更合理。

**但有一个风险**：inline 后主 session 的 context 里会多 ~30 行迁移指令，对所有 init 调用都可见（包括新项目，根本没 v0.2.x 格式）。可以做条件加载优化——只在检测到旧格式时才展开迁移步骤。

### D6 — 删除已废弃的 Step 4 CLAUDE.md fragment

**结论**: 同意
**Confidence**: high
**理由**: v0.5 起已废弃（`skills/cadence-init/SKILL.md:180-184` 明确标注），bootstrap 注入完全替代了 CLAUDE.md fragment。删除 ~8 行死代码。

### D7 — 协议严格 3 层，"分层不染色"

**结论**: 反对（最弱的一条）
**Confidence**: medium
**理由**: "分层不染色"在原则层面是好的，但 **blueprint 自己违反了这个原则**。具体证据：

- L0 §5 (激活规则 ~20 行) 包含"✅ 必激活 4 类 / ❌ 不激活 3 类 / 🟡 边界模糊"的正反例详表——这是**协议细则**，按 D7 原则应该放 L2。
- L0 §3-4 (单判据 + 记录动作 ~20 行) 是 recording-protocol.md §1-2 的摘要——这是在 L0 和 L2 之间**制造了刻意重复**。
- L1 §2 的 Phase 化协议骨架又跟 L0 §6 的三阶段名字 + meta-protocol 重叠。

三层之间不是"不染色"，而是**"防御性分层"**——每层都有一部分协议内容，密度递增。这是 valid design pattern（类似 TCP/IP 分层中的 header 嵌套），但 blueprint 把它包装成"不染色"是一种 self-deception。更诚实的描述是：**L0 = 最小可行协议（防失血） / L1 = 标准操作协议 / L2 = 完整细则**。

**替代方案**: 重命名 D7 为"防御性 3 层，L0 含最小可行协议作为失血兜底"。承认层间存在**刻意、受控的协议内容渗透**——L0 渗透进来的不是"污染"而是"安全网"。同时量化每个渗透点的理由（如 L0 含激活规则是因为"Gate 1 漏触发的 cost > context budget cost"），写入 ADR-002。

**补充**：blueprint 中 L0 的借口反驳表与 L2 recording-protocol.md 的借口反驳表确实只保留一份——这一点是真正的 dedup，值得肯定。但整体"不染色"叙事仍然 overstated。

### D8 — L0 ~95 行，含 happy path 协议 + meta-protocol + 完整借口反驳表

**结论**: 同意方向，但对体量预算持疑
**Confidence**: medium
**理由**: 见 ADR-002 分析（§4）。核心论点（cadence 是常驻监察 skill，L0 极简会导致 silent failure）成立。但 ~95 行的预算来自跟 superpowers 的 118 行对比——superpowers 的 using-superpowers 不含任何协议内容，cadence 含 happy path 协议后还比它短，这需要解释 current bootstrap 为什么是 104 行（比目标长 9 行）才能塞进更多内容。详见 §4。

### D9 — L2 5 份 references → 3 份

**结论**: 同意，但合并方案需要微调
**Confidence**: medium
**理由**: incident-handling.md (141 行) 跟 recording-protocol.md 确实有重叠——incident 就是 recording 的一个特殊 case。但合并为 ~70 行附录后，incident 的可见性降低。当前 `skills/cadence-bootstrap/SKILL.md:80` 把"用户问 cadence 协议本身"的场景路由到 `_CONVENTIONS.md`（里面有 incident 记录节）。合并后 incident 内容藏在 recording-protocol.md §8，LLM 需要知道"incident 记录规则在 recording-protocol 的附录里"才能找到。建议在 L1 project-discuss/SKILL.md 的路由表中显式加一行："Incident 记录 → references/recording-protocol.md §8"。

doc-reliability-protocol.md (76 行) 合并到 query-behavior.md 是合理——可信度协议本质上是查询的前置知识。但 codex-tools.md (126 行) + opencode-tools.md (100 行) 合并为 harness-adapters.md (~60 行) 需要验证：两源文件合计 226 行，目标仅 60 行，压缩比 3.8:1。blueprint 声称核心是 6×3 适配表 (~15 行)，但 codex-tools.md §2 的 XML wrapping 模板和 spawn_agent 5 步流程是 Codex 强依赖的实操指令，压缩后是否保留足够操作性？见 §6 实施风险。

---

## 2. 3 层分层的正确性 (L0/L1/L2)

### L0/L1/L2 分法是否合理？

基本合理，但有 **3 处内容错位**：

1. **L0 §5 激活规则的正反例详表应该下移到 L1**。L0 应该只说"首条项目相关发言 → 必须激活 project-discuss；边界模糊时倾向触发"，具体的 4 类必激活 / 3 类不激活分类属于 L1 的加载策略层。把详表放 L0 跟 D8 的 ~95 行预算矛盾——详表本身就是 ~12 行，占 L0 预算的 13%。

2. **L0 §9 "ASSUME INTERRUPTION" 应该上移到 L0 §1 或跟 §9 合并为 L0 的引导性开头**。当前 blueprint 把它放在 §9 末尾作为 ~5 行补充，但它应该是 L0 的核心操作原则之一——session 启动后 `/compact` 会清除 context，L0 需要让 LLM 知道"每次 `/compact` 后必须重做这些步骤"。

3. **L1 §10 (graphviz 流程图) 应该在 L2**。graphviz 是给人类开发者看的，LLM 不解析 graphviz。把 ~25 行 graphviz 放在 L1 是对 context budget 的浪费。如果目标读者是维护 cadence 的开发者，graphviz 应该放在 `docs/design/` 而不是运行时 skill 文件。

### L0 ~95 行的预算是否合适？

**过度收缩**。用 superpowers' using-superpowers (118 行, 0 协议内容) 做对比基准是**错误类比**——using-superpowers 只做 meta-protocol（"如何发现和使用 skills"），cadence-bootstrap 要做 meta-protocol + happy path 协议 + 完整借口反驳表。如果 using-superpowers 118 行干了 1 件事，cadence-bootstrap 要干 3 件事却只要 95 行——要么在施魔法，要么内容会过度压缩。

现实的预算是 **110-130 行**。当前 bootstrap 是 104 行（`skills/cadence-bootstrap/SKILL.md` wc -l 实测），blueprint 要删 Codex 调度铁律 (~18 行) 和 `_CONVENTIONS.md` 引用 (~3 行)，释放 ~21 行。同时要加入：完整借口反驳表 (~20 行)、激活规则正反例 (~12 行)、meta-protocol (~10 行)、happy path 协议 (~27 行)，合计 ~69 行新增。104 - 21 + 69 = 152 行。即使做 aggressive trimming，降到 130 行以下需要牺牲内容完整性。95 行是一个**可以追求但不该承诺的目标**。

### 借口反驳表放 L0 的决定对吗？

**对，但不是因为 ADR-002 说的理由**。ADR-002 的核心论证是"LLM 最可能 rationalize '这条不必记' 的时刻，正是它最不可能主动 invoke project-discuss 取反驳依据的时刻"——这个论证是 blueprint 里**最坚实的一个洞察**。`skills/project-discuss/SKILL.md:97` ("调用了 brainstorming 就以为可以跳过 project-discuss,是最常见误判") 和 `skills/project-discuss/references/recording-protocol.md:349-356` (借口反驳表 #1-#5) 的实践经验支持"反驳必须在 LLM 产生借口的同一 context 里可用"。

但借口反驳表放 L0 不是因为"首发言漏激活"——那个场景反驳表帮不上忙（LLM 根本没有激活 project-discuss，但反驳表存在 L0 context 里，LLM 还是能看到）。借口反驳表放 L0 的真正价值是：**即使 project-discuss 已激活，LLM 在决策瞬间也可能 rationalize 不记录**——而这时候它不会去翻 L2 recording-protocol.md 的 §7。L0 让反驳表始终在 context 里，LLM 在做"记不记"判断时零延迟匹配。

### 替代方案"session 启动强制 invoke project-discuss" 被拒绝的理由够不够？

**不够充分**。blueprint 给的理由是"LLM 可能在 invoke 完成前就响应了用户首条发言"——这确实是个问题，但不能作为唯一拒绝理由。可以在 bootstrap 里设"activate project-discuss BEFORE responding to user"的强约束来缓解。superpowers 的 using-superpowers 就用了这个模式（"Invoke relevant or requested skills BEFORE any response or action"）且在实践中有效。

更诚实的拒绝理由应该是：**invoke project-discuss 把 ~249 行 L1 内容 + 按需加载的 L2 references 全部吞进 context，对于"用户第一句话是轻量闲聊"的场景是浪费**。L0 的 happy path inline 策略让 LLM 在轻量场景下不需要吞 L1/L2 也能正确记录。这个理由 blueprint 没写，但比"invoke 完成前就响应了"更有说服力。

---

## 3. ADR-001 (opt-in via cadence-init) 论证强度

### "explicit opt-in 是 feature" 是否站得住？

**站得住，但论证漏了一环**。核心论证的三点（不污染非 cadence 项目 / 可预测性 / 零代价沉默）是 solid 的。但 ADR-001 全文没有讨论一个关键设计维度：**cadence 是一个工作流插件，用户安装它的目的就是用它。为什么还要在每个项目里再 init 一次？**

答案是：全局安装 ≠ 全局启用。一个开发者可能在 10 个项目里只想在 3 个里用 cadence。但这个答案在 ADR-001 里没有显式说出来——它只说"不污染非 cadence 项目"，没说"用户可能有 N 个项目但只想在 M 个里用"。建议补充。

### "全局安装但忘 init 的用户体验是 silent failure" —— blueprint 提了但没解决

**这是 ADR-001 最大的未决问题**。blueprint §6 ADR-001 "When to Revisit" 说：

> "如 dogfood 数据显示大量用户全局安装后忘 init(silent failure 频发),重新考虑增加一次性'首次进入未 init 项目时提示'机制"

但 **dogfood 数据怎么收集？**cadence 没有遥测、没有使用统计、没有 logging。这个 "When to Revisit" 是一个没有触发机制的 revisit。建议至少在 Phase C validation 里加入一项手动测试：找 3 个没用过 cadence 的开发者，让他们"全局安装 cadence 后在一个新项目里开始讨论"，观察有多少人意识到需要先跑 `/cadence-init`。如果 3 人里有 ≥2 人没意识到，就应该在 ADR-001 定稿前加入发现性改进（如 SessionStart hook 在检测到非 cadence 项目时追加一行 `[cadence 已安装但未在此项目激活。运行 /cadence-init 开始使用。]` 的静默提示）。

### "When to Revisit" 够不够？

不够。缺少：
- 触发 revisit 的具体指标（用户报 bug？安装量 vs init 量比例？）
- 数据收集方式（目前完全没有）
- Revisit 的时间窗口（"一个月后检查" vs "观察到 N 个报告后"）

---

## 4. ADR-002 (L0 必须 inline happy path) 论证强度

### "cadence 是常驻监察 skill vs superpowers 是按需 invoke" 是否成立？

**成立，但是被过度简化了**。superpowers 的 skills 不全是"按需 invoke"——`using-superpowers` 本身通过 SessionStart hook 注入，跟 cadence-bootstrap 的机制完全一致。区别在于：superpowers 注入后教 LLM "去 invoke 其他 skills"，而 cadence 注入后教 LLM "你自己要会记录决策"。

superpowers 的"按需 invoke 模式"能工作是因为：TDD skill 被 invoke 后，TDD 的规则立即加载到 context；不需要在 using-superpowers 里预装 TDD 规则。但 cadence 的记录规则不同——**记录动作发生在 invoke project-discuss 之前**（因为 project-discuss 本身要判断"这条要不要记"）。这是一个**鸡生蛋问题**：要正确记录就需要 project-discuss 的规则，但 project-discuss 规则需要在"已被承接"判据命中时才能被加载。L0 inline happy path 解决了这个鸡生蛋。

blueprint 没把这个鸡生蛋逻辑说清楚，而是用了一个较弱的概念"常驻监察"。建议 ADR-002 重写这个核心论证。

### "首发言漏激活 → 整 session 失血" 真的会发生吗？

**没有数据支持**。blueprint 把这个场景当作必然会发生的事实陈述，但它是一个**hypothesis**，从未被验证。当前系统从 v0.2.0 (2026-05-08) 运行至今约 2 周。这段时间里：

- 有几次 session 启动后 project-discuss 确实没被激活？
- 其中几次导致了决策漏记？
- 漏记的决策后来在 handoff/resume 时被发现的？

没有任何数据回答这些问题。ADR-002 的 worst-case 论证在逻辑上是自洽的（"如果发生 → 后果严重 → 应该预防"），但缺少"how likely is it"的校准。一个没有概率权重的 worst-case 论证是**不可证伪的**——它可以用来 justify 把任意内容塞进 L0。

**建议**: ADR-002 应该区分两种 failure mode：
- **Mode A**: 首发言未被识别为"项目相关"，project-discuss 未激活 → 概率未知，需 dogfood 数据
- **Mode B**: project-discuss 已激活，但 LLM 在单条决策时 rationalize 不记录 → 借口反驳表直接解决

Mode B 的概率显然高于 Mode A，但 ADR-002 把两者混在一起论证。L0 inline happy path 主要防备的是 Mode B，而不是 Mode A。修正这个区分后，L0 的内容范围可以更精准。

### L0 inline 完整借口反驳表 (5 项) 是不是过度？

**不过度，但有 1 项可以降级**。#3 ("上限到了再问用户怎么归档") 是 L1/_ACTIVE.md 段管理的行为，跟 L0 的 happy path 记录动作无关。它在 L0 的借口反驳表里的作用是提醒 LLM "70% 软警告时 consolidator 已经静默处理了"——但这要求 LLM 先理解什么是"70% 软警告"、什么是"段独立上限"，这些概念在 L0 里没有展开。

建议 L0 只放 4 项高频借口（#1 流程 skill 误代、#2 等用户说记、#4 概念太多简化执行、#5 主观判断不重要），#3 下移到 L1 的 `_ACTIVE.md` 段管理节旁边——在 LLM 真正面对段管理场景时反驳才有效。

### 替代方案被拒绝的理由够不够？

"session 启动强制 invoke project-discuss" 被拒绝的理由（"LLM 可能在 invoke 完成前就响应了"）已经在 §2 分析过——不够充分。

"不要 L0, 只 inject project-discuss/SKILL.md 全文" 被拒绝的理由（"含大量 edge case 内容, 每 session 注入浪费 context"）是 solid 的——project-discuss/SKILL.md 目前 249 行，含 70/100 阈值、undo 协议、补救路径、session 结束提醒等大量非 happy path 内容。每 session 注入这些是浪费。

---

## 5. 遗漏的设计选项

### cadence-init 形态第 5 种

8 轮 grilling 考虑了 (a) 纯 scaffold 复制 / (b) marker / (c) project-scanner / (d) 交互式问答。遗漏了：

**(e) cadence-init 不是 skill，是 CLI 命令 + 纯文件操作**。当前 cadence-init 作为一个 skill 被 LLM 执行，LLM 需要理解 Step 1/2/3 的分支逻辑、处理用户交互。但如果 cadence-init 只是复制 3 个模板文件 + 跑一个 scanner 脚本，它完全可以是一个 hook 脚本（类似 `hooks/session-start`），用户运行一次就完成初始化，不经过 LLM。

优点：零 context 消耗、确定性执行、不依赖 LLM 判断。
缺点：需要 3 个 harness（CC/OpenCode/Codex）各写一份 hook/script，维护成本上升。

当前选择 (b) skill 形态的合理性在于：skill 是跨 harness 的统一抽象，不需要为每个平台写一份 init 逻辑。但 blueprint 应该 acknowledge 这个 trade-off 的代价：LLM 执行 init 意味着 ~85 行 SKILL.md 在每次 init 时都要被 LLM 解析和推理，而不是被机器直接执行。

### 旧版本迁移第 5 种

C1 (纯手动) / C2 (LLM 主动) / C3 (inline) / B (独立命令) 之外：

**(D) 不迁移，宣布 v0.2.x 格式不再支持**。`CHANGELOG.md` 显示 v0.2.0 发布于 2026-05-08，距今仅 2 周。v0.2.x 格式（单 `_INDEX.md` 含活跃内容 + 索引）的用户基数极小。直接宣布"v0.2.x 项目请删除 `cadence/` 目录后重跑 `/cadence-init`"，比维护 ~30 行 inline 迁移逻辑更简单。

反对 D 的理由：v0.2.x 用户的项目里 `cadence/_INDEX.md` 可能包含有价值的决策记录，直接丢弃会丢失数据。但这个理由的强度取决于"v0.2.x 用户实际积累了多少决策"——如果大部分 v0.2.x 项目只有 2-3 条决策（符合 2 周的时间窗口），迁移的收益可能不如重建。

建议：在 Phase A 先做一次 v0.2.x 用户抽样（检查 cadence-public 仓库的 issue/discussion 或 dogfood 项目），如果确认用户基数 < 5 且决策 ≤ 3 条/项目，就选 D 而不是 C3。

### 协议分层替代范式

blueprint 直接借用了 superpowers 的 3 层模型（inject / skill / references），没有考虑其他范式。两个值得考虑的替代范式：

**DDD Bounded Context**：cadence 的 3 个 phase（记/整/查）各自是一个 bounded context，有独立的 ubiquitous language 和不变量。按 bounded context 分层会是：
- 记 context：单判据 / 承接信号 / entry schema / streaming 落点——这些具有高内聚
- 整 context：consolidator trigger / plan schema / archive 流程
- 查 context：retriever 契约 / context budget / 路由表

而不是按"L0/L1/L2 注入深度"分层。DDD 分层的优势是每个 context 内部高度自洽，LLM 加载一个 context 就能完整理解一个 phase。当前 L0/L1/L2 分层的代价是：要理解"记"阶段，LLM 需要从 L0 §3-4 + L1 §2 + L2 recording-protocol.md §1-2 三个文件里拼凑信息。

**Event Sourcing**：cadence 的 streaming entries 本质是 event log（append-only / immutable / 按时间排序），`_ACTIVE.md` 是 materialized view（当前状态的投影），consolidator 是 event handler（消费 streaming events 更新 projections）。事件溯源范式能自然地解释：
- 为什么 streaming 是 append-only（event sourcing 的不可变性）
- 为什么 `_ACTIVE.md` 可以被重建（从 streaming events replay）
- 为什么 handoff 是快照（snapshot pattern 减少 replay 成本）

这个范式不在 blueprint 的讨论范围内，但它能提供一个比 superpowers 3 层模型更贴合 cadence 领域语义的架构语言。

---

## 6. 实施风险

### Phase A/B/C 切分

**Phase A (cadence-init 简化) 和 Phase B (协议三层化) 不能完全解耦**。Phase A Step 1 删除 `_CONVENTIONS.md` scaffold 后，`skills/cadence-bootstrap/SKILL.md:18`、`:32`、`:70`、`:80` 的 4 处 `_CONVENTIONS.md` 引用立即变为 dangling reference——它们指向一个不再写入用户项目的文件。如果 Phase A 完成后、Phase B 开始前有用户走 `/cadence-init` 流程，新创建的 `cadence/` 目录里没有 `_CONVENTIONS.md`，但 bootstrap 仍告诉 LLM "去读 `cadence/_CONVENTIONS.md`"。

**建议**: 把 Phase B Step 7 (bootstrap 重写) 拆出来作为 Phase A 的最后一步，或者把 Phase A Step 1 (删除 `_CONVENTIONS.md` scaffold) 移到 Phase B 的开头。总之不能让 bootstrap 的引用和 scaffold 的存在性之间出现 gap。

### 破坏性动作识别

| 步骤 | 破坏性 | 影响范围 |
|---|---|---|
| Phase A Step 1: 删除 `_CONVENTIONS.md` scaffold | **高** | 现有 v0.2.x 用户的 `_CONVENTIONS.md` 升级检查失效（但 D4 本来就是删除它）；之后的 init 不再创建该文件 |
| Phase B Step 7: 重写 bootstrap | **高** | 所有 session 的注入内容改变——如果重写有 bug（如借口反驳表措辞导致 LLM 行为改变），影响所有活跃 session |
| Phase B Step 12: 删除 4 个 reference 文件 | **中** | 如果有其他文件通过绝对路径引用这些文件（而不是通过 `references/` 目录路径），会断裂 |
| Phase B Step 13: 更新 `_CONVENTIONS.md` 引用 | **低** | 纯文本替换 |

### Rollback path 未定义的步骤

blueprint 没有为以下场景定义 rollback：

1. **Phase B Step 7 bootstrap 重写后发现 L0 行为异常** — 怎么回滚？`git revert` 可以恢复文件，但已注入到活跃 session 的 LLM 已经读了旧版 bootstrap，`/clear` 后会读新版。如果在 `git revert` 和用户 `/clear` 之间有时间窗口，LLM 可能跑的是有问题的版本。建议 Phase B 先在 staging 分支上验证，确认后 squash merge。

2. **Phase B Step 9-10 合并 reference 文件后，发现合并丢失了关键细节** — 原来的 incident-handling.md 和 doc-reliability-protocol.md 已删除。回滚需要从 git history 恢复。建议在删除前先 commit 原始状态，保留一个 `git revert` 能一键回滚的 commit。

3. **Phase B Step 13 更新引用不完整** — blueprint 的 grep 验证清单（§7.1）只检查了 4 个模式（`_CONVENTIONS.md` / `scaffold-upgrader` / `codex-tools.md|opencode-tools.md` / `incident-handling.md|doc-reliability-protocol.md`），但没有检查**新增的 harness-adapters.md 是否被正确引用**。这是一个 gap。

### Phase B Step 13 `_CONVENTIONS.md` 引用清单验证

grep 验证结果（`skills/` 目录下的 `_CONVENTIONS.md` 引用）：

| # | 文件 | 行号 | blueprint §3.4 是否覆盖 | 改动类型 |
|---|---|---|---|---|
| 1 | `skills/cadence-bootstrap/SKILL.md` | L18, L32, L70, L80 | ✅ (4 处) | 改指 plugin 内 |
| 2 | `skills/project-discuss/SKILL.md` | L166 | ✅ (1 处) | 改为 inline |
| 3 | `skills/cadence-handoff/agents/handoff-writer.md` | L144, L209 | ✅ (2 处) | 不动(Candidate C) |
| 4 | `skills/cadence-init/agents/scaffold-upgrader.md` | L115, L119 | ✅ (2 处) | 随文件删除 |
| 5 | `skills/cadence-init/scaffolds/_ACTIVE.md` | L27 | ✅ (1 处) | 删除 hint |
| 6 | `skills/cadence-init/scaffolds/_INDEX.md` | L23 | ✅ (1 处) | 删除行 |
| 7 | `skills/cadence-init/SKILL.md` | L30, L47, L69, L71, L73, L79, L88, L89, L94, L109, L190, L215 | ❌ **漏记** | 随文件重写 |

**#7 是一个重要遗漏**：`skills/cadence-init/SKILL.md` 有 12 处 `_CONVENTIONS.md` 引用，blueprint §3.4 完全没有列出。blueprint §3.2 标记了 cadence-init/SKILL.md 为"重写"，所以这些引用会随着重写自然消失。但 **blueprint 在 §3.4 的表中应该注明"cadence-init/SKILL.md 有 12 处引用，因文件整体重写而不单独列出"**，否则读者会误以为只有 7 个文件受影响。当前表格给人"这是完整清单"的错觉。

另有 `.codex/RUNBOOK.md:62` 的 1 处引用——blueprint 表里有但标注为"改为指 plugin 内"。具体改成指什么？当前 RUNBOOK 的内容是 smoke test 清单，需要 `cadence/_CONVENTIONS.md` 存在于用户项目。删除 scaffold 后，这个 smoke test 步骤需要改成检查 `cadence/_INDEX.md` + `cadence/_ACTIVE.md` 而不是 `cadence/_CONVENTIONS.md`。blueprint 只是说"改为指 plugin 内"，没给具体替换文本。

### 补充验证：合并后 reference 文件大小

blueprint §4.3.3 声称 harness-adapters.md 约 60 行，合并 codex-tools.md (126 行) + opencode-tools.md (100 行) = 226 行。压缩比 3.8:1。合并合理性取决于"6×3 适配表"能否替代两个文件的全部操作性内容。具体风险：

- codex-tools.md §2 的 XML wrapping 模板 (L42-58, ~17 行) 是 Codex spawn_agent 的实操关键——没有这个模板，LLM 在 Codex 形态下可能生成错误格式的 XML。合并到 ~60 行文件后，XML 模板很可能被压缩到 2-3 行伪代码。
- opencode-tools.md §1 标注的"behavior 1:1 alignment with CC"是一个重要的信任信号——Codex 有调度铁律，但 OpenCode 没有。合并后如果这个区分被模糊化，可能误导 LLM 在 OpenCode 上也使用 Codex 级保守策略。

**建议**: harness-adapters.md 目标行数调高到 ~90 行，保留 XML wrapping 模板和 OpenCode/Codex 差异的完整性。

---

## 7. 跟 superpowers 对比的盲点

### 合理借鉴

- SessionStart hook 注入 bootstrap 的模式 — superpowers 通过 `using-superpowers` skill 注入，cadence 通过 `cadence-bootstrap` skill 注入，机制一致。
- skill + references 的文件组织 — superpowers 的 `skills/<name>/SKILL.md` + `references/` + `agents/` 目录结构被 cadence 直接采用。
- 借口反驳表 (anti-rationalization table) — superpowers 的 using-superpowers 有 "Red Flags" 表（"This is just a simple question" → "Questions are tasks. Check for skills." 等），cadence 的借口反驳表在概念上同源。

### 不该照搬的

1. **superpowers 的"skills 按需 invoke"模型被盲目对照**。superpowers 的 TDD/debugging/brainstorming 都是 task-scoped（开始→执行→结束），但 cadence 的 project-discuss 是 session-scoped（持续整个 session）。blueprint 在 ADR-002 中隐含地承认了这一点（"cadence 是常驻监察 skill"），但没有在 D7 分层设计中反映这个差异。superpowers 的 L0 (using-superpowers) 不需要协议内容是因为 TDD/brainstorming 等 skills 被 invoke 后才加载各自的协议。cadence 不能照搬这个模型——project-discuss 的协议需要在"被 invoke 之前"部分可用。

2. **superpowers 的 `brainstorming` skill 作为"流程前置"被类比到 cadence 的 `project-discuss`**。`skills/cadence-bootstrap/SKILL.md:97` 强调两者的正交性，但 blueprint 的 L0/L1/L2 分层实际上把 project-discuss 的内容拆成了"注入层"和"按需加载层"——这正是 superpowers 对待 TDD/brainstorming 的方式（核心规则在 skill body，meta 在 using-superpowers）。cadence 需要更诚实地承认这种结构相似性，而不是强调差异。

### superpowers 自身也有问题、cadence 还盲目跟随的反例

**superpowers 的 `using-superpowers` description 字段过长**。`using-superpowers` 的 description（the `name:` frontmatter 下的 `description:` 字段）包含了大量触发规则和流程图——这跟 cadence-bootstrap 的 description（`skills/cadence-bootstrap/SKILL.md:3`）结构类似。两者都用 description 字段承载了超过"触发条件描述"的内容。

但 superpowers 能这样做是因为它的 description 被 CC 的 skill discovery 机制读取并展示给 LLM，而 cadence-bootstrap 不依赖 skill discovery——它靠 SessionStart hook 强制注入 body。cadence-bootstrap 的 description 字段实际上只在 Codex 形态下起作用（Codex 无 SessionStart，靠 skill discovery 机制触发 LLM 主动 load skill body）。blueprint 完全没有讨论这个差异——它假设 bootstrap 的注入机制在三个 harness 上一致，但实际上 Codex 走的是完全不同的路径（progressive disclosure: LLM 先看到 description → 判断是否 load body）。

---

## 8. Candidate A 与 Candidate G 的关联

### A 是否真的为 G 铺好了路？

**部分铺路，部分埋坑**。

铺路的部分：
- 删除 `_CONVENTIONS.md` 消除了"协议在 plugin 和用户项目各有一份"的双主问题，LLM 不再可能读到过时的记录协议。如果 v0.3.1 的"假设读者无上下文"原则在 455 行的 frozen scaffold 里缺失（因为它是在 v0.3.1 引入的），删除 scaffold 直接消除了这个隐患。
- 借口反驳表移到 L0 意味着 LLM 在写 entry 时始终能看到"不要过于简洁"的反驳——这是 G 的 root cause #1（streaming entry 选填字段几乎不被填）的直接对抗。

埋坑的部分：
- **合并 references 可能加剧 streaming entry 太简的问题**。L2 references 合并后，`recording-protocol.md` 从 368 行膨胀到 ~400 行（加了 incident 附录）。LLM 在需要查询"entry 应该写多详细"时，需要在一个 400 行文件里找到 §2 的"信息密度正反例"——而合并前，相关信息在更短的文件里（recording-protocol.md 368 行）。如果 LLM 不主动 Read L2 references（依赖 L0/L1 的摘要），合并后更大的文件反而降低 LLM 主动 Read 的概率。
- **handoff 失血 (Candidate G) 的一个 root cause 是"consolidator 触发不主动"**。Candidate A 的 Phase B 删除了 recording-protocol.md 的借口反驳表 §7（其中 #3 是"上限到了再问用户怎么归档"的反驳），只在 L0 保留了反驳表。但 consolidator 的触发判断发生在 L2 context（record-protocol.md §3 触发条件），而不是 L0 context。L0 的反驳表提醒 LLM"70% 软警告时 consolidator 已经静默处理了"——但 LLM 在读到 §3 触发条件时，L0 的反驳表可能已经被后续 context 淹没。这是一个 **context 时效性问题**：反驳表在 session 启动时注入，但触发场景发生在 session 中后期。

### 建议 A 实施前先做的 G 兼容性预防措施

1. **在 L0 §4 (记录动作) 中直接嵌入"信息密度正反例"的指针 + 一句强制语句**。当前 blueprint §4.1 L0 §4 只说"context/options/rejected 选填但鼓励填(指向 L2 信息密度正反例)"——这是一个弱引用。建议改为："写 entry 时**必须**对照 L2 `recording-protocol.md` §2 的信息密度正反例自检——密度过低的 entry 会导致下游 session 信息偏差 (dogfood 实证)。" 把"鼓励"升级为"必须"，把指向从可选变为强制。

2. **在合并 recording-protocol.md 时，把 §2 的"信息密度正反例"保留为一个独立的醒目 section，不埋在其他内容里**。当前 blueprint §4.3.1 的 L2 结构调整中，信息密度正反例在 §2 (记阶段) 的子节里——合并 incident 附录后，它的相对位置会更隐蔽。建议在 L2 文件顶部加一个"🔥 写 entry 前必读：信息密度正反例 (§2.X)" 的导航提示。

3. **在 L1 project-discuss/SKILL.md 的 Phase 1 记阶段摘要中，加入一句"质量自检：对照 L2 recording-protocol.md §2 信息密度正反例"**。这样 LLM 在激活 project-discuss 后（即使不主动 Read L2），至少知道存在一个"自检标准"可以查阅。当前的 L1 §2 设计（blueprint §4.2）只说"Phase 1 记 — 触发 / 落点 / 告知 / 铁律(指向 L2 细则)"——这个"指向 L2 细则"太弱了。

---

## 9. 总评估

**结论**: **(b) Ship with conditions**

### 必须先解决的 blocking issues (3 项)

**B1 — Phase A/B 之间的依赖断裂**。Phase A Step 1 (删除 `_CONVENTIONS.md` scaffold) 和 Phase B Step 7 (重写 bootstrap) 不能分开执行。要么删 scaffold 和重写 bootstrap 在同一个 commit 里完成，要么 Phase A 不包含删 scaffold（把它推迟到 Phase B）。当前 Phase A 独立执行会导致 bootstrap 引用 dangling。

**B2 — D7 "分层不染色"叙事修正**。不能声称"不染色"但实际在 L0/L1/L2 之间制造刻意协议渗透。将 D7 改为"防御性 3 层，层间有受控且最小化的协议内容渗透"。如果坚持"不染色"叙事，实际实施时开发者会注意到矛盾、产生困惑。ADR-002 需要引用修正后的 D7。

**B3 — `_CONVENTIONS.md` 引用清单不完整**。blueprint §3.4 漏列 `skills/cadence-init/SKILL.md` 的 12 处引用（虽然该文件整体重写，但清单应注明以自证完整）。另需为 `.codex/RUNBOOK.md:62` 的引用给具体替换文本，而非仅说"改为指 plugin 内"。

### Strong suggestions (2 项)

**S1 — L0 体量预算从 ~95 行调高到 110-130 行**。以 superpowers using-superpowers (118 行, 0 协议) 为基准，cadence-bootstrap 多了 happy path 协议 + 完整借口反驳表 + 激活规则，95 行不可达。设定不合理目标会导致实施时被迫裁减内容。

**S2 — harness-adapters.md 目标行数从 ~60 行调高到 ~90 行**。codex-tools.md 的 XML wrapping 模板是 Codex 实操关键，不能压缩到伪代码。压缩比从 3.8:1 放宽到 2.5:1。

### 不需要 redesign 的理由

核心方向（删 frozen scaffold、协议收敛到 plugin、借口反驳表前移到 injection 层）是正确的。问题出在实施细节和叙事一致性上，不是方向性错误。修正 B1-B3 + S1-S2 后可以执行。

---

## 附录 A: 验证证据

### A.1 行数实测 (wc -l)

```
skills/cadence-bootstrap/SKILL.md                    104 行
skills/project-discuss/SKILL.md                      249 行
skills/project-discuss/references/recording-protocol.md  368 行
skills/project-discuss/references/query-behavior.md      248 行
skills/project-discuss/references/incident-handling.md   141 行
skills/project-discuss/references/doc-reliability-protocol.md 76 行
skills/project-discuss/references/codex-tools.md         126 行
skills/project-discuss/references/opencode-tools.md      100 行
skills/cadence-init/SKILL.md                         228 行 (blueprint 称 230)
skills/cadence-init/scaffolds/_CONVENTIONS.md        455 行
skills/cadence-init/agents/scaffold-upgrader.md      128 行 (blueprint 称 123)
```

9 份"协议描述"文件实测合计: **1,640 行**，blueprint 声称 1,867 行。差 227 行 (14% 偏高)。

### A.2 `_CONVENTIONS.md` 引用完整清单 (git grep)

8 个文件含引用。Blueprint §3.4 覆盖了 7 个，遗漏 `skills/cadence-init/SKILL.md` 的 12 处（因该文件整体重写，但清单未注明）。

### A.3 git log 时间线 (验证 "v0.2.x 用户基数小")

```
v0.2.0: 2026-05-08 (首个正式发布)
v0.2.1: 2026-05-14 (6 天后)
v0.3.0: 2026-05-18 (4 天后)
v0.3.1: 2026-05-19 (1 天后)
v0.3.2: 2026-05-21 (2 天后)
v0.4.0: 2026-05-21 (同一天)
```

从 v0.2.0 到 v0.4.0 仅 13 天，5 个版本。v0.2.x 格式存活窗口为 10 天（v0.2.0 → v0.3.0），用户基数确实小。支持 C3 (inline 迁移) 或 D (不迁移) 的选择。

### A.4 `_CONVENTIONS.md` 引用在 handoff-writer.md 的具体位置

- `skills/cadence-handoff/agents/handoff-writer.md:144`: "此行为与 `cadence/_CONVENTIONS.md` 的「Handoff 生命周期」一致。" — 如果 Candidate C 延迟，这个引用指向不存在的文件。
- `skills/cadence-handoff/agents/handoff-writer.md:209`: "遵循 `_CONVENTIONS.md` 并发约定" — 同上。
