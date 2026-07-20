# 架构改造方案 — Hostile Review v2 (DeepSeek)

**Reviewer**: hxt9805 (委托 DeepSeek-V4-Pro 执行 hostile review, v2 round)
**Model**: DeepSeek-V4-Pro
**Date**: 2026-05-22
**Blueprint under review (v2)**: `2026-05-22-candidate-A-blueprint.md`
**Previous review (v1)**: `2026-05-22-deepseek-review-v1.md`

---

## Executive Summary

v2 修订解决了 v1 review 的全部 3 个 blocking issues (B1/B2/B3) 和 2 个 strong suggestions (S1/S2)。叙事从"分层不染色"改为"L0 是 L2 精炼摘要"提高了内部一致性。ADR-002 的"鸡生蛋"重写 + Mode A/B 区分 + Precautionary Design 声明是 v2 最坚实的改进。**Ship now** — 无新的 blocking issues。有 2 个 minor patches 建议在实施时顺手处理（不影响 ship 判定）。

---

## 1. v2 修订验证

### 修订 #1: B1 — Phase A/B 依赖断裂

**是否解决**: **solved**
**是否引入新问题**: 有 1 个 minor sibling concern
**修订强度**: right

v2 将"删 `_CONVENTIONS.md` scaffold"从 Phase A Step 1 移到 Phase B Step 6a，与 bootstrap 重写 (6b) 和引用清理 (6c) 打包为同一个 commit (6d)。`2026-05-22-candidate-A-blueprint.md:436-441` 的指令是明确的："必须同 commit"。

Phase A Step 1 现在只删 `scaffold-upgrader.md`，Step 2 重写 `cadence-init/SKILL.md`（不再调用 scaffold-upgrader）。Phase A 不再碰 `_CONVENTIONS.md` scaffold。

**Minor sibling concern**: Phase A 内部没有类似 Phase B Step 6 的显式"同 commit"约束。Step 1 删 scaffold-upgrader.md 后，如果实施者在 Step 1 和 Step 2 之间 commit，中间状态的 cadence-init/SKILL.md 仍引用一个已删除的 subagent。建议在 Phase A 描述中加一句"Steps 1-4 建议同 commit，至少确保 Step 1 和 Step 2 在同一次 session 内连续完成"。

### 修订 #2: B2 — 分层叙事修正

**是否解决**: **solved**
**是否引入新问题**: 无
**修订强度**: right

v2 将 D7 从"分层不染色"改为"L0 是 L2 的精炼摘要,单一权威源在 L2,L0 写错时以 L2 为准"(`2026-05-22-candidate-A-blueprint.md:56`)。ADR-002 新增"L0 是 L2 精炼摘要的关系契约"段 (`:644-650`)，明确了"这不是重复,这是 summary↔detail"。

grep 验证"不染色"残留：v2 全文中只有 2 处出现，都是在历史记录上下文中（`:16` changelog 解释"从 X 改为 Y"、`:796` grilling 历史表 round 7 结论 —— 记录当时讨论内容）。设计主体部分统一使用"精炼摘要"术语。叙事一致性修复到位。

### 修订 #3: B3 — 引用清单补全

**是否解决**: **solved**
**是否引入新问题**: 无
**修订强度**: right

v2 `:159` 在 §3.4 表中新增一行："`skills/cadence-init/SKILL.md` | **12 处** | 随该文件整体重写(§4.4)自然消失,不单独列"。RUNBOOK 引用也给了具体替换文本 (`:160`)，从模糊的"改为指 plugin 内"改为"`cadence/_INDEX.md` + `cadence/_ACTIVE.md` 存在性检查"。

### 修订 #4: S1 — L0 预算 110-130

**是否解决**: **solved**
**修订强度**: right

v2 L0 内容清单 (`:177-244`) 各节预算合计 ~111 行，接受 ±20 行浮动（有效区间 91-131）。逐节计算：§0(5) + §1(5) + §2(5) + §3(7) + §4(15) + §5(12) + §6(12) + §7(12) + §8(25) + §9(3) + §10(10) = **111 行**。

