---
name: cadence-init
description: >
  初始化 cadence 工作流目录结构。支持两种模式：新项目（极简模板 + TBD 占位）
  和已有项目（快速扫描生成快照 + 文档-代码不一致清单）。当用户说"初始化 cadence"、
  "开始用 cadence"、或跑 /cadence-init slash command 时触发。
---

# Cadence Init

初始化 cadence 工作流。双模式：新项目 / 已有项目。

## 主流程

### 第 1 步：检查现有状态

读取项目根目录，检查 `cadence/` 是否存在：

- **不存在** → 继续第 2 步
- **存在** → 检测子状态：
  - `cadence/_INDEX.md` 存在 + `cadence/_ACTIVE.md` 存在 → **新版本（v0.2.2+）**：进入**补全模式**（下方流程）
  - `cadence/_INDEX.md` 存在 + `cadence/_ACTIVE.md` **不存在** → **旧版本（v0.2.1 或更早）**：触发**【第 1a 步：迁移流程】**
  - `cadence/_INDEX.md` 不存在 → 目录异常，提示用户手动修复或删除 `cadence/` 后重跑

#### 补全模式（新版本检测后执行）

对比 `${CLAUDE_PLUGIN_ROOT}/skills/cadence-init/scaffolds/` 下的文件：

- **文件存在性检查**：scaffold 规定的文件/目录是否都在？
- **内容结构检查（best-effort）**：关键文件（`_CONVENTIONS.md`）顶层 section 是否齐全？空壳（全"（暂无）"占位）视为"需要补全"
- 有缺失或空壳 → 展示清单询问用户"发现已有 cadence 目录但 X, Y 缺失或为空壳。要补全还是跳过？"
- 用户同意补全 → 按"**标记外私域不动 / 缺失 section 追加 / 空壳替换**"原则处理（第 4 步的 CLAUDE.md 处理遵循同样原则）
- 无缺失 → 告知"cadence 已完整初始化"，退出

> **注**：补全模式跨文件 diff 和自动 section 追加的细节，旧版迁移已抽到 `scaffold-upgrader` subagent（见第 1a 步）；新版本补全的细节按最小必要原则人工确认。CLAUDE.md 的 2 分支处理见第 4 步。

### 第 1a 步：迁移流程（从旧版升级到 v0.2.2）

当**第 1 步**检测到"`_INDEX.md` 存在 + `_ACTIVE.md` 不存在"时执行：

#### Step 1a.1 提示用户

```
检测到旧版 cadence 目录（v0.2.x 前）。v0.2.2 将 _INDEX.md 拆为
"纯索引 _INDEX.md + 纯活跃 _ACTIVE.md"（会降低 session 加载成本）。

迁移涉及：_INDEX/_ACTIVE 拆分 + _CONVENTIONS.md 升级 + CLAUDE.md fragment 升级。

迁移前建议先 commit 当前状态。要继续迁移吗？[Y / N / 详情]
```

#### Step 1a.2 用户响应分流

- 用户选 **[N]** → abort，不做任何写入
- 用户选 **[详情]** → 展示映射表 + 影响文档清单 + design doc 路径 → 再回到 [Y/N]
- 用户选 **[Y]** → 进入 Step 1a.3

#### Step 1a.3 调用 `scaffold-upgrader` subagent（处理 `_INDEX/_ACTIVE` 迁移）

```
请按 ${CLAUDE_PLUGIN_ROOT}/skills/cadence-init/agents/scaffold-upgrader.md
的规范迁移本项目 cadence 目录。

项目路径：{project_root}
```

subagent 返回**迁移预览**（diff 摘要 + 超限处理选项）→ 主 session 展示给用户 → 用户最终确认 → subagent 执行原子性 Write 两文件。

#### Step 1a.4 `_CONVENTIONS.md` 升级检查（主流程接手）

`scaffold-upgrader` 边界仅含 `_INDEX/_ACTIVE`(subagent 边界严格限定为元文件,便于授权审计)。跨域升级(`_CONVENTIONS.md`)由主流程负责:

1. **比对**：读 `cadence/_CONVENTIONS.md`（用户当前版）+ `${CLAUDE_PLUGIN_ROOT}/skills/cadence-init/scaffolds/_CONVENTIONS.md`（v0.4 现行版）
2. **检测**：完全一致 → 静默跳过；不一致 → 进入下一步
3. **判断旧版特征**（best-effort）：当前文件**缺少**新 scaffold 含的 v0.4 关键节(典型如「记录判据(v0.4 单判据 + 承接对象扩展)」「三阶段通路关系(v0.4)」「征询图景(v0.2.2 → v0.4)」「状态标记(v0.4 状态机)」「并发写缓解(v0.3)」)→ 视为"旧版需升级"
4. **提示用户**：

   ```
   _CONVENTIONS.md 是旧版(缺 v0.4 现行协议的 N 个节,bootstrap 注入引用的节
   会指向不存在内容)。要升级吗?

   - [Y] 用 v0.4 scaffold 覆盖(用户自定义会被覆盖;git diff 可找回)
   - [N] 保留旧版(bootstrap 与 conventions 会有引用不一致;留 TODO 提示稍后手动同步)
   - [详情] 查看完整 diff 摘要(按 section 列出"新增 X / 改动 Y / 缺失 Z")
   ```

5. **用户响应**：
   - **[Y]** → 用 scaffold 内容**覆盖**写入 `cadence/_CONVENTIONS.md`；告知"已覆盖；git diff cadence/_CONVENTIONS.md 可对比"
   - **[N]** → 不写入；告知不一致风险 + 在 `cadence/_ACTIVE.md` TODO 区块追加一行"`[ ] 手动同步 _CONVENTIONS.md 到 v0.4 协议(bootstrap 注入引用的新节缺失)`"
   - **[详情]** → 展示按 section 的 diff 摘要 → 再回到 [Y/N]

#### Step 1a.5 完成迁移 → 继续主流程

迁移结束(`_INDEX/_ACTIVE` 拆分 + `_CONVENTIONS.md` 升级决策完成)→ **进入第 5 步(汇报产物)**。v0.5 起第 4 步 CLAUDE.md fragment 处理已废弃,迁移路径直接跳过。

### 第 2 步：判断项目状态

检查项目根的文件/目录：
- 空或只有 `.git/`、空 README → **新项目模式**
- 有 `src/` / `app/` / `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` / 任何源代码目录 → **已有项目模式**

### 第 3a 步：新项目模式

1. 创建目录骨架：
   ```
   cadence/
   ├── _INDEX.md           ← 从 scaffolds 复制（纯索引版）
   ├── _ACTIVE.md          ← 从 scaffolds 复制（纯活跃版，v0.2.2 新增）
   ├── _CONVENTIONS.md     ← 从 scaffolds 复制
   ├── _archive/
   │   └── .gitkeep
   └── discussions/
       └── .gitkeep
   ```
2. 展示极简模板，允许 `[TBD]` 占位：
   ```
   项目档案（初版）：
   - 项目是什么：???
   - 给谁用：???
   - 已知硬约束（预算、技术栈限制、截止日期等）：???

   告诉我能说的部分，其他留白也 OK。
   ```
3. 用户提供的字段写入 `cadence/_INDEX.md` 的「项目简述」区块。不提供的保持 `[TBD]`。
4. 用户说「随便聊聊」→ 全保持 `[TBD]`，跳过 onboarding。

### 第 3b 步：已有项目模式

1. 询问扫描偏好：
   ```
   检测到这是已有项目。我可以：
     [A] 快速扫描现状，生成一份「项目快照」档案（推荐）
     [B] 先不扫描，等你后面问到时再按需了解
   你选哪个？
   ```
2. 用户选 [A]：
   - 创建目录骨架（同新项目模式的目录结构）
   - 调用 `project-scanner` subagent：
     ```
     请按 ${CLAUDE_PLUGIN_ROOT}/skills/cadence-init/agents/project-scanner.md 的规范扫描本项目。

     项目路径：{project_root}
     输出：
       cadence/discussions/00-project-snapshot.md
       cadence/discussions/01-inconsistencies.md
     ```
   - subagent 完成后，主 skill 读 snapshot 摘要报告展示给用户
   - **消费 `suggested_index_fields` 回填 `_INDEX.md` 项目简述**（见下方第 3b.3 步）

