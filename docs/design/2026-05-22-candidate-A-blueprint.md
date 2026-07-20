# 架构改造方案 — Candidate A:协议单一来源化

> **版本**: **v2.2**(Candidate G grilling 完成后整合至 § 11)
> **修订日期**: 2026-05-22(v1 → v2 → v2.1 → v2.2 同日完成)
> **分支策略**: 本次所有改动只在 `dev-local` 分支累积,不立即合并到 `main` 或发版。Phase 切分目标从"独立可发布"放宽为"逻辑分组 + 每 commit 内部一致 + 提供 rollback path",允许 cross-Phase 状态过渡(但仍要避免 dev-local 中间状态自相矛盾)。

---

## Changelog v2.1 → v2.2

Candidate G grilling 完成(Round 14-19)。原 v2 blueprint § 9 标记的 "未解决相邻 issue (Candidate G — handoff 失血)" 已完成 design,**整合至本 blueprint § 11**。

**关键纠偏**(grilling 17-19 轮揭示):
- v2 假设 G root cause #3 (handoff 太薄) 是问题 — **砍掉**。handoff = 书签是 v0.3 对的设计哲学
- v2 假设 G root cause #1 是 schema compliance — **重新框架**为信息密度低(dogfood 信号)
- 砍 "接入 `validate_streaming.py` 到 plugin runtime"(Python validator 在 LLM-readable file 上是 misfit)
- G + D 解耦(不需要 candidate D 的 validator 路径统一)

**G 实施成本**: 纯 markdown 改动 ~50 行,无 Python / 无 subagent / 无 candidate D 依赖。Piggyback 到 candidate A Phase B。详 § 11。

---

## Changelog v2 → v2.1

deepseek-V4-Pro 对 v2 又做了一轮 review,见 `2026-05-22-deepseek-review-v2.md`。**verdict: Ship now**。3 项 minor patches 已内联:

| # | Patch | 位置 |
|---|---|---|
| 1 | Phase A Steps 1-2 加"同 commit"约束(避免 cadence-init/SKILL.md 引用已删的 scaffold-upgrader) | § 5 Phase A 顶部 |
| 2 | L0 §5 信息密度自检指令加"先 Read 一次后续复用"提示(避免每次 entry Read L2 膨胀 context) | § 4.1 L0 §5 |
| 3 | 附录 B 顶部加 disambiguation(避免实施者误以为要做 event sourcing 改造) | 附录 B 顶部 |

**拒绝**的 deepseek v2 建议:
- ❌ ADR-002 "L0 写错时以 L2 为准" → "L0 描述与 L2 有歧义时"(不必要的 wordsmithing)
- 🟡 ADR-002 拒绝理由层次重新组织(cosmetic,选择性不动)

---

## Changelog v1 → v2

deepseek-V4-Pro 做了 hostile review,见 `2026-05-22-deepseek-review-v1.md`。本 v2 采纳的修订:

| # | 类别 | 修订 |
|---|---|---|
| 1 | 实施 | **B1 修正**: Phase A 不再含「删 `_CONVENTIONS.md` scaffold」,该动作移到 Phase B 第一步,跟 bootstrap 重写**同一个 commit**(避免 dev-local 中途状态出现 bootstrap 引用 dangling)|
| 2 | 叙事 | **B2 修正**: D7 从「分层不染色」改为「分层职责清晰,L0 是 L2 的精炼摘要,单一权威源在 L2」。承认 L0/L2 之间是 summary↔detail 关系。|
| 3 | 文档 | **B3 修正**: § 3.4 引用清单补充注明 `skills/cadence-init/SKILL.md` 含 12 处 `_CONVENTIONS.md` 引用(随文件整体重写消失)|
| 4 | 预算 | **S1 修正**: L0 体量预算从 `~95 行` 调到 `~110-130 行`(以 superpowers 118 行为参考,cadence 多了 happy path 协议)|
| 5 | 预算 | **S2 修正**: `harness-adapters.md` 预算从 `~60 行` 调到 `~80-100 行`(保留 Codex XML wrapping 模板的操作性)|
| 6 | ADR | **ADR-002 核心论证重写**: 从「常驻监察 skill」叙事改为「鸡生蛋」叙事(更精确),并区分 Mode A(首发漏激活)vs Mode B(已激活但单条 rationalize)|
| 7 | 设计 | **借口反驳 #3 下移**: L0 借口反驳表从 5 项削到 4 项(#1/#2/#4/#5),#3「上限到了再问归档」依赖 L1 段管理概念,下移到 L1 旁边 |
| 8 | 设计 | **L0 §5 激活规则正反例精简**: 从 4+3 类全部展开改为每类 1-2 个 anchor 示例(节省 ~6 行)|
| 9 | 设计 | **Candidate G 兼容性预防 3 条**(对抗 G root cause):L0 §4 强化信息密度引用 / L2 顶部加导航 / L1 Phase 1 加自检 |
| 10 | 文档 | **`.codex/RUNBOOK.md`** 引用给出具体替换文本(不再只说"改为指 plugin 内")|
| 11 | ADR | **ADR-001 补 context budget 角度** + **ADR-002 加 precautionary design 声明**(承认缺 dogfood telemetry 时是保守设计)|
| 12 | 验证 | § 7 验证清单加 `harness-adapters.md` 引用 grep 检查 |
| 13 | 新增 | **附录 B**:Event sourcing / DDD bounded context 范式精化(acknowledge deepseek 提议)|

明确**拒绝**的 deepseek 建议(理由见 deepseek review 报告我的回应):
- ❌ "L1 graphviz 流程图应该下移 L2"(graphviz 是 LLM behavior shaping 实证有效手段,superpowers 大量使用)
- ❌ "协议总量 1,867 行偏高 14%"(deepseek 算术错误,自己列的清单总和不是 1,640)
- ❌ "L0 激活规则正反例完全下移 L1"(L0 happy path 必须含 anchor 示例,但接受精简)
- ❌ Reopen "Candidate-init 作为 CLI 而非 skill"(grilling 已 close,用户选定 skill 形态)
- ❌ Reopen "不迁移直接 deprecate v0.2.x"(grilling 已 close,用户选定 C3)

---

## 0. 一句话定位

把当前散布在 7 个文件、共 1,867 行的「cadence 记录协议」收敛为**3 层架构**(L0 注入 / L1 skill 入口 / L2 细则,L0 是 L2 的精炼摘要),用户项目内不再写协议副本(`_CONVENTIONS.md` 删除)。

预计净瘦身 ~880 行(47%)。更重要的是:每个协议不变量**单一权威源在 L2**,L0 是 actionable summary。

---

## 1. 9 项核心决策(v2 修订后)