注意 §8 (~25 行 for 4 项反驳表) 比 v1 的 §7 (~20 行 for 5 项) 多了 5 行预算——少了一项内容但多了行数。这是合理的，因为 v2 的 §8 包含了更详细的"正交并行"解释段（`:222-230`）。实施时需 discipline 控制 §8 的行数，否则容易 spill over。

### 修订 #5: S2 — harness-adapters 80-100

**是否解决**: **solved**
**修订强度**: right

v2 `:358-375` 给 harness-adapters.md 每节的预算：§1(5) + §2(15) + §3(15) + §4(17-完整XML模板) + §5(10) + §6(15) = **77 行**。加上文件格式 frontmatter 和自然留白，80-100 区间可达。

XML wrapping 模板保留完整 (`:365-367` "不压缩为伪代码")，OpenCode 差异显式说明 (`:369-371` "防止 LLM 在 OpenCode 上误用 Codex 级铁律")。相比 v1 的计划，这两个风险点都被消除了。

### 修订 #6: ADR-002 核心论证重写

**是否解决**: **solved** (详见 §2)
**是否引入新问题**: 无
**修订强度**: right

### 修订 #7: 借口反驳 #3 下移

**是否解决**: **solved**
**修订强度**: right

v2 `:268-269` 将借口反驳 #3 放在 L1 §4 (_ACTIVE.md 段独立管理) 内。位置选择正确：LLM 读到 70/100 阈值机制时，立即看到"不要等到 100%"的反驳。比放在 L0（LLM 不理解段管理概念时看到）更有操作价值。

### 修订 #8: L0 激活规则正反例精简

**是否解决**: **solved** (详见 §3c)
**修订强度**: right (given the constraint of staying in L0)

### 修订 #9: Candidate G 兼容性预防 3 条

**是否解决**: **solved**
**修订强度**: right, 但有 1 个 implementation-quality concern

三条预防措施 (`:748-758`) 分别在 L0 §5 (强制)、L2 顶部导航、L1 Phase 1 摘要处嵌入信息密度引用。三条措施覆盖了 LLM 在三个不同 context 深度看到信息密度自检的路径。

**Minor concern**: L0 §5 的强制指令 (`:204-206`)："写 entry 时**必须**对照 L2 recording-protocol.md §2 的「信息密度正反例」自检" —— 这是 L0 里最强的 imperative 之一。如果 LLM 在 happy path (未 activate project-discuss, L2 未加载) 时写了 entry，它被要求对照一个还没 Read 的文件。这可能导致两种后果：(a) LLM 主动 Read L2（好），或 (b) LLM 忽略该指令（指令被"习得性忽略"）。建议在 L0 §5 中加条件措辞："写 entry 时**必须**对照 L2 recording-protocol.md §2「信息密度正反例」自检。**如 L2 不在 context,先 Read 它**。" 这样 LLM 知道下一步操作而不只是被警告。

### 修订 #10: RUNBOOK 引用具体化

**是否解决**: **solved**
**修订强度**: right

### 修订 #11: ADR-001 + ADR-002 补充

**是否解决**: **solved**
**修订强度**: right

ADR-001 v2 新增第 4 条 rationale "Context budget 节约" (`:522-524`) —— 这个论证补上了 v1 review 指出的"用户可能在 N 个项目中只有 M 个用 cadence"的缺失。When to Revisit 新增"数据收集 gap"承认 (`:553-554`)。

ADR-002 新增 Precautionary Design 声明 (`:622-631`) —— 诚实承认 Mode A 是 hypothesis 而非 proven fact。这在技术上**增强**了 ADR 的说服力：它是一个有自知之明的预防性设计，不是基于错误 certitude 的 over-engineering。

### 修订 #12: 验证清单加 harness-adapters 检查

**是否解决**: **solved**
**修订强度**: right

v2 `:680-683` 新增 grep 检查验证 harness-adapters.md 被正确引用。

### 修订 #13: 附录 B — Event Sourcing / DDD

**是否解决**: **N/A (new addition, not solving a v1 issue)**
**是否引入新问题**: 见 §4
**修订强度**: slightly over

详见 §4 分析。主体不影响 ship 判定。

---

## 2. ADR-002 重写质量

