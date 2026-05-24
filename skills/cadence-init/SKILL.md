---
name: cadence-init
description: >
  初始化 cadence 工作流目录结构。支持两种模式：新项目（极简模板 + TBD 占位）
  和已有项目（快速扫描生成快照 + 文档-代码不一致清单）。当用户说"初始化 cadence"、
  "开始用 cadence"、或跑 /cadence-init slash command 时触发。
---

# Cadence Init

初始化 cadence 工作流。双模式：新项目 / 已有项目。

## 1. 检查现有状态

读取项目根，检查 `cadence/`：

- **`_INDEX.md` + `_ACTIVE.md` 都在**（已初始化 v0.2.2+）→ 询问 `要重做项目快照吗？[r/n]`。`r` 跳到 § 3.3 已有项目模式 [A]；`n` 退出（无需 /clear，bootstrap 在本 session 启动时已注入）。
- **`_INDEX.md` 在 + `_ACTIVE.md` 不在**（v0.2.x 旧格式）→ § 2 迁移
- **都不在** → § 3 init
- **其他异常**（如 `_INDEX.md` 不在但 `_ACTIVE.md` 在）→ 提示用户手动修复或删 `cadence/` 后重跑

## 2. v0.2.x 旧版本迁移（inline）

主 session 直接处理（不再调 subagent）。

```
检测到旧版 cadence 目录（v0.2.x 前）。v0.2.2 将 _INDEX.md 拆为
"纯索引 _INDEX.md + 纯活跃 _ACTIVE.md"。迁移前建议先 commit。继续？[Y/N]
```

`N` → abort。`Y` → 执行：

1. 读 `cadence/_INDEX.md`。
2. 按映射拆 section：
   - 「当前活跃决策」/「待决清单」/「TODO」/「最近讨论」→ `_ACTIVE.md`
   - 「项目简述」/「话题词典」/「快速导航」→ 留 `_INDEX.md`
   - 未识别 section → 留 `_INDEX.md` 末尾（加 `<!-- cadence 未识别 -->` 注释）
3. `_ACTIVE.md` 若超 8 条活跃决策上限，inline 三档：
   ```
   ⚠️ 检测到 N 条活跃决策，新上限 8 条。
   (a) Claude 推荐归档清单（按日期倒序最老 N-8 条）
   (b) 我自己选要归档哪些
   (c) 保留全部（暂时超限，下次记决策时会提示整理）
   ```
4. 更新话题词典 pointer：`→ 活跃决策` 改为 `→ _ACTIVE.md#活跃决策` 或 `@active`。
5. 展示 diff 摘要 → 用户确认 → `Edit _INDEX.md` + `Write _ACTIVE.md`（IO 失败回滚，不留半迁移状态）。
6. 完成告知：`📝 已迁移：_INDEX.md（NN→MM 行 / 纯索引）+ _ACTIVE.md（新建 KK 行）。详见 git diff cadence/`

→ § 4 汇报产物（无需 /clear，bootstrap 在本 session 启动时已注入）。

## 3. init 主流程

### 3.1 判断项目状态

- 空或只有 `.git/` / 空 README → **新项目模式**（§ 3.2）
- 有源代码目录（`src/` / `app/` / `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` 等）→ **已有项目模式**（§ 3.3）

### 3.2 新项目模式

创建目录骨架：

```
cadence/
├── _INDEX.md       ← scaffolds/_INDEX.md
├── _ACTIVE.md      ← scaffolds/_ACTIVE.md
├── _archive/.gitkeep
└── discussions/.gitkeep
```

极简 onboarding（允许 `[TBD]`）：

```
项目档案（初版）：
- 项目是什么：???
- 给谁用：???
- 已知硬约束：???
告诉我能说的部分，其他留白也 OK。
```

用户提供的字段写入 `_INDEX.md` 的「项目简述」；不提供的保持 `[TBD]`。用户说「随便聊聊」→ 跳过 onboarding。

### 3.3 已有项目模式

```
[A] 快速扫描生成「项目快照」（推荐）
[B] 先不扫描，按需了解
```

- **[A]**：创建目录骨架（同 § 3.2）→ 调 `project-scanner` subagent：
  ```
  请按 ${CLAUDE_PLUGIN_ROOT}/skills/cadence-init/agents/project-scanner.md 的规范扫描本项目。
  项目路径：{project_root}
  输出：cadence/discussions/00-project-snapshot.md + 01-inconsistencies.md
  ```
  完成后展示 scanner 的 `suggested_index_fields`（每字段标 `[来源: X]`，`[推断]` 优先级低需额外确认）。让用户选 `[Y]` 全部回填 / `e<编号>` 编辑某项 / `[N]` 全保持 [TBD]。
- **[B]**：只创建目录骨架，不调 subagent。

## 4. 汇报产物 + 下一步

```
Cadence 已初始化：
- cadence/（_INDEX.md / _ACTIVE.md / discussions/ / _archive/）
- 项目快照：cadence/discussions/00-project-snapshot.md（如果扫描）
- 不一致清单：cadence/discussions/01-inconsistencies.md（如果扫描）
```

⚠️ **若本 session 是首次 init**（之前没有 cadence/_INDEX.md）：

必须先跑 `/clear` 重新加载 cadence 协议 — 本 session 启动时项目还未初始化，SessionStart hook 没注入 bootstrap；新建 cadence/_INDEX.md 后需 /clear 让 hook 重新触发，否则记 / 整 / 查行为不完整（project-discuss 仅靠 progressive disclosure 弱激活）。后续新 session 自动加载，只需这一次。

之后正常使用：

- 和我说想讨论的话题（project-discuss 自动触发）
- `/cadence-handoff` 整理到档案；`/cadence-resume` 续接之前 session

## 异常处理

| 情况 | 处理 |
|---|---|
| project-scanner 失败或超时（> 1 分钟）| 告知用户，建议改选 [B] 或手动填 _INDEX.md |
| 用户中途取消 | 保留已创建目录，告知可随时再跑 /cadence-init |
| § 2 迁移 IO 失败 | 回滚未提交改动；告知用户 git 状态 |

> Scaffold 路径：`${CLAUDE_PLUGIN_ROOT}/skills/cadence-init/scaffolds/_INDEX.md` / `_ACTIVE.md`。
> v0.5 起 cadence 协议由 plugin SessionStart hook 自动注入，不再写 `_CONVENTIONS.md` 或 CLAUDE.md fragment。