| # | 决策 | 状态 |
|---|---|---|
| **D1** | `_CONVENTIONS.md` scaffold 删除,不再写入用户项目 | ✅ |
| **D2** | `cadence-init` 形态 = `(b)` marker + 状态档骨架,可选 `(c)` project-scanner | ✅ |
| **D3** | `cadence-init` 补全模式删除,改"已 init 时友好提示 `[r/n]`" | ✅ |
| **D4** | `cadence-init` Step 1a.4 `_CONVENTIONS.md` 升级检查整段删除 | ✅ |
| **D5** | Step 1a 旧版本迁移走 **C3** — inline 在 SKILL.md 主流程,删除 `scaffold-upgrader.md` subagent | ✅ |
| **D6** | `cadence-init` 已废弃的 Step 4 CLAUDE.md fragment 段删除 | ✅ |
| **D7** | 协议 3 层(L0 注入 / L1 skill / L2 references)。**L0 是 L2 的精炼摘要,单一权威源在 L2,L0 写错时以 L2 为准**(v2 叙事修正)| ✅ |
| **D8** | L0 内容承诺 — `cadence-bootstrap/SKILL.md` **~110-130 行**(v2 上调),含 happy path 协议 + meta-protocol + 借口反驳表 4 项(#1/#2/#4/#5)| ✅ |
| **D9** | L2 合并方向 — 5 份 references → 3 份(`recording-protocol`+incident、`query-behavior`+doc-reliability、`harness-adapters` ~80-100 行,合并 codex+opencode 保留 XML 模板)| ✅ |

外加 2 个 ADR:
- **ADR-001**: `opt-in via cadence-init` 是 feature(v2 补 context budget 角度)
- **ADR-002**: L0 注入层必须 inline happy path 协议(v2 重写"鸡生蛋"核心论证 + 区分 Mode A/B)

ADR 全文见 § 6。

---

## 2. 当前状态 → 目标状态

```
   当前:                                       目标(v2):
   ─────                                       ──────────
   
   plugin 内 9 份含协议描述的文件,1,867 行     plugin 内 5 份,~985 行
   
   bootstrap/SKILL.md  ────┐                  bootstrap/SKILL.md (L0, ~110-130 行)
   ├──── 协议核心(重复)  │                  ├── happy path 协议(L2 精炼摘要)
   ├──── 借口反驳引子    │                  ├── meta-protocol
   └──── Codex 调度铁律 │                  └── 借口反驳表 4 项 (#1/#2/#4/#5)
                         │
   project-discuss/SKILL ──┤                  project-discuss/SKILL (L1, ~180 行)
   ├──── 借口反驳表      │                  ├── 加载策略
   ├──── 三阶段骨架     │ 相互重复          ├── 段独立 70/100 阈值
   └──── 中途自检       │                  ├── Phase 化骨架(指针)
                         │                  ├── 借口反驳 #3(段管理旁边)
   references/recording  ┤                  ├── 中途自检
   ├──── 单判据完整版    │                  └── 特殊场景处理 + 路由表(加 incident)
   ├──── 借口反驳表      │
   └──── 三阶段细则     │                  references/
                         │                  ├── recording-protocol.md (L2 权威,~400 行)
   references/query     ─┤                  │   含 incident 附录;顶部加导航 "🔥 信息密度正反例"
   references/incident  ─┤                  ├── query-behavior.md (L2, ~280 行)
   references/doc-rel   ─┤                  │   含 doc-reliability
   references/codex-tools┤                  └── harness-adapters.md (L2, ~80-100 行)
   references/opencode  ─┘                      合并 codex + opencode,保留 XML 模板
   
   用户项目内:                                  用户项目内:
   cadence/_CONVENTIONS.md (455 行 frozen)    cadence/_CONVENTIONS.md ✂️ 不再存在
```

净瘦身估算:

```
                              当前        目标        净改动
   ─────────────────────────────────────────────────────────
   plugin 内 9 份协议描述     1,867       985        -882 行 (-47%)
   用户项目 _CONVENTIONS      455         0          -455 行
   scaffold-upgrader         123         0          -123 行
   cadence-init/SKILL        230         85         -145 行 (-63%)
   ─────────────────────────────────────────────────────────
   合计                                              ~-1,600 行
```

---

## 3. 文件级改动清单

### 3.1 删除(完全消失)

| 文件 | 行数 | 原因 | 删除时机 |
|---|---|---|---|
| `skills/cadence-init/scaffolds/_CONVENTIONS.md` | 455 | scaffold 不再写入用户项目(D1)| **Phase B 第一步**(v2 修正:跟 bootstrap 重写同 commit)|
| `skills/cadence-init/agents/scaffold-upgrader.md` | 123 | 迁移流程 inline,subagent 抽象不必要(D5)| Phase A |
| `skills/project-discuss/references/incident-handling.md` | 141 | 70% 内容跟 recording-protocol 重叠,合并为附录(D9)| Phase B |
| `skills/project-discuss/references/doc-reliability-protocol.md` | 76 | L1-L4 等内容合并到 query-behavior.md(D9)| Phase B |
| `skills/project-discuss/references/codex-tools.md` | 126 | 合并到新文件 harness-adapters.md(D9)| Phase B |
| `skills/project-discuss/references/opencode-tools.md` | 100 | 合并到新文件 harness-adapters.md(D9)| Phase B |

### 3.2 重写(大幅修改)

| 文件 | 当前行数 | 目标行数 | 主要变化 |
|---|---|---|---|
| `skills/cadence-bootstrap/SKILL.md` | 104 | **~110-130**(v2)| L0 重新定位 — 含 happy path + meta + 借口反驳表 **4 项**(详 § 4.1)|
| `skills/project-discuss/SKILL.md` | 249 | ~180 | L1 — 删除已上移 L0 的内容、加借口反驳 #3、路由表加 incident、加 graphviz 流程图(详 § 4.2)|
| `skills/project-discuss/references/recording-protocol.md` | 368 | ~400 | 合并 incident 内容为 § 9 附录 + 顶部加导航(详 § 4.3.1)|
| `skills/project-discuss/references/query-behavior.md` | 248 | ~280 | 合并 doc-reliability 为 § 11 节(详 § 4.3.2)|
| `skills/cadence-init/SKILL.md` | 230 | ~85 | 大幅瘦身(详 § 4.4)|

### 3.3 新建

| 文件 | 预计行数 | 用途 |
|---|---|---|
| `skills/project-discuss/references/harness-adapters.md` | **~80-100**(v2)| 合并 codex-tools + opencode-tools 为统一 6×3 适配表 + **保留 Codex XML wrapping 模板** |
| `docs/adr/001-opt-in-via-cadence-init.md` | ~35 | ADR-001(v2 补 context budget 角度)|
| `docs/adr/002-bootstrap-must-inline-happy-path.md` | ~55 | ADR-002(v2 重写"鸡生蛋"论证 + Mode A/B 区分)|

### 3.4 受影响但仅小修

需要把对 `_CONVENTIONS.md` 的引用全部移除或改指 plugin 内 references:

| 文件 | 引用次数 | 改动 |
|---|---|---|
| `skills/cadence-bootstrap/SKILL.md` | 4 处(L18/L32/L70/L80)| 全部改指 project-discuss SKILL.md / references/(随 § 3.2 重写消化)|
| `skills/project-discuss/SKILL.md` | 1 处(L166)| 改为 inline,不再引用 `_CONVENTIONS.md` 的「征询图景」 |
| `skills/cadence-handoff/agents/handoff-writer.md` | 2 处(L144/L209)| 不动 — 该 subagent 在 candidate C 整文件删除 |
| `skills/cadence-init/agents/scaffold-upgrader.md` | 2 处(L115/L119)| 整个文件删除(§ 3.1)|
| `skills/cadence-init/scaffolds/_ACTIVE.md` | 1 处(L27)| 删除该 hint(LLM 靠 bootstrap 注入知道协议)|
| `skills/cadence-init/scaffolds/_INDEX.md` | 1 处(L23)| 删除"项目约定: _CONVENTIONS.md" 行 |
| **`skills/cadence-init/SKILL.md`** | **12 处**(v2 新加,L30/L47/L69/L71/L73/L79/L88/L89/L94/L109/L190/L215)| **随该文件整体重写(§ 4.4)自然消失,不单独列**|
| `.codex/RUNBOOK.md` | 1 处(L62)| **(v2 具体化)** smoke test 清单中将"`cadence/_CONVENTIONS.md` 存在性检查"替换为"`cadence/_INDEX.md` + `cadence/_ACTIVE.md` 存在性检查"|

### 3.5 保留(不改)

- `skills/cadence-init/agents/project-scanner.md`(服务可选 c)
- `skills/cadence-init/references/scan-rules.md`(scanner 的 dependency)
- 全部 7 个 subagent 中除 scaffold-upgrader 外的 6 个
- `hooks/session-start`、`hooks/run-hook.cmd`、`hooks/hooks.json`
- `tests/test_session_start_hook.py`(应仍通过)

---

## 4. 三层各自的内容清单(v2 修订)

### 4.1 L0 — `cadence-bootstrap/SKILL.md`(~110-130 行,v2 上调预算)

```
   §0  frontmatter (name + description)                              ~5 行
   
   §1  ★ ASSUME INTERRUPTION ★ (v2 前移)                            ~5 行
       · /compact 后必须重做 session 启动步骤
       · 不假设"上次读过的还在"
   
   §2  目录约定                                                       ~5 行
       · 产物在 cadence/(不在 docs/)
       · 事项真实状态以 _ACTIVE.md 为准
   
   §3  项目档案落点                                                   ~7 行
       · 决策 → _ACTIVE.md 活跃决策
       · 待决 → _ACTIVE.md 待决清单
       · TODO → _ACTIVE.md TODO
       · 完整 reasoning → discussions/<date>-<slug>.md
       · 流式记录 → streaming/<YYYY-MM-DD>-<topic>.md
   
   §4  单判据「已被承接」(L2 精炼摘要)                              ~15 行
       · 一句话定义 + 承接对象覆盖"结论 OR 中间决定"
       · 强信号 3 项(嗯/好/OK; 基于此推进; 引用此决定)
       · 弱信号 2 项(沉默; 反问)
       · "倾向漏记 > 噪音"
   
   §5  记录动作(happy path)                                         ~12 行
       · 命中判据 → append streaming entry
       · entry 最小 schema (^entry-id [ts] 摘要 + chosen 必填)
       · context/options/rejected 选填
       · ★ (v2 强化) **写 entry 时必须对照 L2 recording-protocol.md §2
                       的「信息密度正反例」自检**——密度过低的 entry 会导致
                       下游 session 信息偏差(dogfood 实证)
       · ★ (v2.1 加) 如本 session 未 Read 过该节,**先 Read 一次后续复用**
                       (不要每次 entry 重读 — context 膨胀)
       · 告知一行 "📝 已记: ..."
   
   §6  project-discuss 激活规则(v2 精简正反例 anchor)               ~12 行
       · session 首条"项目相关"发言 → 必须 Skill("project-discuss")
       · ✅ 必激活(典型例 1-2 个):"用 Postgres" / "改 Auth"
       · ❌ 不激活(典型例 1 个):"React hooks 怎么用"
       · 🟡 边界模糊 → 倾向触发
       · ⚠️ 中途自检:已决策但 _ACTIVE/streaming 空 → 立即补调追溯征询
       · 完整正反例详表见 L2 query-behavior.md「修改/扩展类查询前置」节
   
   §7  三阶段名字 + meta-protocol                                    ~12 行
       · 记(α) / 整(ε) / 查(ρ) 各自谁写、谁触发、subagent 名
       · subagent 调度铁律:只读 / Plan-only / 主 session 唯一写者
       · Codex 形态额外强制 spawn(指向 L2 harness-adapters)
   
   §8  Skill 正交并行 + 借口反驳表 4 项(v2 削到 4 项)              ~25 行
       · project-discuss 与 brainstorming/writing-plans/etc 正交
       · "调用了流程 skill ≠ 跳过 project-discuss"
       · 借口反驳:
         #1 流程 skill 已激活,project-discuss 可跳过 → 错,正交
         #2 用户没明确说要记 → 错,承接信号已扩展(中间决定)
         #4 概念太多,简化执行 → 错,已简化到 3 Phase,不要凭印象
         #5 这条不重要,先不写 archive → 错,判断标准是承接信号不是主观感觉
         (#3「上限到了再问归档」下移 L1,见 § 4.2)
   
   §9  指向 L1/L2                                                    ~3 行
       · 完整协议:Skill("project-discuss")
       · 细则单一权威源:references/recording-protocol.md / query-behavior.md / harness-adapters.md
       · L0 是上述细则的精炼摘要,冲突时以 L2 为准
   
   §10 Session 启动时的行为(必做)                                  ~10 行
       · 列目录 + 读 _INDEX.md(若存在)
       · 按用户首发言话题决定读哪个具体文档
   
   ────────────────────────────────────────────────────
   预算合计: ~111 行(含表格 + 适度留白)
   接受 ±20 行浮动,目标区间 110-130 行
```

### 4.2 L1 — `project-discuss/SKILL.md`(~180 行)

```
   §0  frontmatter                                                   ~5 行
   §1  讨论开始前(必做)                                             ~15 行
       · 检查 cadence 骨架是否存在
       · 建立全局上下文(读 _INDEX.md / 按需读 _ACTIVE.md)
   
   §2  Phase 化协议骨架(记 / 整 / 查)                              ~30 行
       · Phase 1 记 — 触发 / 落点 / 告知 / 铁律
         · ★ (v2 加) 质量自检:对照 L2 recording-protocol.md §2「信息
           密度正反例」自检 entry 密度
       · Phase 2 整 — 触发条件 5 类 / consolidator 流程(指向 L2)
       · Phase 3 查 — 触发 / retriever 流程 / 硬限(指向 L2)
       · recall-analyzer(决策前回忆分析)
   
   §3  主 session 工作记忆(v0.4 lifecycle)                         ~15 行
       · n_rounds_counter / recent_user_turns / git_log_window
   
   §4  _ACTIVE.md 段独立管理                                         ~30 行
       · 段独立条数上限表
       · 软警告 70% / 硬阈值 100% 切换
       · ★ (v2 加) 借口反驳 #3:"上限到了再问用户怎么归档" → 错,70%
                   软警告时 consolidator 已经静默处理了,不要等 100%
       · Undo 协议
       · 补救路径
   
   §5  记录位置分流(完整表)                                        ~15 行
       · 完整内容类型 → 写入位置映射
   
   §6  中途自检                                                      ~10 行
       · session 进行中发现未触发 → 立即激活 + 追溯征询
   
   §7  特殊场景处理                                                  ~20 行
       · 查询类 / 修改类 / 导航类
   
   §8  话题词典维护 + 路由表(v2 加 incident 路由)                 ~15 行
       · 每次写决策后顺手更新 _INDEX.md 话题词典
       · 文档 > 10 时启用 _INDEX-ROUTING.md
       · ★ (v2 加) 路由表显式条目:
         · Incident 记录 → references/recording-protocol.md §9(附录)
         · 文档可信度 L1-L4 → references/query-behavior.md §11
         · Harness 适配 → references/harness-adapters.md
   
   §9  Session 结束提醒(克制版)                                    ~5 行
   §10 内嵌 graphviz 流程图(LLM behavior shaping 工具)             ~20 行
       · 段独立 trigger 决策流(70/100/段满 → consolidator 路径)
       · phase 选择流(用户发言 → 记 vs 整 vs 查)
   
   ────────────────────────────────────────────────────
   不再 inline:
   · 借口反驳 #1/#2/#4/#5 → L0
   · 单判据完整定义 → L0 (摘要) + L2 (细则,权威)
   · 三阶段细则 → L2 (权威)
   · 隐含确认信号详表 → L2
   · 加载策略 4 trigger → L2
```

### 4.3 L2 — `references/`(3 份,**单一权威源**)

#### 4.3.1 `recording-protocol.md`(~400 行,含 incident 附录)

```
   ★ (v2 加) 顶部导航提示                                            ~3 行
   ────────────────────────────────────────────────────
   > 🔥 **写 streaming entry 前必读**:§2 「信息密度正反例」
   > 🔥 **incident 记录请直接跳 §9 附录**
   ────────────────────────────────────────────────────
   
   §1  记录单判据 (完整版,L0 是精炼摘要)                            ~30 行
   §2  记 阶段(Phase 1: Record)                                    ~80 行
       · 触发条件 / 落点表
       · 写入原则:假设读者无上下文
       · ★ 信息密度正反例(L0 §5 强制对照此节)
       · Entry schema(完整)
       · Tombstone(撤回)
       · 输出(告知格式)
   §3  整 阶段(Phase 2: Consolidate)                               ~50 行
   §4  查 阶段(Phase 3: Retrieve)                                  ~30 行
   §5  共享行为                                                      ~80 行
   §6  边界与禁忌                                                    ~40 行
   §7  历史脉络                                                      ~10 行
   §8  (v2 移走) 借口反驳表 → 上移 L0 (#1/#2/#4/#5) + L1 (#3),L2 不再保留
   §9  ★ Incident 附录 ★ (合并自 incident-handling.md)              ~70 行
       · Incident 触发条件
       · 三阶段在 incident 场景的应用(简化叙述)
       · 完整模板 + 摘要模板
       · 模板选择判据
```

#### 4.3.2 `query-behavior.md`(~280 行,含 doc-reliability)

```
   §1  查询优先级                                                    ~20 行
   §2  加载策略                                                      ~30 行
   §3  代码复核的时机                                                ~10 行
   §4  冲突处理                                                      ~10 行
   §5  新信息补档征询                                                ~10 行
   §6  历史决策遗忘场景                                              ~10 行
   §7  查询行为的克制                                                ~5 行
   §8  修改/扩展类动作前的查询前置                                   ~30 行
       (L0 §6 的"完整正反例详表"指向此节)
   §9  4 trigger 主动重读                                            ~25 行
   §10 路由表管理                                                    ~50 行
   §11 ★ 文档可信度协议 ★ (合并自 doc-reliability-protocol.md)       ~60 行
       · L1-L4 信息分级表
       · 事实性 / 意图性问题查询行为
       · 实际举例
```

#### 4.3.3 `harness-adapters.md`(**~80-100 行**,v2 上调,合并 codex+opencode)

```
   §1  前言:LLM 自适应原则                                          ~5 行
   §2  6×3 适配表(核心)                                            ~15 行
   §3  Codex 调度铁律(脚注,保留强祈使句)                          ~15 行
       · 历史检索 / 整合归档 / 决策前回忆分析三类必须 spawn_agent
       · 三大铁律理由
       · 反例(禁止)
   §4  ★ Codex XML message wrapping 模板 ★(v2 保留完整,~17 行)
       · subagent 调度时的完整 XML 包裹格式
       · 不压缩为伪代码
   §5  OpenCode 形态差异(v2 保留显式说明)                          ~10 行
       · OpenCode 跟 CC behavior 1:1 alignment
       · 无 Codex 级保守策略
       · 防止 LLM 在 OpenCode 上误用 Codex 级铁律
   §6  调试 tips                                                     ~15 行
       · Codex sandbox 拒 rg
       · OpenCode plugin 加载失败 troubleshooting
```

### 4.4 `cadence-init/SKILL.md`(~85 行)

```
   §0  frontmatter                                                   ~5 行
   §1  检查现有状态                                                  ~10 行
       · cadence/_INDEX.md + _ACTIVE.md 都在 → "已初始化,要重做项目快照吗? [r/n]"
       · _INDEX.md 在 + _ACTIVE.md 不在(v0.2.x 旧格式)→ Step 2 迁移
       · 都不在 → Step 3 init
       · 异常 → 提示用户
   
   §2  v0.2.x 旧版本迁移(C3 inline)                               ~30 行
       · 提示 + Y/N(commit 建议)
       · 主 session 直接 Read _INDEX.md
       · 解析 4 个 section
       · Edit _INDEX.md + Write _ACTIVE.md
       · 处理 8 条上限超限(inline 三档选项)
       · 更新话题词典 pointer
       · 完成告知
   
   §3  init 主流程                                                   ~35 行
       · 判断项目状态:新 / 已有
       · 新项目模式(b):创建 _INDEX.md / _ACTIVE.md / discussions/ / _archive/
       · 已有项目模式:询问 [A 扫描 / B 跳过]
       · A 模式调 project-scanner subagent
       · scanner 返回 suggested_index_fields → Y/e<编号>/N 处理
       · 不再写 _CONVENTIONS.md
   
   §4  汇报产物 + 下一步建议                                         ~5 行
```

---

## 5. 实施步骤次序(v2 重新切分,dev-local 累积)

> **dev-local 分支策略**(v2 新增): 本次所有改动只在 `dev-local` 分支累积,
> 不立即合并到 `main` 或发版。Phase 切分目标从"独立可发布"放宽为"逻辑分组 +
> 每 commit 内部一致 + 提供 rollback path"。但**不允许 dev-local 中间 commit
> 出现自相矛盾**(如 scaffold 删了但 bootstrap 仍引用它)—— 跨 Phase 的依赖
> 必须在同一 commit 内完成。

### Phase A — cadence-init 简化(独立可完成)

预计耗时:1-2 小时

> ⚠️ **v2.1 加**: Steps 1-2 **建议同一 commit**(或确保连续完成,中间不 commit)。
> 原因: Step 1 删除 `scaffold-upgrader.md` 后,如果立即 commit,中间状态的
> `cadence-init/SKILL.md` 仍引用已删除的 subagent(L60 附近的"调用 `scaffold-upgrader` subagent")。
> 必须 Step 2 重写 `cadence-init/SKILL.md` 后才能 commit。

1. **删除 scaffold-upgrader**: `rm skills/cadence-init/agents/scaffold-upgrader.md`
2. **重写 `cadence-init/SKILL.md`**: 按 § 4.4 骨架 — 删 Step 1a.4 / 补全模式 / 已废弃 Step 4,inline Step 1a 迁移流程
3. **更新 scaffold 引用**: 修改 `cadence-init/scaffolds/_ACTIVE.md` L27 和 `_INDEX.md` L23 删除对 `_CONVENTIONS.md` 的引用
4. **commit + 验证**: `python -m pytest tests/test_session_start_hook.py` 应仍通过

> ⚠️ **v2 修正(B1)**: Phase A **不**删除 `_CONVENTIONS.md` scaffold。
> 原因:bootstrap 仍有 4 处 `_CONVENTIONS.md` 引用,删 scaffold 会让 bootstrap
> 引用 dangling。删 scaffold 推迟到 Phase B 第一步,跟 bootstrap 重写同 commit。

### Phase B — 协议三层化(核心改造)

预计耗时:3-5 小时

5. **新建 ADR**(可任意 commit 时机):
   - 创建 `docs/adr/` 目录(若不存在)
   - 写入 ADR-001 + ADR-002(全文见 § 6)
6. **★ commit X — bootstrap 重写 + scaffold 删除(B1 修正,必须同 commit)★**:
   - 6a. **删除 scaffold**: `rm skills/cadence-init/scaffolds/_CONVENTIONS.md`
   - 6b. **重写 `cadence-bootstrap/SKILL.md`**: 按 § 4.1 骨架,目标 ~110-130 行,含借口反驳表 4 项(#1/#2/#4/#5)
   - 6c. 删除 bootstrap 的 4 处 `_CONVENTIONS.md` 引用(L18/L32/L70/L80 → 改指 plugin 内 references)
   - 6d. **commit 单步骤完成**,不允许只跑 6a 或只跑 6b
7. **重写 `project-discuss/SKILL.md`**: 按 § 4.2 骨架,加 graphviz 流程图 + 借口反驳 #3
8. **重写 `recording-protocol.md`**: 按 § 4.3.1,合并 incident 为 §9 附录,删除 §7 借口反驳表,顶部加导航
9. **重写 `query-behavior.md`**: 按 § 4.3.2,合并 doc-reliability 为 §11
10. **新建 `harness-adapters.md`**: 按 § 4.3.3 骨架,**保留 XML wrapping 模板**
11. **删除合并源文件**:
    - `rm skills/project-discuss/references/incident-handling.md`
    - `rm skills/project-discuss/references/doc-reliability-protocol.md`
    - `rm skills/project-discuss/references/codex-tools.md`
    - `rm skills/project-discuss/references/opencode-tools.md`
12. **更新 project-discuss/SKILL.md L166** 引用 `_CONVENTIONS.md` 的「征询图景」改为 inline
13. **更新 `.codex/RUNBOOK.md` L62**(v2 具体化): "`cadence/_CONVENTIONS.md` 存在性检查" → "`cadence/_INDEX.md` + `cadence/_ACTIVE.md` 存在性检查"

### Phase C — Validation

预计耗时:1 小时

14. **静态 grep 检查**(见 § 7.1)
15. **跑测试**: `python -m pytest tests/`(全部应通过)
16. **手动 dogfood**(在另一个项目跑 `/cadence-init`):
    - 不创建 `_CONVENTIONS.md` ✓
    - 创建 `_INDEX.md` + `_ACTIVE.md` + 目录骨架 ✓
    - 跑两次第二次提示 `[r/n]` ✓
17. **bootstrap 注入验证**: `/clear` 后看 LLM 是否收到新版 bootstrap(含借口反驳表 4 项 inline 在 L0)
18. **Migration 验证(可选)**: 找一个 v0.2.x 老格式项目跑 cadence-init,确认 Step 1a inline 迁移成功

### Rollback path(v2 加)

由于在 `dev-local` 累积,rollback 简单:

```bash
# 单 commit 出错
git reset --hard HEAD~1

# 整个 Phase 出错(找到 Phase 起点 commit)
git log --oneline | grep "Phase A start"
git reset --hard <commit-sha>

# 整个 candidate A 出错,放弃改造
git checkout main  # dev-local 仍可保留作为存档
```

**关键不变量**: Phase B Step 6(bootstrap + scaffold 同 commit)必须 atomic,否则 dev-local 中间状态 broken。

---

## 6. ADR 草稿(v2 修订)

### ADR-001: Explicit opt-in via cadence-init(v2 补 context budget 角度)

```markdown
# ADR-001: Explicit opt-in via cadence-init

**Status**: Accepted
**Date**: 2026-05-22
**Deciders**: hxt9805
**Context**: Architecture review 2026-05-22 (Candidate A grilling Q2)
**Reviewers**: deepseek-V4-Pro (hostile review, 2026-05-22)

## Context

cadence 是一个 session-scoped 的讨论记录 / 整合 / 检索工作流插件。当用户全局
安装 cadence 后,问题是 cadence 何时在某个具体项目中激活。

可能的策略:
- A. **explicit opt-in**:用户必须显式跑 `/cadence-init`,创建
  `cadence/_INDEX.md` marker;SessionStart hook 据此守门
- B. **auto-on**:全局安装即在所有项目生效
- C. **首发激活**:LLM 在 session 首条用户发言时主动询问"要激活吗"

## Decision

采用 A — **explicit opt-in via `cadence-init`**。

## Rationale

1. **不污染非 cadence 项目**:全局插件的最大风险是被不想用的项目误激活。
   显式 marker 把"是否启用"明确成单一信号。
2. **可预测性**:用户/团队清楚知道某项目是否启用 cadence,不依赖 LLM
   启发式判断(C 方案的非确定性)。
3. **零代价沉默**:对未 init 项目,plugin 跟没装一样。
4. **(v2 新加) Context budget 节约**:全局安装但只在部分项目用 cadence 的
   常见 case 下,explicit opt-in 让未启用项目每次 session 启动节省 ~110-130 行
   bootstrap 注入开销 + 后续可能的 project-discuss 加载开销。

## Consequences

**正向**:
+ cadence 不污染非 cadence 项目
+ 是否启用信号清晰(单文件存在性)
+ 没有 false positive 触发
+ context budget 在未启用项目中归零

**负向**:
- 全局安装但忘 init 的用户体验为"插件不工作"(silent)
- 用户须为每个想用 cadence 的项目显式 init

## Considered Alternatives

- **auto-on**:拒绝 — 污染所有项目
- **首发激活**(LLM 主动询问):拒绝 —
  · LLM 非确定性触发,用户没控制感
  · 触发时机难预测,可能在用户敲第一条话后才询问,体验割裂
  · 已激活项目和未激活项目混在一起,认知负担

## When to Revisit

如 dogfood 数据显示大量用户全局安装后忘 init(silent failure 频发),重新
考虑增加一次性"首次进入未 init 项目时静默提示"机制(不改 opt-in 本质,
只增加发现性,如 SessionStart hook 检测到非 cadence 项目时追加一行
`[cadence 已安装但未在此项目激活。运行 /cadence-init 开始使用。]`)。

**(v2 加) 数据收集 gap**: cadence 当前无遥测。Revisit trigger 暂以
"用户主动反馈"为准。
```

### ADR-002: Bootstrap (L0) must inline happy-path recording protocol(v2 重写)

```markdown
# ADR-002: Bootstrap (L0) must inline happy-path recording protocol

**Status**: Accepted (v2 修订)
**Date**: 2026-05-22
**Deciders**: hxt9805
**Context**: Architecture review 2026-05-22 (Candidate A grilling round 6, 8 + deepseek hostile review)

## Context

cadence-bootstrap/SKILL.md 在 SessionStart 时被 hook 注入到 LLM context。
设计上有两种倾向:
- 极简(类似 superpowers' using-superpowers,~118 行,0 协议内容)
- 自包含(inline happy path 协议)

## Decision

L0 (cadence-bootstrap/SKILL.md) **必须 inline 以下内容**(目标 110-130 行):

1. 单判据「已被承接」摘要(L2 recording-protocol §1 的精炼)
2. 记录动作 happy path(entry 落点 + minimal schema + 信息密度强制引用)
3. `project-discuss` 激活规则(精简到 anchor 示例,详表指向 L2)
4. 三阶段名字 + subagent 调度 meta-rules
5. 借口反驳表 4 项(#1/#2/#4/#5,#3 依赖段管理概念下移 L1)

## Rationale (v2 重写 —— "鸡生蛋"论证)

cadence 的核心 paradox:**要正确记录决策就需要 `project-discuss` 的协议规则,
但 `project-discuss` 的规则需要在「已被承接」判据命中时才能加载到 context**。

如果 L0 极简(只含 meta-protocol),LLM 在首条用户发言时:
- 没看到记录协议 → 不知道该不该记
- 没 invoke project-discuss → 看不到完整协议
- 完成响应 → 决策已经过去,后续 invoke project-discuss 也救不回

L0 inline happy-path 协议直接解决这个鸡生蛋:LLM 在 session 启动后已经
"自带"了核心记录规则,即使没 invoke project-discuss 也能记录关键决策。

### 区分两种 failure mode(v2 加)

ADR-002 实际防备两种不同的失败模式,各自有不同的论证:

| Failure Mode | 描述 | 防御机制 | 概率 |
|---|---|---|---|
| **Mode A** | 首发言未被识别"项目相关",`project-discuss` 未激活 | L0 inline happy path 协议(单判据 + 记录动作) | 未知(需 dogfood)|
| **Mode B** | `project-discuss` 已激活,但 LLM 在单条决策时 rationalize 不记录 | L0 inline 借口反驳表 4 项 | 显然高于 Mode A |

借口反驳表放 L0 的真正价值是 **Mode B 防御**:即使 project-discuss 已激活,
LLM 在决策瞬间 rationalize 时**不会去翻 L2 recording-protocol.md 的 §7**。
L0 让反驳表始终在 context 里,LLM 在做"记不记"判断时**零延迟匹配**。

## Consequences

**正向**:
+ 鸡生蛋问题被打破,首发言决策不再可能完全漏记
+ Mode B 防御零延迟(LLM 看到借口立即匹配反驳)
+ Gate 1 漏触发的代价从"灾难"降为"边界用法缺失"

**负向**:
- bootstrap 注入比 superpowers using-superpowers 长(~110-130 行 vs 118 行,
  cadence 多了 happy path 协议)
- 每个 cadence session ~25-40 行的"always-injected"协议开销

## (v2 新加) Precautionary Design 声明

本 ADR 的 Mode A 防御论证缺少 dogfood telemetry 支持 — "首发漏激活会导致
失血"是 hypothesis 不是 fact。在 cadence 当前无遥测的前提下,本设计是
**precautionary design**(预防性设计):

- 缺数据时倾向保守(L0 inline 协议)而非冒险(L0 极简)
- 当 dogfood 数据可得时,重新评估 Mode A 实际频率
- 如 Mode A 频率 <1%,可考虑把 happy path 协议从 L0 下移 L1,只保留 Mode B
  防御(借口反驳表)

## Considered Alternatives

- **L0 极简(纯 meta-protocol,0 协议)**:拒绝 — 鸡生蛋问题不解决,
  Mode A silent loss UX 不可接受
- **session 启动强制 invoke project-discuss**:拒绝 —
  · LLM 可能在 invoke 完成前就响应用户首条发言
  · 一旦 invoke,把 ~249 行 L1 内容全部吞进 context,对"轻量闲聊"
    场景是浪费
- **不要 L0,只 inject project-discuss/SKILL.md 全文**:拒绝 —
  project-discuss/SKILL.md 含大量 edge case 内容,每 session 注入浪费 context

## L0 是 L2 精炼摘要的关系契约(v2 加)

L0 inline 的协议内容是 L2 细则的**精炼版**,**不是平行定义**:
- 单一权威源 = L2
- L0 写错时以 L2 为准
- L0/L2 修改时,L2 优先 → L0 同步精炼
- 这不是"重复",这是"summary↔detail"

## When to Revisit

1. 如 dogfood 数据(主动收集或 issue 报告)显示 LLM Gate 1 激活率 > 99%
   → 考虑把 happy path 协议从 L0 下移 L1
2. 如 LLM 实测在 L0 借口反驳 4 项之外发现新的高频 rationalization
   → L0 借口反驳表扩充
```

---

## 7. 验证清单(v2 修订)

### 7.1 静态 grep 检查

```bash
# 应返回 0(除 git history / ADR / 本 blueprint)
git grep '_CONVENTIONS.md' -- ':!架构改造方案-candidate-A.md' \
  ':!架构改造方案-deepseek-review-2026-05-22.md' ':!docs/adr/' ':!CHANGELOG.md'

# 应返回 0
git grep 'scaffold-upgrader'

# 应返回 0(除 harness-adapters 自己提"合并了")
git grep 'codex-tools.md\|opencode-tools.md\|incident-handling.md\|doc-reliability-protocol.md' \
  -- ':!架构改造方案-candidate-A.md' \
  ':!skills/project-discuss/references/harness-adapters.md' \
  ':!CHANGELOG.md' ':!docs/adr/'

# (v2 加) 验证 harness-adapters.md 被引用到位
git grep 'harness-adapters.md'
# 应该至少出现在: bootstrap §7 / project-discuss SKILL §8 路由表
```

### 7.2 行为验证

| 场景 | 期望行为 |
|---|---|
| 新项目跑 `/cadence-init` | 创建 `_INDEX.md` + `_ACTIVE.md` + `discussions/` + `_archive/`;**不创建 `_CONVENTIONS.md`** |
| 已 init 项目重跑 `/cadence-init` | 提示"已初始化,要重做项目快照吗? [r/n]" |
| v0.2.x 旧格式项目跑 `/cadence-init` | inline 迁移:Read _INDEX → 拆分写入 _ACTIVE → 更新词典 pointer |
| SessionStart 注入 | LLM 上下文含 ~110-130 行 bootstrap,**含借口反驳表 4 项**,**不含 _CONVENTIONS.md 引用** |
| LLM 看到"这条不必记"念头 | 立即匹配 L0 借口反驳表 #1/#2/#4/#5 中相应项,记录决策 |
| LLM 写 streaming entry | **对照 L2 信息密度正反例自检**,不写过简的 entry(对抗 Candidate G root cause #1)|

### 7.3 测试套件

```bash
python -m pytest tests/                      # 全部应通过
python -m pytest tests/test_session_start_hook.py -v
python -m pytest tests/schema/
```

---

## 8. 与其他 candidate 的关系

| Candidate | 关系 |
|---|---|
| **B**(统一 subagent 契约) | 独立战场。A 完成后 subagent 数量从 7 → 6,为 B 减负 |
| **C**(删除 DEPRECATED 死代码) | 独立战场。A 之后或并行执行 |
| **D**(validator 字节级复制) | 独立战场。跟 A 无依赖 |
| **E**(bootstrap injection 物化为 build artifact) | A 完成后 L0 内容稳定,E 改造时机更合适 |
| **F**(合并 harness 适配文档) | **被本 blueprint 吸收** — § 4.3.3 已包含 codex + opencode 合并 |
| **G**(streaming entry 信息密度强化)| **本 blueprint § 11 整合** — G piggyback 到 A 的 Phase B,无独立 Phase |

---

## 9. Candidate G 整合(原 v2 标记的"未解决相邻 issue")

v2 blueprint 把 Candidate G(streaming entry 失血问题)标记为下一战场。grilling 14-19 轮完成 G 的完整 design,**整合到本 blueprint § 11**。

**G 与 A 的关系**:

- **铺路部分**(A 改造直接帮到 G):
  - 删 `_CONVENTIONS.md` 消除协议双主问题(LLM 不再读到过时协议)
  - 借口反驳表前移 L0,LLM 写 entry 时始终能看到反驳

- **G 在 A 之上加的事**(详 § 11):
  - L0 信息密度对照例(简短 anchor)
  - L1 Phase 1 质量自检 checklist(6 项)
  - Recommended YAML frontmatter schema(dual schema,旧 markdown 仍合法)

- **诊断纠偏**(grilling 17-19 轮):
  - ✂️ Root cause #3 (handoff 太薄) — 砍掉(handoff = 书签是 v0.3 对的设计哲学)
  - 🔄 Root cause #1 重新框架 — 从 "schema compliance" 改为 "信息密度低"
  - ⏸️ Root cause #2 (`discussions/` 没生成) — 仍开放,标记为 **Candidate G+**,A+G 实施后启动

---

## 11. Candidate G — Streaming entry 信息密度强化

> **起源**: grilling 14-19 轮(含 dogfood evidence 评估 + 4 个 hypothesis 测试 + 17-19 轮关键纠偏)
> **范围**: 纯 protocol fragment patches(markdown),无 Python / 无 subagent / 无 candidate D 依赖
> **实施**: piggyback 到 candidate A 的 Phase B,无独立 Phase,总成本 ~50 行 markdown

### 11.1 G 6 项核心决策

| # | 决策 | 关键洞察 |
|---|---|---|
| G1 | 真问题=信息密度低(不是 schema compliance)| dogfood 案例显示 LLM 写 markdown 段落,但缺 rejected reasons + context |
| G2 | **不接入** `validate_streaming.py` 到 plugin runtime | Python validator 在 LLM-readable file 上是 misfit;LLM 是 polyglot reader,markdown 段落能读 |
| G3 | 引入新 schema(YAML frontmatter)作 **recommended**,旧 markdown 段落仍合法(dual schema)| YAML frontmatter 是 LLM 训练分布常见格式,LLM-friendly + readability 高 |
| G4 | LLM 写 entry 后做**语义自检**(semantic checklist)| 检查"内容充分",不检查"格式合规";append-only 补充,不重写 |
| G5 | L0 直接 inline 简短信息密度对照,L1 详细 checklist | LLM 一眼看到反差,首发言就有 anchor;不依赖主动 Read L2 |
| G6 | 不写 migration tool,旧 streaming 文件保留 | LLM 是 polyglot reader,旧数据对 LLM-based subagent 仍 useful |

### 11.2 受影响文件(纯 markdown)

| 文件 | 增量 |
|---|---|
| `skills/cadence-bootstrap/SKILL.md` L0 | +30 行(entry example + 对照 + 自检 prompt)|
| `skills/project-discuss/SKILL.md` L1 § 2 | +12 行(质量自检 checklist) |
| `skills/project-discuss/references/recording-protocol.md` L2 § 2 | +5 行(dual schema 说明)|

**无 Python 改动 / 无 subagent 改动 / 无 candidate D 依赖。**

### 11.3 具体文字草稿(grilling 19 轮产出)

#### 11.3.1 L0 §5a — Recommended entry format (YAML frontmatter)

放在 cadence-bootstrap/SKILL.md L0 §5 后面:

````markdown
### Recommended entry format (YAML frontmatter + markdown body)

```markdown
---
id: e1
created: 2026-05-21T12:30:00+08:00
status: accepted
chosen: 显式「开始学习」按钮触发
context: 教学模式 UX 设计访谈中讨论"首次进入"入口形态;担心自动触发导致误启动 session
options:
  - 显式按钮触发
  - 自动进入教学
  - 弹窗询问
rejected:
  - 自动进入: 用户路过页面就启动 session,缺乏控制感
  - 弹窗询问: 多一步骤打断流程
---

## E1: 教学入口用「开始学习」按钮触发

用户点击 → 创建 session + AI 发开场白
后续进入:自动恢复 active session,不重发开场白
```
````

> 📌 **非强制** —— Markdown 段落格式也合法,**只要信息密度达到 (chosen + context + options/rejected 三选二) 的 minimum 组合**。

#### 11.3.2 L0 §5b — 信息密度对照例(简短 anchor)

放在 cadence-bootstrap/SKILL.md L0 §5b,LLM 一眼看到反差:

```
❌ 过简(下游 LLM 看不懂为什么 — resume 失血):
   ## E1: 教学入口
   - 用「开始学习」按钮触发
   - 已承接

✅ 充分(含 chosen + context + rejected,下游可独立理解):
   ## E1: 教学入口用「开始学习」按钮触发
   讨论 UX 入口形态(自动 / 弹窗 / 按钮 3 方案)
   chosen: 显式按钮 — 用户点击后创建 session
   rejected: 自动进入(误启动)/ 弹窗(打断流程)

→ 完整正反例见 L2 recording-protocol.md § 2
```

#### 11.3.3 L0 §5 自检 prompt(简版,更新当前 § 4.1 L0 §5)

```
§5 记录动作(happy path)
    · 命中判据 → append streaming entry
    · 推荐 YAML frontmatter + markdown body(见 § 5a);自由 markdown 也合法
    · ★ 写完 entry 立即自检(L0 简版,L1 完整 checklist):
       chosen / context / (options 或 rejected) 三项 minimum 是否齐?
       若任一关键信息缺失 → **append 补充段**(append-only,不重写已有 entry)
    · 告知一行 "📝 已记: ..."
```

#### 11.3.4 L1 § 2 Phase 1 详细 checklist

放在 project-discuss/SKILL.md § 2 Phase 1(替代当前的 Phase 1 摘要):

```
Phase 1 记 —— 触发 / 落点 / 告知 / 铁律 / 质量自检

· 触发: 单判据「已被承接」命中 → append streaming entry
· 落点: cadence/streaming/<YYYY-MM-DD>-<topic>.md
· 铁律: append-only(不修改已有 entry;撤回 = append tombstone)
· 告知: 一行 "📝 已记: <摘要> → <path>"

★ 质量自检 checklist(扩展 L0 §5 简版):

  写完 entry 后,自检以下 6 项,任一关键缺失 → append 补充段:

  ☐ chosen        — 选了什么方案?(必填)
  ☐ context       — 决策的前提/场景是什么?
  ☐ options       — 讨论中有过哪些候选?
  ☐ rejected      — 为什么不选其他?各自被排除原因?
  ☐ dependencies  — 是否依赖其他 entry(引用其 id)?(可选)
  ☐ status        — accepted / pending / superseded?

  minimum 充分组合: chosen + context + (options 或 rejected)
  trap signal: 单写"chosen X 已承接" 必然下游失血,补充 context + rejected
  
  详 L2 recording-protocol.md § 2「信息密度正反例」
```

### 11.4 G 未涵盖:Candidate G+(follow-up)

Root cause #2 (`discussions/` ADR doc 没生成 — consolidator 触发不主动)**仍开放**,但前提依赖 G 实施后再 grill:
- streaming 内容充分 → consolidator 有合法输入 → discussions/ 质量提升
- streaming 仍空 → 即使 consolidator 触发也产不出好 ADR

**Candidate G+ 可能方向**(等 A+G 实施后启动 grilling):
- consolidator 触发条件加 "用户首次承接重大决策" 等更具体 LLM 信号
- 每 K 条 streaming entry 后自动触发 ε 整合(K=5?)
- 用户明确语义信号("OK 那这块就这样")作为话题收尾 trigger

G+ **不在本 blueprint 范围**。

### 11.5 实施:piggyback Phase B(无独立 Phase)

G 改动**完全 piggyback** 到 candidate A 的 Phase B:

| Phase B Step | A 改动 | G 增量 |
|---|---|---|
| Step 6b 重写 bootstrap | L0 § 1-10 按 § 4.1 重写 | **加 § 5a + § 5b + 更新 § 5 自检 prompt**(§ 11.3.1-3)|
| Step 7 重写 project-discuss SKILL | L1 按 § 4.2 重写 | **§ 2 Phase 1 加 6 项自检 checklist**(§ 11.3.4)|
| Step 8 重写 recording-protocol | L2 按 § 4.3.1 重写 | (§ 2 信息密度正反例 v0.3.2 已有,保留即可)|

总成本: ~50 行 markdown 修改,跟 candidate A Phase B 同期完成。

### 11.6 G grilling 历史(Round 14-19)

| Round | 关键拷问 | 结论 |
|---|---|---|
| 14 | G 三个 root cause 优先级? | 用户给 dogfood evidence(教学入口 E1 案例)|
| 15 | streaming entry schema compliance 是 root cause? | dogfood 显示 LLM 完全不按 schema 写 — 升级为 critical |
| 16 | grill-me 干扰 + handoff 太薄是 root cause? | ✂️ 砍 #3 handoff 太薄;grill-me 是 amplifier 不是 root cause |
| 17 | G2 enforcement 形态? | 砍 CC hook(用户嫌重);倾向 G2d 改 schema |
| 18 | 改 schema 向后兼容? | dual schema 实施 cost 远低预期(LLM polyglot);G+D 解耦 |
| **19** | **🔄 关键纠偏**:真问题是 schema 还是信息密度? | dogfood 信号:**信息密度**才是真问题。砍 validator runtime,改 semantic 自检 |

19 轮中**最关键的纠偏发生在 17-19 轮** — 从"严格 schema + validator"转向"recommended schema + 语义自检",更贴合 cadence 的 LLM-centric 哲学。

---

## 10. Sign-off

| 角色 | 姓名 | 日期 |
|---|---|---|
| Design lead | hxt9805 | 2026-05-22 |
| Reviewer | Claude (Opus 4.7) | 2026-05-22 |
| Hostile reviewer | DeepSeek-V4-Pro | 2026-05-22 |
| Implementation owner | TBD | TBD |

变更历史:
- 2026-05-22 v1 初稿(grilling 8 轮后产出)
- 2026-05-22 v2 修订(deepseek hostile review 后,13 项修订)
- 2026-05-22 v2.1 微调(deepseek v2 round review,3 项 minor patches)
- 2026-05-22 v2.2 整合 Candidate G(grilling 14-19 轮产出,§ 11 inline)

---

## Appendix A — Grilling 历史脉络

| 轮次 | 关键拷问 | 结论 |
|---|---|---|
| 1 | _CONVENTIONS.md 主要作用是什么? | dogfood 显示作者自己不读;3 个声明角色全部 paradox → 可删除 |
| 2 | cadence-init 应该做什么? | (b) marker + 状态档骨架,可选 (c) 调研 |
| 3 | "必须 init 才能用"是 feature 还是 friction? | feature(opt-in via init)→ ADR-001 |
| 4 | 旧版本迁移 + 升级检查具体做什么? | 大部分是 _CONVENTIONS 制造的 noise;删 _CONVENTIONS 后整套迁移瘦身 50% |
| 5 | 补全模式留还是删? | 删 — self-healing 不该是 init 的职责;改为"已 init 友好提示" |
| 6 | v0.2.1 迁移做成独立命令? | 不,走 C3 — inline 在 SKILL.md 主流程;subagent 抽象过度工程 |
| 7 | 摘要层 vs 细则层关系? + 调研 superpowers 的分层模式 | 严格 3 层 / 不染色 / 各层职责清晰 |
| 8 | 但 cadence 是常驻 skill,L0 极简会 silent failure? | L0 必须 inline happy path 协议 + 借口反驳表 → ADR-002 |
| **9** | **(v2)** DeepSeek-V4-Pro hostile review | B1/B2/B3 + S1/S2 共 13 项修订(详 changelog)|
| **10** | (v2.1) DeepSeek-V4-Pro v2 round review | Ship now verdict + 3 项 minor patches |
| **14** | (G) Root cause 优先级 + dogfood evidence | 用户教学入口 E1 案例 |
| **15** | (G) streaming schema compliance 是 root cause? | dogfood 显示 LLM 完全不按 schema 写 |
| **16** | (G) grill-me 干扰 + handoff 太薄是 root cause? | ✂️ 砍 #3;grill-me 是 amplifier |
| **17** | (G) G2 enforcement 形态? | 砍 CC hook + 倾向改 schema |
| **18** | (G) schema 向后兼容? | dual schema + LLM polyglot reader |
| **19** | **(G) 🔄 关键纠偏**:schema vs 信息密度? | 真问题是信息密度,不是 schema |

每一轮都有 load-bearing reason 记录在 ADR 或本 blueprint 各节。

---

## Appendix B — 范式精化(v2 新增,acknowledge deepseek 建议)

> ⚠️ **v2.1 disambiguation**: 本附录**不暗示任何实施层面的优先方向**。
> Candidate A 主体设计**不依赖** event sourcing 或 DDD bounded context 这些概念。
> 实施者**不需要**按 event sourcing 改造任何文件 —— 本附录纯粹是「**为后续
> design 工作提供更精确的架构语言**」的可选阅读材料。

deepseek review 建议把 cadence 用更贴合领域语义的架构范式描述。本附录
**不改变 Candidate A 主体设计**,只是为后续 design 工作提供更精确的架构语言。

### B.1 Event Sourcing 视角

cadence 的数据流天然符合 event sourcing pattern:

| Event Sourcing 概念 | cadence 对应 |
|---|---|
| Event log(append-only / immutable / time-ordered)| `streaming/<date>-<slug>.md` entries(append-only / tombstone-only 撤销) |
| Materialized view(状态投影)| `_ACTIVE.md`(当前活跃决策 / 待决 / TODO 等的快照)|
| Event handler(消费 events 更新 projections)| `recall-consolidator` subagent |
| Snapshot(减少 replay 成本)| `cadence/.handoff/<id>.md`(handoff 书签)|
| Read model(优化查询)| `_INDEX.md` 话题词典 + `_INDEX-ROUTING.md` 路由表 |

这个范式能自然解释:
- 为什么 streaming 必须 append-only(event sourcing 的不可变性)
- 为什么 `_ACTIVE.md` 可重建(从 streaming events replay)
- 为什么 handoff 是快照(snapshot pattern)
- 为什么 retriever 是只读(独立 query path,不污染 event log)

### B.2 DDD Bounded Context 视角

cadence 的 3 个 phase(记/整/查)各自是一个 bounded context:

| Phase | Bounded Context | Ubiquitous Language | Invariants |
|---|---|---|---|
| 记 (α) | Recording | 「已被承接」/ entry / streaming / tombstone | append-only / 单判据 / happy path |
| 整 (ε) | Consolidation | trigger_reason / plan / archive / lifecycle | Plan-only / 主 session 唯一写者 |
| 查 (ρ) | Retrieval | summary / pointers / confidence | 只读 / <500 tokens 硬限 |

按 bounded context 分层是**另一个范式选项**(不是替代 L0/L1/L2,而是
在每个 L 内按 phase 组织内容)。当前 Candidate A 仍按 L0/L1/L2 注入深度
分层,但**承认 cadence 的领域结构是 phase-centric** 而非 layer-centric。

### B.3 为何 Candidate A 仍按 L0/L1/L2 分层而非 bounded context

L0/L1/L2 分层服务的是 **"LLM 在 session 中看到什么"** 这个观察者视角:
- L0 = LLM session 启动时看到的
- L1 = LLM 主动 invoke skill 时加载的
- L2 = LLM 自判需要细则时 Read 的

而 bounded context 分层服务的是 **"领域模型如何组织"** 的开发者视角。
两者**不冲突**。Candidate A 的设计可以视为 **L0/L1/L2 注入维度 ×
phase bounded context 维度的二维矩阵**。

### B.4 未来 Candidate(可能)

如果 Candidate G(handoff 失血)需要更深架构调整,可以考虑:
- 显式引入 event sourcing 术语到 SKILL.md / references
- 在 recording-protocol.md / consolidator 文档中用 "event handler" 描述
- 这是**架构语言精化**,不是结构改造

→ Out of scope for Candidate A 主体。

---

**END OF BLUEPRINT v2**
