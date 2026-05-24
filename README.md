# cadence

讨论驱动的软件开发工作流插件 — 通过 **记 / 整 / 查** 三阶段记录协议，把 Claude Code / Codex session 的讨论、决策、TODO 自动落地到项目档案中，支持长 session handoff 与跨 session resume。

> **Claude Code 与 OpenCode 都是 first-class 形态**（两边都通过原生机制支持自动 bootstrap 注入、Task tool fork named subagent、context 隔离）。Codex CLI / App / IDE 通过兼容层支持——SessionStart hook、Task tool、`${CLAUDE_PLUGIN_ROOT}` 在 Codex 没有原生等价,部分体验依赖 LLM 自适应;详见下文 [平台与兼容性](#平台与兼容性)。

## 这是什么

cadence 解决一个具体问题：**LLM session 的讨论与决策容易被 `/compact` 或 session 切换冲掉**。它通过一组 skill + hook 让 LLM 自动：

- **记**：在你与 Claude 讨论时，把"已被承接"的决策、TODO、待决问题流式追加到 `cadence/streaming/`
- **整**：阶段性地把 streaming 条目整合为 ADR-like 的讨论文档（`recall-consolidator` subagent）
- **查**：跨 session 检索历史决策与讨论（`recall-retriever` subagent，<500 tokens 硬限）

记录、查询、决策路由由常驻的 `project-discuss` skill 统筹；多档案 / 5+ 轮 / 冲突风险时另派 `recall-analyzer` subagent 做"决策前回忆分析"（产三分类事实供用户确认）。

session 之间通过 `/cadence-handoff` 写"书签式"快照，下次用 `/cadence-resume` 继续。

## 安装

### Claude Code

```
/plugin marketplace add https://github.com/hxt9805/cadence.git
/plugin install cadence@cadence
```

### OpenCode

在 `opencode.json`（global 或 project-level）的 `plugin` 数组里加入 cadence：

```json
{
  "plugin": ["cadence@git+https://github.com/hxt9805/cadence.git"]
}
```

重启 OpenCode。plugin manager 会自动 clone 仓库、注册 5 个 skill（自动暴露为 `/cadence-init` / `/cadence-handoff` / `/cadence-resume` / `/cadence-bootstrap` / `/project-discuss` slash command），并注册 `recall-retriever` / `recall-consolidator` / `recall-analyzer` 三个 named subagent（context 隔离，与 CC 等价）。

`bootstrap` 自动注入只在项目根存在 `cadence/_INDEX.md`（即跑过 `/cadence-init`）时生效——未 init 项目不会被污染。

详细说明（含 Windows install 故障排查、版本锁定、卸载步骤）见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md)。

### Codex CLI / App / IDE

**前置条件**：

- Codex CLI **v0.117.0+**（`codex --version` 检查）
- `~/.codex/config.toml` 启用 multi-agent（cadence 依赖 subagent 调度）：
  ```toml
  [features]
  multi_agent = true
  ```