### "鸡生蛋"叙事

v1 review 建议 ADR-002 从"常驻监察 skill"改为"鸡生蛋"论证。v2 完全采纳 (`:586-594`)：

> "cadence 的核心 paradox:**要正确记录决策就需要 project-discuss 的协议规则,
> 但 project-discuss 的规则需要在「已被承接」判据命中时才能加载到 context**。"

这个叙事比 v1 的"常驻监察 skill"更精确。v1 的"常驻监察"只是描述了 project-discuss 的行为特征（session-scoped），但没有解释**为什么 L0 必须 inline 协议**。v2 的"鸡生蛋"直接命中因果链：记录动作 → 需要规则 → 但规则在 skill 里 → skill 需要被 invoke → invoke 发生在判据命中后 → 死锁。打破死锁的唯一方式是把规则预装到 injection 层（L0）。

**没有逻辑漏洞**。这个论证是 airtight 的（给定"LLM 需要在判据命中瞬间判断是否记录"这个前提），比 v1 的论证有更强的因果结构。

### Mode A/B 区分

`:599-608` 的区分表是我 v1 review 最核心的建议之一，v2 完整采纳。表本身是清晰的：

| Failure Mode | 防御机制 | 概率 |
|---|---|---|
| Mode A: 首发漏激活 | L0 inline happy path 协议 | 未知 |
| Mode B: 已激活但 rationalize | L0 inline 借口反驳表 | 显然高于 Mode A |

一个 subtle 但重要的点：Mode A 的防御机制（L0 inline happy path）和 Mode B 的防御机制（L0 inline 借口反驳表）**都在同一个 L0 里实现**，所以这个区分不会导致"选哪个"的 trade-off —— 两者都通过 L0 inline 获得。这让 ADR 不存在内部张力。

### Precautionary Design 声明

`:622-631` 的声明："在 cadence 当前无遥测的前提下,本设计是 precautionary design" —— **反而增强了 ADR 的说服力**。它表明设计者知道自己的 knowledge gap，做了 conservative choice，并定义了什么时候可以 revisit。一个诚实的"我可能高估了 Mode A 的风险"比一个假装 certainty 的"Mode A 必然发生"更能让未来的维护者信任这个决策。

### "L0 是 L2 精炼摘要的关系契约"

`:644-650` 的 4 点契约：单一权威源 = L2、L0 写错以 L2 为准、L2 优先修改 → L0 同步、不是重复是 summary↔detail。这段跟 D7 的叙事完全一致，没有内部矛盾。

**唯一微调建议**：当前措辞"L0 写错时以 L2 为准"暗示 L0 可能出错。但实际上 L0 是精炼版，不存在"错"——它只是不完整。建议改为"L0 描述与 L2 有歧义时,以 L2 为准"——把"错"改为"歧义"，更精确反映 summary↔detail 关系的本质。

---

## 3. Push back 项回应

### 3a. Graphviz 下移 L2

**v1 建议**: L1 graphviz 流程图应该下移 L2（LLM 不解析 graphviz）。
**作者拒绝**: superpowers 大量在 SKILL.md 内嵌 graphviz 是 LLM behavior shaping 实证有效手段。

**我的回应**: **同意作者的反驳，撤回 v1 建议**。

交叉验证结果：
- `E:\Study\github-project\superpowers\skills\using-superpowers\SKILL.md:48-63` — dot digraph "skill_flow"，在 always-injected bootstrap 中，描述 skill 调用决策流程
- `E:\Study\github-project\superpowers\skills\brainstorming\SKILL.md:36-64` — dot digraph "brainstorming"，在 on-demand skill body 中，描述 9 步设计流程
- `E:\Study\github-project\superpowers\skills\test-driven-development\SKILL.md:49-53` — dot digraph "tdd_cycle"，描述 Red-Green-Refactor 循环

这些 dot 图直接在 SKILL.md body 中，LLM 在 session 中读到它们。Dot 语法是结构化文本（`shape=box`、`->`、`[label="..."]`），LLM 完全能解析。superpowers 使用 dot 图不是为了人类开发者，而是作为 LLM behavior shaping 工具——编码决策树/流程图为结构化文本，减少 LLM 自由解读散文的空间。