3. **第 3b.3 步：消费 scanner 的 `suggested_index_fields`**（仅用户选 [A] 时执行）

   若 subagent 返回的 `suggested_index_fields` 非空（至少一个字段非 null/空），向用户展示：

   ```
   扫描完成。从 README / manifest 推断出以下项目简述字段，是否填入 _INDEX.md？

   - 项目是：{project_is.value} [来源: {project_is.source}]
   - 给谁用：{target_users.value} [来源: {target_users.source}]
   - 已知硬约束：
     · {hard_constraints[0].value} [来源: {hard_constraints[0].source}]
     · {hard_constraints[1].value} [来源: {hard_constraints[1].source}]
     （无法推断的字段显示 "[无法推断]"）

   [Y] 全部接受并回填    [e<编号>] 编辑某项（如 e1 编辑"项目是"）
   [N] 全部保持 [TBD]
   ```

   **处理用户回复**：
   - `Y` → 将每个非 null 字段写入 `cadence/_INDEX.md` 的「项目简述」区块对应行；null 字段保持 `[TBD]`
   - `e<编号>` → 内联编辑：展示当前 value，让用户改写，改后回到菜单
   - `N` → 不回填，保持全部 `[TBD]`

   **边界情况**：
   - `source` 以 `[推断]` 开头（优先级 3 低可信）→ 展示时额外提示："⚠ 此字段为低可信推断，建议确认"
   - scanner 返回 `suggested_index_fields: null` 或所有字段都是 null → 跳过本步骤，静默保持 `[TBD]`
3. 用户选 [B]：
   - 只创建目录骨架
   - 不调 subagent

### 第 4 步（已废弃,v0.5 起不再修改用户项目 CLAUDE.md）

项目级 cadence 约定由 `hooks/session-start` 脚本读 `skills/cadence-bootstrap/SKILL.md`,
通过 CC SessionStart hook 在 session 启动时运行时注入。**用户项目零侵入** — 不动 CLAUDE.md、
不动 AGENTS.md、不留 fragment 标记。

### 第 5 步：汇报产物 + 下一步建议

```
Cadence 已初始化：
- 创建了 cadence/ 目录（含 _INDEX.md、_CONVENTIONS.md、discussions/）
- 项目快照：cadence/discussions/00-project-snapshot.md（如果扫描）
- 不一致清单：cadence/discussions/01-inconsistencies.md（如果扫描）
- (v0.5 起无需修改 CLAUDE.md;cadence 约定通过 plugin/hook 自动注入)

⚠️ 下一步必须先做：
- **运行 `/clear` 重新加载 cadence 协议** — 本 session 启动时项目还未初始化,
  SessionStart hook 没注入 bootstrap;需要 /clear 让 hook 重新触发,检测到新建
  的 cadence/_INDEX.md 后注入完整协议(否则记 / 整 / 查行为不完整,project-discuss
  仅靠 progressive disclosure 弱激活)。后续新 session 会自动加载,只需要这一次。

之后正常使用：
- 和我说你想讨论的话题，project-discuss 会自动触发
- 用 /cadence-handoff 在 session 变长时整理到档案
- 用 /cadence-resume 继续之前的 session
```

## Scaffold 路径约定

从 `${CLAUDE_PLUGIN_ROOT}/skills/cadence-init/scaffolds/` 复制到用户项目的 `cadence/`。

映射：

- `scaffolds/_INDEX.md` → `cadence/_INDEX.md`
- `scaffolds/_ACTIVE.md` → `cadence/_ACTIVE.md`（新项目或迁移后）
- `scaffolds/_CONVENTIONS.md` → `cadence/_CONVENTIONS.md`

> **v0.5 起**:`scaffolds/CLAUDE-fragment.md` 已删除,内容搬到
> `skills/cadence-bootstrap/SKILL.md` 作为单一来源。cadence-init 不再
> 写用户项目 CLAUDE.md。

## 异常处理

| 情况 | 处理 |
|---|---|
| project-scanner subagent 失败 | 告知用户，建议"改选 [B] 按需了解"或手动填 _INDEX.md |
| 扫描超时（> 1 分钟） | 同上 |
| 用户中途取消 | 保留已创建的目录，告知用户可随时再跑 /cadence-init 补全 |
| 用户手动删除某些 scaffold 文件 | 下次跑 /cadence-init 时检测缺失自动补 |
