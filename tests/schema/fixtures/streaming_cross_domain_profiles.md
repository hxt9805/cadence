---
started: 2026-07-18T10:00:00+08:00
status: active
---

---
id: ^entry-20260718-10
created: 2026-07-18T10:10:00+08:00
status: accepted
detail_profile: standard
context: 长文已有素材，但章节顺序会影响读者理解论证。
chosen: 先解释问题背景，再呈现案例，最后总结方法；具体章节标题仍待定。
rationale: 先建立共同语境，再让案例承担证据作用。
semantic_slots:
  sequence_and_dependencies:
    - 背景先于案例
  open_questions:
    - 各章节的最终标题
---

## 写作章节结构

---
id: ^entry-20260718-11
created: 2026-07-18T10:20:00+08:00
status: accepted
detail_profile: high
context: 学习计划持续半年，中断后若直接补齐全部欠账会导致计划崩溃。
chosen: 连续中断超过两周时不追补全部旧任务；从当前阶段的最小复习单元重新进入。
rationale: 保留长期节奏比短期清零欠账更重要。
semantic_slots:
  sequence_and_dependencies:
    - 先完成最小复习单元，再恢复正常进度
  failure_and_recovery:
    - 中断超过两周时触发重新进入流程
not_applicable:
  - external_commitments
---

## 学习中断恢复

---
id: ^entry-20260718-12
created: 2026-07-18T10:30:00+08:00
status: accepted
detail_profile: high
context: 活动涉及外部供应商和公开宣传，超预算或关键审批缺失会造成资金与信誉损失。
chosen: 总预算不得超过 50000 元；任何新增支出必须由活动负责人批准；审批缺失时暂停活动。
rationale: 在外部承诺产生前建立清晰的资源边界和中止条件。
semantic_slots:
  resources_and_limits:
    - 总预算上限 50000 元
  actors_and_responsibilities:
    - 活动负责人批准新增支出
  failure_and_recovery:
    - 审批缺失时暂停活动
---

## 运营预算与中止

---
id: ^entry-20260718-13
created: 2026-07-18T10:40:00+08:00
status: accepted
detail_profile: light
context: 页面按钮需要避免给用户造成已经提交的误解。
chosen: 按钮文案从“完成”改为“保存草稿”，仅用于当前草稿页。
---

## 局部文案调整
