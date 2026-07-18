---
name: cadence-resume
description: "继续之前某次 session 的讨论上下文(v0.4:Step 6 archive cleanup B1 修复 + content_hashes 判据 + 派 retriever 替代 auditor)。用户说 '继续上次'/'resume' 或跑 /cadence-resume 时触发。"
---

# cadence-resume(v0.4)

## 定位

用户跑 `/cadence-resume` 或说"继续上次" → 展示可 resume 的 handoff 列表 → 用户选择 → 加载对应 handoff 上下文 + 对比当前档案状态 → 报告"你上次讨论到哪、和现在有何差异"。

## 路径约定

所有 handoff 产物必须位于 `<project-root>/cadence/.handoff/`。不得在项目根创建或读取裸 `.handoff/`;Step 1 前置检测发现时只提示迁移,不阻断主流程。

## 流程

### Step 1:列出可 resume 的 handoff

#### 前置检测(路径漂移护栏)

读取 index 之前,先检测项目根是否存在裸 `.handoff/`(历史版本不一致 bug 痕迹):

- 若 `<project-root>/.handoff/` 存在 **且** `<project-root>/cadence/.handoff/` 不存在 → 一行提示:
  `⚠️ 检测到 .handoff/ 在项目根,这是 v0.2.0 历史路径不一致 bug 的痕迹。建议:mv .handoff cadence/.handoff 后重试。`
  本次仍按规范从 `cadence/.handoff/` 读取(为空则展示"无 handoff")。
- 若两者都存在 → 警告 `⚠️ 同时存在项目根 .handoff/ 和 cadence/.handoff/,请手动合并(以 cadence/.handoff/ 为准)。`
- 否则静默通过。

检测失败(IO 异常等)→ 不抛、不阻断主流程(参 § Step 6 失败优雅降级风格),继续 Step 1 主体。

#### 主体

读 `cadence/.handoff/index.json`,按 `created_at` 倒序展示最近 N 条(默认 N=5):

```
最近 handoff:
  1. 2026-04-23 18:00  v0.3 Phase D handoff 联动重构
  2. 2026-04-20 12:00  阶段 B 深度审查(legacy v0.2.2)
  ...
要继续哪条?(输入编号 / "new" 开新 session)
```

### Step 2:用户选择后读取 handoff 快照

`Read cadence/.handoff/<handoff_id>.md`,解析 frontmatter。

### Step 3:识别版本(v0.4 / v0.3 / legacy v0.2.2)

```python
# 伪代码(Claude 按逻辑执行,不跑真 python)
is_legacy = (
    "content_hashes" not in frontmatter
    and "item_counts" in frontmatter
)
```

- 有 `content_hashes + continuation_refs + fidelity` → v0.4,走 Step 4a
- 仅有 `content_hashes` → v0.3,走 Step 4a 的兼容路径
- legacy v0.2.2 → 走 Step 4b

**判据优先级**:字段判据为主(覆盖 99% 场景);若字段判据**两字段都不存在或都存在**(corner case,如文件损坏或迁移中)→ 调用 `python ${CLAUDE_PLUGIN_ROOT}/skills/cadence-handoff/scripts/validate_handoff.py <path>`(macOS / Linux 把 `python` 换成 `python3`)兜底:v0.3 合法则走 4a;抛 "legacy v0.2.2 detected" 则走 4b;其他错误 → 告知用户"handoff 文件格式无法识别"。

### Step 4a:v0.3/v0.4 — hashes 对比 + canonical 恢复

1. 用 cadence-handoff Step 3 同方法(`git hash-object` 首选,平台 fallback 见 `skills/cadence-handoff/SKILL.md` Step 3)计算**当前** `cadence/_INDEX.md` + `_ACTIVE.md` 的 sha1
2. v0.4:逐个验证 `continuation_refs.path` 存在,计算当前 sha1 并与快照对比
3. 读取所有校验通过的 continuation discussion,不得只展示路径而不读正文
4. 仅依赖 handoff + 已读 cadence 档案回答冷启动六问:
   - 已决定什么?
   - 为什么?
   - 否决过什么?
   - 哪些约束不能破坏?
   - 哪些问题仍未决定?
   - 下一步是什么?
5. 对比所有 hashes:

   **索引 + canonical 均 match** → 档案未变,走简洁视图:
   ```
   📍 上次讨论到:<cursor.last_discussed>
   📋 待定:<cursor.pending_questions>
   ➡️ 下一步:<cursor.next_step>
   📚 已恢复:<continuation_refs paths>
   注:档案自 handoff 以来无变化,且 canonical 上下文已读取,可直接接续。
   ```

   **至少一侧 mismatch / ref 缺失** → 档案已变或不完整,走 Step 5(派 retriever)

6. `fidelity.status: partial` 时,在简洁视图中逐条展示 `uncovered`;禁止把推断补成既定事实。
   v0.3 没有 fidelity 字段时标注"legacy-unverified",不声称做过本次保真扫描。

### Step 4b:legacy v0.2.2 — mtime fallback

v0.2.2 老 handoff 无 content_hashes。回退 mtime 判据:

1. Compare mtime of `cadence/.handoff/<file>.md` vs current mtime of `cadence/_INDEX.md` and `cadence/_ACTIVE.md`
2. handoff 晚于档案 → 可直接展示 body「关键事项」段
3. handoff 早于档案(档案已更新)→ 提示"上次 handoff 后档案有更新,建议用 retriever 查历史" → 走 Step 5

### Step 5:派 retriever 检索差异点

使用 Phase C 引入的 `recall-retriever`:

- 输入:
  - `user_query`:基于 handoff 的 `cursor.last_discussed` + `pending_questions` 拼接
  - `current_session_context`:轻量,说明"新 session 刚启动,需了解 handoff 后档案新变化"
- 接收 <500 tokens 输出(summary + pointers + confidence)
- v0.4 continuation ref mismatch 时,把 mismatch path 作为检索锚点并优先读取替代 canonical
- 展示:
  ```
  📍 上次讨论到:<cursor.last_discussed>
  📋 待定:<cursor.pending_questions>
  ➡️ 下一步:<cursor.next_step>

  🔎 档案自 handoff 以来有变化,检索到相关更新:
  <retriever.summary>

  相关文件:
  - <pointers[0].path>:<pointers[0].relevance>
  ...
  ```
- 主 agent 自动 `Read` 与冷启动六问直接相关的 pointer;弱相关 pointer 只展示路径

### Step 6: Archive cleanup（v0.4 新增 / B1 修复）

resume 成功后（已读取必要 canonical 或已精确报告 partial 缺口,并向用户展示恢复结果），
**立即执行** archive cleanup，防止 resumed 条目永远停留在
`cadence/.handoff/index.json`（B1 bug）。若 ref/hash 校验失败且 retriever 也失败,本次
不算成功恢复,不得 cleanup,以便修复后重试。

#### 调用方式

> 命令名按平台:Windows = `python`,macOS / Linux = `python3`(下例以 Windows 风格写)

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/cadence-resume/handoff_cleanup_helper.py <project_root>/cadence/.handoff/ <handoff_id>
```

示例（handoff_id = `h_20260423_180000`）：

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/cadence-resume/handoff_cleanup_helper.py cadence/.handoff/ h_20260423_180000
```

helper 打印每步结果，`exit 0`（即使部分 skip / fail）。

#### 子步说明

| 子步 | 动作 | 幂等条件（skip） |
|------|------|-----------------|
| **6a** | 从 `cadence/.handoff/index.json` 移除该 `handoff_id` 条目 | 条目已不在 pending index |
| **6b** | 移动 `cadence/.handoff/<id>.md` → `cadence/.handoff/archived/<id>.md`（自动创建 `archived/` 目录） | 目标文件已在 `archived/`，或源文件已不存在 |
| **6c** | 追加条目（含 `resumed_at` 时间戳）到 `cadence/.handoff/archived/index.json` | `archived/index.json` 中已有该 `handoff_id` |

#### 幂等性

每个子步独立判断是否已执行：已执行则返回 `skip`，不报错，不重复执行。重复 resume 同一 handoff 时三步全 skip，安全。

#### 失败优雅降级（§ 6d）

- helper 每步失败记录 `fail:<reason>` 到返回 dict，**不抛异常**，**不中断主流程**
- 主 session 若收到任意 `fail:*` → 告知用户"Step 6 部分步骤异常：`<step>: <reason>`，handoff 档案状态可能需要手动检查"
- **绝不因 archive cleanup 失败而阻断 resume 主流程**（用户已获得 resume 上下文，这才是核心价值）

#### 用户感知格式（合并到 resume 通知末尾）

```
✅ Step 6 archive cleanup: 已将 <handoff_id> 移至 archived/（6a/6b/6c 均成功）
```

若部分 skip（如幂等重复 resume）：

```
⏭️ Step 6 archive cleanup: <handoff_id> 已在 archived/（skip）
```

若有失败：

```
⚠️ Step 6 archive cleanup 部分异常（<step>: <reason>），请手动检查 cadence/.handoff/ 目录
```

#### 测试覆盖

`tests/schema/test_handoff_cleanup.py` 包含 4 个强制契约测试（§ 5.3）：

- `test_resume_step6_normal_cleanup` — 正常 resume，6a/b/c 全 success
- `test_resume_step6_idempotent` — 重复 resume，第二次全 skip，archived 无重复条目
- `test_resume_step6_creates_archived_dir` — archived/ 目录不存在时自动创建
- `test_resume_step6_pending_index_externally_emptied` — pending index 已清空时 6a skip，6b/c 仍执行

## 失败模式

**核心红线**:**绝不基于 handoff 内容瞎编档案现状**(design doc § 2.1)。所有失败分支必须走"告知用户 + 降级展示",**不伪造数据**。

其他具体失败情形:
- Step 2 handoff 文件缺失 → 告知用户"handoff 文件已丢失 / 被手动删除",展示 index.json 中其他候选
- Step 4a sha1 计算失败 → 回退走 Step 4b mtime 判据 + 告知用户"sha1 不可用,使用 mtime 粗判"
- Step 5 retriever 失败 → 告知用户 + 降级为"展示 handoff body,由用户自行决定是否深入"
- continuation ref 缺失或 hash mismatch → 不使用旧正文冒充当前真相;走 retriever 查替代文档
- 冷启动六问无法回答 → 显示具体缺项,标记恢复为 partial,不重新拍板

## `handoff-resume-auditor` 废弃

v0.2.2 的 `agents/handoff-resume-auditor.md`(对比 `_INDEX`/`_ACTIVE` 差异)职责在 v0.3 由
`content_hashes + retriever` 取代,**已废弃**。文件保留(加 DEPRECATED 标注)防外部引用。

## 版本兼容

- v0.4 handoff:content_hashes + continuation_refs + fidelity(4a → 5)
- v0.3 handoff:content_hashes 兼容分支(4a → 5,标 legacy-unverified)
- v0.2.2 legacy:mtime fallback(4b)
- 不强制迁移老 handoff 文件