> ⚠️ Codex 0.129 上 marketplace 模式因 [issue #17066](https://github.com/openai/codex/issues/17066) **拒绝**注册 plugin 在 repo 根的 marketplace（CLI add 看似成功但 plugin 实际不会装载）。**当前推荐 Symlink 模式**；marketplace 模式作为实验路径备查，等 Codex 修复后会回归推荐。

**Symlink 模式（推荐）**

```bash
# 1. clone cadence 到任意位置（下方以 ~/.codex/cadence 为例，可改成任何绝对路径）
git clone https://github.com/hxt9805/cadence.git ~/.codex/cadence

# 2. 建 symlink：target 必须指向 clone 目录下的 skills/ 子目录

# macOS / Linux：
mkdir -p ~/.agents/skills
ln -s ~/.codex/cadence/skills ~/.agents/skills/cadence

# Windows（admin PowerShell：右键 → 以管理员身份运行）：
New-Item -ItemType Directory -Force -Path "$HOME\.agents\skills" | Out-Null
New-Item -ItemType SymbolicLink -Path "$HOME\.agents\skills\cadence" -Target "$HOME\.codex\cadence\skills"
```

> **路径自定义**：上面的 `~/.codex/cadence` 只是推荐位置，可以替换成任意绝对路径（如 `D:\dev\cadence`、`~/projects/cadence`），symlink 的 `-Target` / `ln -s` 源路径同步替换为 `<你的clone路径>/skills`。**关键**：symlink target 必须是 `skills/` 子目录，**不是 repo 根**（否则 Codex 找不到各 skill 的 SKILL.md）。
>
> **Windows 用户避免 admin**：打开 `设置 → 隐私和安全性 → 开发人员选项`，把 "**开发人员模式**" 拨到 ON，之后普通 PowerShell 跑 `mklink /D %USERPROFILE%\.agents\skills\cadence %USERPROFILE%\.codex\cadence\skills` 也能创建 symlink，无需 admin。

**验证安装**（重启 Codex 后）：

```powershell
codex debug prompt-input "test" | Select-String -Pattern 'cadence:'
```

应该能看到 `cadence:cadence-bootstrap` / `cadence:project-discuss` / `cadence:cadence-init` 等 5 个 skill 出现。

更详细的 Symlink 安装说明（含 macOS / Linux / Windows 各档位 + 卸载步骤）见 [.codex/INSTALL.md](.codex/INSTALL.md)。

**Marketplace 模式（实验性，Codex 0.129 上不稳定）**

> ⚠️ 已知问题：受 [Codex issue #17066](https://github.com/openai/codex/issues/17066) 影响，CLI `marketplace add` 看似成功但 Codex 不会真正装载 plugin（plugin 路径解析逻辑拒绝 repo 根布局）。修复前请用上面的 Symlink 模式。

```bash
codex plugin marketplace add https://github.com/hxt9805/cadence.git
```

成功后会自动写入 `~/.codex/config.toml`：

```toml
[marketplaces.cadence]
source_type = "git"
source = "https://github.com/hxt9805/cadence.git"
```

随后在 Codex App **Plugins** 面板里启用 `cadence@cadence`。或手动在 `config.toml` 末尾加入：

```toml
[plugins."cadence@cadence"]
enabled = true
```

> 详细 Codex 形态适配（subagent dispatch 铁律 / sandbox / `$plugin:skill` 触发语法 / context 预算）见 [`skills/project-discuss/references/harness-adapters.md`](skills/project-discuss/references/harness-adapters.md)。

## 安装/降级到历史版本

如果不想用最新 stable,想锁某个旧版本,用本地 marketplace fallback。把 `v0.2.0` 换成 [Releases 页](https://github.com/hxt9805/cadence/releases) 上的任意 tag。

### Claude Code

```bash
git clone --branch v0.2.0 https://github.com/hxt9805/cadence.git ~/cadence-v0.2.0
# 注意：该目录是 CC 的 marketplace 源,clone 后不要删除,否则 plugin 会失效
```

然后在 CC 里：

```
/plugin marketplace add ~/cadence-v0.2.0
/plugin install cadence@cadence
```

### Codex CLI / App

```bash
git clone --branch v0.2.0 https://github.com/hxt9805/cadence.git ~/cadence-v0.2.0
```

`~/.codex/config.toml` 改成：

```toml
[marketplaces.cadence]
source_type = "local"
source = "/Users/你/cadence-v0.2.0"
```

## 使用

### 首次使用流程

1. **初始化** — 在项目根目录跑 `/cadence-init`，按提示选模式（新项目极简模板 / 扫描已有项目生成快照）。完成后会创建 `cadence/` 目录骨架。
2. **重新加载协议** — **CC 用户**运行 `/clear`，让 SessionStart hook 重新触发并把 cadence bootstrap 注入当前 session；**OpenCode 用户**重启 OpenCode 让 plugin re-init；**Codex 用户**重新开启 session 让 native skill discovery 重新扫描。
   > **为什么需要这一步？** bootstrap 注入只在 session 启动时检查项目状态；首次 init 是在 session 中途完成的，注入逻辑在你启动 session 时检查到项目尚未初始化、跳过了注入。重启 / clear 一次让它重新检测到新建的 `cadence/_INDEX.md`。**后续新 session 自动加载，无需再操作。**
3. **开始讨论** — 之后正常和 Claude 讨论项目，cadence 按"已被承接"判据自动落地决策到 `cadence/streaming/`；长 session 时跑 `/cadence-handoff` 整理到档案。

### Session 启动行为

- **已 init 项目**（项目根存在 `cadence/_INDEX.md`）：CC 通过 SessionStart hook 自动注入 bootstrap；OpenCode 通过 plugin `experimental.chat.messages.transform` hook 自动注入（行为与 CC 等价）；Codex 通过 native skill discovery 加载 cadence-bootstrap 描述并按需取全文。
- **未 init 项目**：bootstrap 不注入，cadence 不接入；用户主动跑 `/cadence-init` 才进入工作流。CC / OpenCode / Codex 行为一致。

### 命令对照

| 操作 | Claude Code | OpenCode | Codex |
| --- | --- | --- | --- |
| 初始化项目 | `/cadence-init` | `/cadence-init` | `$cadence:cadence-init` |
| 整理本 session 到档案 | `/cadence-handoff` | `/cadence-handoff` | `$cadence:cadence-handoff` |
| 继续之前某次 session | `/cadence-resume` | `/cadence-resume` | `$cadence:cadence-resume` |

详细约定见 [`skills/cadence-bootstrap/SKILL.md`](skills/cadence-bootstrap/SKILL.md)。

## 更新插件

cadence 不会自动更新；远端发布新版本后需要手动触发。

### Claude Code

```
/plugin marketplace update cadence
/plugin update cadence@cadence
/clear
```

`/clear` 让 SessionStart hook 重新触发，加载新版 bootstrap 内容。

> Windows 上 `/plugin marketplace update` 可能因文件锁报 `EBUSY: resource busy or locked`——这是 CC 端的 known issue（CC 自身持有 marketplace 目录文件句柄导致 rename 失败）。临时 workaround：完全退出 CC → `Remove-Item -Recurse -Force "$HOME\.claude\plugins\marketplaces\cadence*"` → 重新打开 CC → 重新跑 `/plugin marketplace add` 安装命令。

### Codex CLI / App

```bash
codex plugin marketplace upgrade cadence
```

完成后重启 Codex CLI / App 让新 skill 生效。

## 从早期版本迁移

如果你之前装过 `cadence@cadence-dev`（v0.1.0 阶段的旧 marketplace 名），升级到 v0.2.0+ 时 CC 不会自动迁移 marketplace 注册（CC 把旧 git URL 跟 `cadence-dev` 这个名字 hash 绑定），需要手工清理旧状态。

### Claude Code

```powershell
# 1. 完全退出 CC（含 system tray）
# 2. PowerShell 跑：
Remove-Item -Recurse -Force "$HOME\.claude\plugins\marketplaces\cadence-dev*" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$HOME\.claude\plugins\plugins\cadence@cadence-dev*" -ErrorAction SilentlyContinue
# 3. 编辑 ~/.claude/plugins/known_marketplaces.json，删除 "cadence-dev" 这个 key 整段
# 4. 重启 CC，按 "## 安装 → Claude Code" 重新走流程
```

### Codex CLI / App

```powershell
# 1. 退出 Codex
# 2. 编辑 ~/.codex/config.toml：
#    - 删除 [marketplaces.cadence-dev] 整段
#    - 删除 [plugins."cadence@cadence-dev"] 整段
# 3. 清旧 plugin cache：
Remove-Item -Recurse -Force "$HOME\.codex\plugins\cache\cadence-dev" -ErrorAction SilentlyContinue
# 4. 重启 Codex，按 "## 安装 → Codex CLI / App / IDE" 走 Symlink 模式重新装
```

迁移完成后，新版 cadence 在 CC / Codex 上都是 `cadence@cadence`（不再有 `-dev` 后缀）。

## 平台与兼容性

### Harness 形态

cadence 在 **Claude Code 与 OpenCode 上为 first-class 形态**（两边都通过原生机制支持自动 bootstrap 注入、Task tool fork named subagent、context 隔离）。Codex CLI / App / IDE 通过兼容层支持:

| 能力 | Claude Code（first-class） | OpenCode（first-class） | Codex（兼容层） |
| --- | --- | --- | --- |
| Bootstrap 注入 | SessionStart hook 自动 | plugin `experimental.chat.messages.transform` hook 自动 | native skill discovery + LLM 按需取全文 |
| Subagent fork | Task tool 一键自主 fork（CC 自动加载 `agents/*.md`） | Task tool 一键自主 fork（plugin 启动时注册 named subagent，prompt body 预加载） | 主 LLM 用 `spawn_agent` + XML 包裹模拟 |
| 插件路径变量 | `${CLAUDE_PLUGIN_ROOT}` 注入 | LLM 按"当前 skill root 的相对路径"自解析 | LLM 按"当前 skill root 的相对路径"自解析 |
| Slash command | `/cadence-handoff` | `/cadence-handoff`（OpenCode 自动从 skill name 生成） | `$cadence:cadence-handoff` |

Codex 形态下部分行为**依赖 LLM 自适应**（尤其是路径解析与 subagent 调用形式），corner case 可能需要主 LLM 推断到位。详细 mapping + 调度铁律 + OpenCode 工具映射见 [`skills/project-discuss/references/harness-adapters.md`](skills/project-discuss/references/harness-adapters.md)。

### 操作系统

| OS | 支持情况 |
| --- | --- |
| Windows 10 / 11 | ✅ 主要开发 / 测试平台 |
| macOS | ⚠️ 静态审查通过(命令名 / shell / awk 跨平台已处理),社区实测反馈待补 |
| Linux | ⚠️ 同上 |

**命令名差异**(SKILL.md 已含平台备注,此处说明背景):

- Windows:`python skills/cadence-handoff/scripts/validate_handoff.py ...`
- macOS / Linux:`python3 skills/cadence-handoff/scripts/validate_handoff.py ...`

macOS 12+ 已移除 system `python`,只保留 `python3`;Debian 12+ 等新发行版同样如此。LLM 在跑 cadence 命令时会按 SKILL.md 的平台备注选对的命令名。

如果你在 Mac / Linux 上跑 cadence 遇到问题,欢迎在仓库开 issue 反馈。

## 故障排查

### `Permission denied (publickey)` — SSH 认证失败

如果你执行的是简写形式 `/plugin marketplace add hxt9805/cadence`，Claude Code 会在底层走 SSH 协议（`git@github.com:...`）clone 仓库；当你没有为 GitHub 配置 SSH key 时就会报这个错。**Windows 用户默认环境通常没有 SSH key，尤其容易遇到。**

两种解决办法，任选其一：

- **改用 HTTPS（推荐）**：直接用[安装段](#claude-code)给出的完整 URL 命令 `/plugin marketplace add https://github.com/hxt9805/cadence.git`，对所有人都通用，不依赖 SSH。
- **配置 GitHub SSH key**：参考 [GitHub 官方文档](https://docs.github.com/cn/authentication/connecting-to-github-with-ssh) 一次性完成配置，之后简写形式也能用。

### OpenCode 安装 / plugin 加载问题

OpenCode 形态的常见失败模式（plugin 未加载、bootstrap 未注入、Windows `git+https` 安装失败、subagent 调用报 `Unknown agent type` 等）详见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md) 的「Troubleshooting」段。

## License

MIT