v2 blueprint 的 graphviz 用于"段独立 trigger 决策流"和"phase 选择流"——这两个恰好是 LLM 最需要精确 decision logic 的场景。用 graphviz 编码比散文更不 ambiguous。**撤回 v1 的"graphviz 下移 L2"建议**。

### 3b. 1,867 行偏高 14%

**v1 声称**: 9 份协议描述文件实测 1,640 行，blueprint 声称 1,867 行，偏高 14%。
**作者反驳**: deepseek 算术错误，自己列的清单总和不是 1,640。

**我的回应**: **v1 确实算错了，承认**。

v1 review 附录 A.1 把 `cadence-init/SKILL.md` (228 行) 计入了 9 份协议描述文件，但 blueprint 的 9 份文件清单是：

```
bootstrap/SKILL.md:              104
project-discuss/SKILL.md:        249
recording-protocol.md:           368
query-behavior.md:               248
incident-handling.md:            141
doc-reliability-protocol.md:      76
codex-tools.md:                  126
opencode-tools.md:               100
_CONVENTIONS.md (plugin source): 455
─────────────────────────────────────
合计:                           1,867  ✓
```

104+249+368+248+141+76+126+100+455 = 1,867。v1 错误地把第 9 个文件替换成了 cadence-init/SKILL.md (228)，得出 1,640。作者的 1,867 是正确的。**v1 review 附录 A.1 中的"差 227 行 (14% 偏高)"结论作废**。

### 3c. L0 激活规则正反例完全下移 L1

**v1 建议**: L0 激活规则的正反例详表应该完全下移到 L1。
**作者部分接受**: 精简到每类 1-2 个 anchor 示例，不接受完全下移。

**我的回应**: **接受修订强度，不再坚持完全下移**。

v2 修订后的 L0 §6 (`:209-215`) 把正反例精简为：
- ✅ 必激活：1-2 个典型例
- ❌ 不激活：1 个典型例
- 🟡 边界模糊 → 倾向触发
- 完整详表指向 L2 query-behavior.md

这个取舍是合理的。L0 保留 anchor 示例（~12 行，占 L0 的 ~10%）给了 LLM 一个"激活还是不激活"的快速匹配模板，不需要 invoke L1。如果完全下移，LLM 在 happy path 遇到边界场景就只能 guess，而"倾向触发"规则在没有示例时很难执行（"什么算边界模糊？"）。

### 3d. Reopen 已 close 的 grilling 议题

**v1 建议**: 重新打开"cadence-init 作为 CLI"和"不迁移直接 deprecate v0.2.x"。
**作者拒绝**: grilling 已 close，用户已选定 (b) skill 形态和 C3 inline 迁移。

**我的回应**: **接受边界**。v1 review 提出这些替代选项是为了确保设计选项的完备性。作者和用户在 8 轮 grilling 中已充分讨论了这些 trade-off，并作出了明确选择。Hostile review 的角色是确保设计的完备性，不是推翻用户已经做的明确决策。这两个边界问题不再追究。

---

## 4. v2 引入的新问题

### 4.1 附录 B — Event Sourcing / DDD (修订 #13)

附录 B (`:804-859`) 引入了 Event Sourcing 和 DDD Bounded Context 两个范式作为"架构语言精化"。

**问题是**：这个附录在主文档的位置（Appendix B, 在 END OF BLUEPRINT 前最后一节）意味着 implementation owner 会读到它。虽然 B.3 (`:843-849`) 说"L0/L1/L2 和 bounded context 不冲突"，B.4 (`:853-858`) 说"Out of scope for Candidate A 主体"，但附录的存在本身可能误导实施者以为"A 实施完成后要做 event sourcing 改造"。

**建议**: 在附录顶部加一行 disambiguation：
> "本附录不暗示任何实施层面的优先方向。Candidate A 主体设计不依赖这些概念。"

或者直接放到 `docs/design/` 作为独立文档，不附在 blueprint 里。如果保留，至少在 B.4 中把"Out of scope for Candidate A 主体"加粗。

### 4.2 Phase A 内部原子性

