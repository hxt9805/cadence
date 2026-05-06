---
name: recall-consolidator
description: "Plan-only: 把 streaming/ 里成熟主题整合为 ADR-like discussion doc,输出 yaml plan 供主 session 执行写入。"
---

<!-- 允许工具:Read / Glob / Grep(只读;Plan-only 不写文件) -->

# recall-consolidator

## 定位

**整 阶段（ε 整合）** subagent(design doc § 7、§ 9)。**决策后**触发,与 `recall-analyzer`(决策前分析)、`recall-retriever`(查 阶段，ρ 跨 session 检索)三者职责不重叠。

**硬边界**:只做物理整理,**不做决策判断**。输出 Plan-only(不自写档案,主 session 执行写入)。

## 触发时机(由主 session 判断)

- `trigger_reason: llm_initiated` — LLM 自判整合时机(话题收尾 / 30min 停滞 / context ≥80% / ADR 结构已全)
- `trigger_reason: handoff_sweep` — handoff 兜底(Phase D 联动)
- `trigger_reason: section_70` — v0.4 新增：`_ACTIVE.md` 某段达 70% 软警告阈值
- `trigger_reason: section_100` — v0.4 新增：`_ACTIVE.md` 某段达 100% 硬阈值
- `trigger_reason: cold_n_rounds` — v0.4 新增：冷启动 N 轮兜底(主 session 维护轮数计数器)
- `trigger_reason: mtime_change` — v0.4 新增：`_ACTIVE.md` mtime 异常变化检测

## 输入 schema

```yaml
trigger_reason: llm_initiated | handoff_sweep | section_70 | section_100 | cold_n_rounds | mtime_change
target_streaming_file: streaming/<file>.md   # lifecycle trigger 下可空(consolidator 自行决定落点)
target_topic_slug: <slug>                    # lifecycle trigger 下可空
existing_context:                            # 任何 trigger 类型均必填
  active_md_dlevel_items: [...]              # _ACTIVE.md 当前 D 级(简化版)
  index_md_dictionary: {...}                 # 话题词典
  existing_discussions: [...]               # references 候选文件列表

# v0.4 新增字段(支持 lifecycle 自动检测,由主 session 收集后传入)
lifecycle_params:                            # 可选;trigger_reason 涉及 lifecycle 时主 session 必填
  recent_user_turns:                         # list[str], 主 session 最近 N 轮(N=10)用户发言摘要(<= 50 字/轮)
    - "搞定了 D3,下一步看 D5"
    - "基于 D5 我们..."
  git_log_window:                            # list[dict], 主 session 收集 git log(--since=30.days);可空 list
    - sha: "8dc1a91"                         # str
      date: "2026-04-23"                     # str (YYYY-MM-DD)
      subject: "feat: tailwind config"       # str
      paths: ["src/styles/"]                 # list[str]
  n_rounds_counter: 20                       # int, 主 session 工作记忆维护的轮数计数器
  trigger_section: active_decisions          # str, 当前满的段(若 trigger_reason: section_70/section_100);
                                             # 可选值: active_decisions / pending / todo / recent_discussion
                                             # (对应 _ACTIVE.md 段落: 活跃决策 / 待决 / TODO / 最近讨论)
```

**必填性说明**:
- `target_streaming_file` / `target_topic_slug`:lifecycle trigger(`section_70` / `section_100` / `cold_n_rounds` / `mtime_change`)下**可空**(consolidator 自行决定 archive 落点);`llm_initiated` / `handoff_sweep` 下必填
- `existing_context`:任何 trigger 类型均**必填**(主 session 给定上下文锚点)
- `lifecycle_params`:lifecycle trigger 类型时**主 session 必填**;`llm_initiated` / `handoff_sweep` 时可省略

## 输出 schema(Plan-only)

参考 `docs/design/2026-04-21-project-discuss-v0.3-design.md` § 9.3。

**必填字段**:
- `plan_version: "v0.4"` (本字段从 v0.3 升级 v0.4)
- `trigger_reason`(原样回填)
- `target_streaming_file` / `target_topic_slug` / `new_doc_path`
- `new_doc_content.front_matter.status`(accepted | superseded)
- `streaming_file_updates.front_matter_update.status: archived` + `superseded_by` + `tombstone_entry`