Phase B Step 6 有显式"必须同 commit"约束 (`:436-441`)，但 Phase A Steps 1-4 没有。Phase A Step 1 删除 `scaffold-upgrader.md`，Step 2 重写 `cadence-init/SKILL.md`（不再调用 scaffold-upgrader）。如果有人在 Step 1 后 commit，中间状态有 dangling 引用。

**影响**: 低——Phase A 预计 1-2 小时，实施者不太可能在中途 commit。但如果实施者习惯于"每步一个 commit"的工作流，会踩坑。

**建议**: 在 Phase A 描述 (`:417`) 中加一句："Steps 1-4 建议同一 commit,至少确保 Step 1-2 在同一次 session 内连续完成(避免 cadence-init SKILL.md 引用已删除的 subagent)"。

### 4.3 L0 §5 强制 Read L2 指令

见 §1 修订 #9 的 minor concern。L0 §5 说"必须对照 L2...自检"但 L2 可能不在 context。如果实施时不加"如 L2 不在 context,先 Read 它"，LLM 可能习得性忽略这条指令。

### 4.4 ADR-002 "替代方案被拒绝"中的冗余论证

v2 ADR-002 的"session 启动强制 invoke project-discuss"拒绝理由 (`:637-640`) 现在包含了两个理由：
1. "LLM 可能在 invoke 完成前就响应用户首条发言"
2. "一旦 invoke,把 ~249 行 L1 内容全部吞进 context,对'轻量闲聊'场景是浪费"

第 1 个理由在 v1 review 中被批评为"不够充分"——可以在 bootstrap 里设强约束来缓解。第 2 个理由（v2 新增）更强。但两个放在一起可能让读者困惑"到底哪个是主要理由"。建议把第 2 个作为 primary reason，第 1 个作为 "additionally"。

这不是 blocking issue，但如果 ADR 要作为永久文档被未来维护者引用，论点的层次应该清晰。

---

## 5. Implementation Readiness

**Final verdict: (A) Ship now**

所有 v1 blocking issues (B1/B2/B3) 已解决。所有 v1 strong suggestions (S1/S2) 已采纳。v2 引入的新问题是 minor 级别，可以在实施时顺手处理。

### 实施时建议顺手修的 2 个 minor patches

1. **Phase A 内部原子性提示**：在 `:417` "独立可完成"后加一句 "（Steps 1-4 建议同 commit）"
2. **附录 B disambiguation**：在 `:804` "范式精化"后加一句 "本附录不改变 Candidate A 主体实施方向"

### v2 最坚实的修订

**ADR-002 的"鸡生蛋"重写 + Mode A/B 区分** (`:586-608`)。v1 review 提出的这个核心修正被完全采纳，且执行质量高于预期——"鸡生蛋"叙事比 v1 的任何建议都更精准，Mode A/B 区分表的结构化呈现清晰可操作。Precautionary Design 声明 (`:622-631`) 是一个 bonus：它展示了设计者在没有 telemetry 前提下的诚实保守主义。

### v2 最薄弱的修订

**附录 B** (`:804-859`)。附录的内容本身有 intellectual value（event sourcing 视角确实贴合 cadence 领域语义），但放在实施 blueprint 的附录里可能产生"实施暗示"的副作用。不过它在 `B.3` 和 `B.4` 中已做了足够的 scope limitation，所以不构成 blocking issue。

---

## 附录 A: 跟 v1 review 的关系