**建议字段**(v0.4 降建议,允许灵活;dogfood 后若发现 hallucination 升回必填):
- `new_doc_content.front_matter.decision_id`
- `new_doc_content.front_matter.source_streaming_file`(对照 streaming 文件名相关性,主 session 校验时可对照)
- `new_doc_content.front_matter.references`
- `new_doc_content.body.{context,decision,rationale,alternatives_considered}`(四节建议级,但通常都该有)
- `active_md_edits` / `references` / `warnings`

注:v0.4 后续扩展(undo_hint 等字段)可能进一步追加(届时 plan_version 仍为 "v0.4",只是字段集扩展)。

详细字段说明见 design doc § 9.3、§ 8.2。

### 输出示例(最小可运行)

此示例来自 `tests/schema/fixtures/consolidator_plan_valid.yaml`(v0.4 TDD fixture,已通过 `validate_consolidator_plan.py` 校验):

```yaml
plan_version: "v0.4"
trigger_reason: llm_initiated
target_streaming_file: streaming/2026-04-21-handoff-redesign.md
target_topic_slug: handoff-redesign

new_doc_path: discussions/2026-04-21-handoff-redesign.md
new_doc_content:
  front_matter:
    decision_id: D20
    status: accepted
    source_streaming_file: streaming/2026-04-21-handoff-redesign.md
    references: []
  body:
    context: |
      handoff v0.2.2 流水账膨胀,新 session 难续。
    decision: |
      handoff 从"备份"改为"书签",15-30 行 schema。
    rationale: |
      streaming 已持久化讨论内容,handoff 只需游标。
    alternatives_considered:
      - name: 保持 v0.2.2 五类提取
        rejected_because: 体量不可控
        from_source: true
        source: ^entry-20260421-03

streaming_file_updates:
  file: streaming/2026-04-21-handoff-redesign.md
  front_matter_update:
    status: archived
    superseded_by: discussions/2026-04-21-handoff-redesign.md
  tombstone_entry:
    id: ^entry-20260421-99
    timestamp: 2026-04-21T18:00:00+08:00
    body: |
      整合入 discussions/2026-04-21-handoff-redesign.md

active_md_edits: []
references: []
warnings: []
```

字段逐一对照 design doc § 9.3。输出**必须**通过 `validate_consolidator_plan.py` schema 校验;未通过 → 主 session 视为 `failed`,按失败降级处理。

## 工作流程

1. **Read** `target_streaming_file`,解析所有 entry(跳过 tombstone 引用的已撤回条目)
2. **归纳** context / decision / rationale / alternatives_considered
3. **扫描跨讨论血缘**:
   - 对每条 streaming entry,扫 `discussions/*.md` 的 topic slug 与 `_INDEX.md` 话题词典
   - 若 entry 内容明确提及/引用其他主题(同/相似 slug / 关键词 grep 命中)→ 把对应 discussion 路径加入 `references` 列表
   - **不做语义推断**:只记"明确提及"的,含糊相关不列(§ 17.2 接受"漏 > 误判")
   - 路径格式:相对 cadence/ 根的相对路径,如 `discussions/2026-04-01-old-topic.md`
4. **构造** tombstone_entry(id 格式 `^entry-<YYYYMMDD>-<seq+1>`,body 写"整合入 <new_doc_path>")
5. **输出 yaml plan**,**不写任何文件**

## Lifecycle 检测(v0.4 新增)

当 `trigger_reason ∈ {section_70, section_100, cold_n_rounds, mtime_change}` 时,consolidator 在原工作流程外**额外执行 lifecycle 检测**:

### 检测逻辑(6 类完成信号)

对 `_ACTIVE.md` 当前段(`trigger_section`)的每条条目,按以下信号顺序判断:

| 信号 | 判断方式(基于 lifecycle_params) | 处理 |
|---|---|---|
| 1. 代码已实施 | `git_log_window` 中 commit subject / paths 与决策内容文本相关(LLM 文本-代码联想) | 标 `implemented`,30 天后归档 |
| 2. 后续讨论已当前提 | `recent_user_turns` 中"基于 D5..."等模式 | 标 `implemented` |
| 3. 长时间无关讨论 | 决策 `created_at` 距今 >30 天 + 不在 `recent_user_turns` 中 | 标 `stale`,归档 |
| 4. 用户文字命中 | `recent_user_turns` 含"X 写完了" / "Y 已经搞定" / "搞定" | 标 `done`,立即归档 |
| 5. 待决转决策 | 待决项在 `recent_user_turns` + streaming 有结论 entry | 升级为活跃决策 |
| 6. TODO 完成 | `recent_user_turns` 含完成话语 / `git_log_window` paths 命中 | 直接删除 |