| v1 建议 | v2 采纳 | 我的回应 |
|---|---|---|
| **B1**: Phase A/B scaffold 删除 x bootstrap 重写同 commit | ✅ 采纳 | 已解决。Phase A 内部的 scaffold-upgrader/cadence-init 原子性可微调 |
| **B2**: "分层不染色"改为"防御性分层,受控渗透" | ✅ 采纳 (改为"L0 是 L2 精炼摘要") | 已解决。v2 叙事比 v1 建议更优 |
| **B3**: `_CONVENTIONS.md` 引用清单补全 + RUNBOOK 具体替换文本 | ✅ 采纳 | 已解决 |
| **S1**: L0 预算 110-130 | ✅ 采纳 | 已解决 |
| **S2**: harness-adapters 80-100,保留 XML 模板 | ✅ 采纳 | 已解决 |
| **ADR-002 "鸡生蛋"重写** | ✅ 采纳 | 已解决,执行质量高于预期 |
| **Mode A/B 区分** | ✅ 采纳 | 已解决 |
| **借口反驳 #3 下移** | ✅ 采纳 | 已解决 |
| **L0 激活规则精简** | ✅ 部分采纳 (不完全下移) | 接受 |
| **Graphviz 下移 L2** | ❌ 拒绝 | **撤回** — superpowers 实证表明 dot 图是有效 LLM behavior shaping |
| **1,867 行偏高 14%** | ❌ 拒绝 | **v1 算术错误,承认** |
| **Cadence-init 作为 CLI** | ❌ 拒绝 (grilling 已 close) | 接受边界 |
| **不迁移 deprecate v0.2.x** | ❌ 拒绝 (grilling 已 close) | 接受边界 |

---

## 附录 B: 行数验证

### B.1 目标行数可行性 (逐节)

**L0 (目标 110-130)**:
```
§0  frontmatter:                                        5
§1  ASSUME INTERRUPTION:                                5
§2  目录约定:                                           5
§3  项目档案落点:                                       7
§4  单判据「已被承接」:                                 15
§5  记录动作(含信息密度强制引用):                       12
§6  project-discuss 激活规则(精简):                     12
§7  三阶段名字 + meta-protocol:                         12
§8  Skill 正交并行 + 借口反驳表 4 项:                   25
§9  指向 L1/L2:                                         3
§10 Session 启动时的行为:                               10
────────────────────────────────────────────────────  ───
                                                      111
+ 自然留白 + 表格格式化标记:                           +0-19
────────────────────────────────────────────────────  ───
总计:                                                 ~111-130
```
预算可行。注意 §8 (25 行) 是最大风险点——4 项反驳 + 正交解释容易膨胀。实施时若超 130 行，优先压缩 §8 的"正交并行"解释段到 §1 或 §9。

**L1 (目标 ~180)**:
```
§0  frontmatter:                                        5
§1  讨论开始前:                                         15
§2  Phase 化骨架(含质量自检):                           30
§3  主 session 工作记忆:                                15
§4  _ACTIVE.md 段管理(含反驳#3):                        30
§5  记录位置分流:                                       15
§6  中途自检:                                           10
§7  特殊场景处理:                                       20
§8  话题词典 + 路由表(含 incident):                     15
§9  Session 结束提醒:                                   5
§10 graphviz 流程图:                                    20
────────────────────────────────────────────────────  ───
                                                      180
```
正好 180。graphviz 从 v1 的 ~25 行压缩到 ~20 行是合理的——superpowers 的 brainstorming dot 图（`brainstorming/SKILL.md:37-64`）27 行但更复杂，cadence 的两个图（段 trigger 决策 + phase 选择）应该可以控制在 20 行内。

**harness-adapters.md (目标 80-100)**:
```
§1  前言:                                               5
§2  6×3 适配表:                                         15
§3  Codex 调度铁律:                                     15
§4  XML wrapping 模板(完整,~17行):                      17
§5  OpenCode 形态差异:                                  10
§6  调试 tips:                                          15
frontmatter + 导航提示:                                 3
────────────────────────────────────────────────────  ───
                                                       80
+ 自然留白:                                            +0-20
────────────────────────────────────────────────────  ───
总计:                                                 ~80-100
```
80 行 nominal 处在这个区间的低端，加上 frontmatter 和自然留白后实际在 85-95。预算可行。

### B.2 源文件行数 (验证 1,867)

重新核对（与作者给出的清单一致）：
```
bootstrap/SKILL.md:                          104
project-discuss/SKILL.md:                    249
recording-protocol.md:                       368
query-behavior.md:                           248
incident-handling.md:                        141
doc-reliability-protocol.md:                  76
codex-tools.md:                              126
opencode-tools.md:                           100
_CONVENTIONS.md (plugin source/scaffold):    455
───────────────────────────────────────────  ───
9 份协议描述文件合计:                      1,867  ✓
```