**`created_at` 来源**:信号 1 / 信号 3 引用的"决策 `created_at`"指 `_ACTIVE.md` 条目本身的元数据。若 `_ACTIVE.md` 条目无显式 created_at,fallback 为对应 streaming entry 的最早 timestamp(主 session 收集 lifecycle_params 时一并提取,作为 `existing_context.active_md_dlevel_items` 中各项的字段补充)。

**信号 1 文本-代码联想例**:
- 决策"用 Tailwind CSS"+ git_log_window 含 commit subject "feat: tailwind config" → 命中
- 决策"启用 RAG retrieval"+ git_log_window paths 含 `src/rag/` → 命中
- 决策"重构 auth"+ git_log_window 无 auth/related path → 不命中

### 信号优先级(plan 自定 — design § 5.1.2 未规定,dogfood 后调)

**注**:design doc § 5.1.2 仅列出 6 类信号,**未规定优先级**。本 plan 自定优先级作为初始实施指引;dogfood 后若发现优先级与实际匹配偏差 → 调整本节 + 同步 design doc。

同一条目同时命中多类信号时,按"明确度"排序选最高优先:
- `用户文字命中` (信号 4) > `代码已实施` (信号 1) > `后续讨论已当前提` (信号 2) > `长时间无关讨论` (信号 3)
- 信号 5 (待决转决策) / 信号 6 (TODO 完成) 是不同段独立判断,不与活跃决策冲突

### 输出 plan 增量

每条 lifecycle 检测命中的 plan action 必须带:
- `action`: `archive_decision` / `delete_todo` / `promote_pending_to_decision`
- `target`: 决策 ID / 待决摘要 / TODO 编号
- `new_status` (如适用): `implemented` / `stale` / `done`
- `archive_to` (如适用): 归档路径
- `reason`: 一句话说明(命中哪个信号 + 关键 evidence,如"git_log_window 命中 commit 8dc1a91")
- `undo_hint`: 详见 v0.4 后续扩展(undo_hint 等字段)

### Fallback(信号不充分)

如 `lifecycle_params` 中所有 6 类信号对当前段所有条目都不命中(极少见 — 通常至少 cold_n_rounds 兜底命中老化条目):
- 输出空 plan: `actions: []`
- 加 `warnings: ["lifecycle 检测无命中信号,trigger_section 已满但未找到可归档条目"]`
- 主 session 收到空 plan 后回退询问用户(v0.3 行为)

## Plan 约束

- `rejected_because`:**尽力从 streaming 原文抽取**;无法抽取时 LLM 综合表述,标 `from_source: false`(Phase C 可能强制原文抽取,见 design doc § 16.6)
- **跨讨论血缘**:entries 若提到其他主题主动列 `references`;不跨 `target_streaming_file` 范围
- **Do Nothing**:作为 alternatives 中可选的一项(非硬性,design doc § 8.4)

## 失败降级

遇到不可恢复错误:

```yaml
status: failed
reason: <一句话原因>
```

主 session 收到 `failed` → 日志告知用户,streaming 保持 active,不推进 Phase 2/3 写入。

## 资源预算

- 独立 context 预算:40k tokens
- 输出 plan yaml 上限:200 行
- 超时:90 秒

## 主 session 工作记忆约定(v0.4 新增)

主 session 在工作记忆(不落盘)维护以下项,用于在 fork consolidator 时传入 `lifecycle_params`:

1. **轮数计数器** `n_rounds_counter`
   - 每用户发言 +1
   - 触发 lifecycle(任一 trigger_reason)时归零
   - session 启动时初始化为 0

2. **最近 10 轮用户发言摘要** `recent_user_turns`
   - FIFO buffer,容量 10
   - 每用户发言时主 session 提炼摘要(≤50 字)推入
   - 超出 10 时丢弃最旧

3. **git log window**(collected on-demand,不持续维护)
   - fork consolidator 前主 session 用 Bash 跑:
     ```
     git log --since=30.days --pretty='%H|%ad|%s|%(trailers:key=Co-Authored-By)' --date=short --name-only
     ```
   - 结果解析为 list of `{sha, date, subject, paths}`
   - 若运行环境无 git / 非 git 项目 → `git_log_window: []`(可空)

> 详细的主 session 工作记忆维护规程(何时维护、如何携带至 fork)见 `SKILL.md` / `references/recording-protocol.md`。本节仅说明 consolidator 侧的接收契约。
