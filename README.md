# cadence

讨论驱动的软件开发工作流插件 — 通过 **记 / 整 / 查** 三阶段记录协议，把 Claude Code / Codex session 的讨论、决策、TODO 自动落地到项目档案中，支持长 session handoff 与跨 session resume。

> **推荐在 Claude Code 中使用**(first-class 形态)。Codex CLI / App / IDE 通过兼容层支持——SessionStart hook、Task tool、`${CLAUDE_PLUGIN_ROOT}` 在 Codex 没有原生等价,部分体验依赖 LLM 自适应;详见下文 [平台与兼容性](#平台与兼容性)。

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

### Codex CLI / App / IDE

**前置条件**：

- Codex CLI **v0.117.0+**（`codex --version` 检查）
- `~/.codex/config.toml` 启用 multi-agent（cadence 依赖 subagent 调度）：
  ```toml
  [features]
  multi_agent = true
  ```

**Marketplace 模式（推荐）**：

```bash
codex plugin marketplace add https://github.com/hxt9805/cadence.git
```

成功后会自动写入 `~/.codex/config.toml`：

```toml
[marketplaces.cadence]
source_type = "git"
source = "https://github.com/hxt9805/cadence.git"
```

随后在 Codex App **Plugins** 面板里启用 `cadence@cadence`。如果 CLI 添加后没有自动启用，手动在 `~/.codex/config.toml` 末尾加入：

```toml
[plugins."cadence@cadence"]
enabled = true
```

**验证安装**（重启 Codex App / CLI 后）：

```powershell
codex debug prompt-input "test" | Select-String -Pattern 'cadence'
```

应该能看到 `cadence:cadence-bootstrap` / `cadence:project-discuss` / `cadence:cadence-init` 等 skill 出现。

**Symlink 模式**（开发者 fallback，免 marketplace 也能用）：详见 [.codex/INSTALL.md](.codex/INSTALL.md)。

> 详细 Codex 形态适配（subagent dispatch 铁律 / sandbox / `$plugin:skill` 触发语法 / context 预算）见 [`skills/project-discuss/references/codex-tools.md`](skills/project-discuss/references/codex-tools.md)。

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
2. **重新加载协议** — 运行 `/clear`，让 SessionStart hook 重新触发并把 cadence bootstrap 注入当前 session。
   > **为什么需要这一步？** hook 只在 session 启动 / `/clear` / `/compact` 时执行；首次 init 是在 session 中途完成的，hook 在你启动 session 时检查到项目尚未初始化、跳过了注入。`/clear` 一次让它重新检测到新建的 `cadence/_INDEX.md`。**后续新 session 自动加载，无需再 clear。**
3. **开始讨论** — 之后正常和 Claude 讨论项目，cadence 按"已被承接"判据自动落地决策到 `cadence/streaming/`；长 session 时跑 `/cadence-handoff` 整理到档案。

### Session 启动行为

- **已 init 项目**（项目根存在 `cadence/_INDEX.md`）：CC 通过 SessionStart hook 自动注入 bootstrap；Codex 通过 native skill discovery 加载 cadence-bootstrap 描述并按需取全文。
- **未 init 项目**：bootstrap 不注入，cadence 不接入；用户主动跑 `/cadence-init` 才进入工作流。CC 与 Codex 行为一致。

### 命令对照

| 操作 | Claude Code | Codex |
| --- | --- | --- |
| 初始化项目 | `/cadence-init` | `$cadence:cadence-init` |
| 整理本 session 到档案 | `/cadence-handoff` | `$cadence:cadence-handoff` |
| 继续之前某次 session | `/cadence-resume` | `$cadence:cadence-resume` |

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

## 平台与兼容性

### Harness 形态

cadence 是为 **Claude Code 形态**设计的(依赖 SessionStart hook、Task tool 自主 fork subagent、`${CLAUDE_PLUGIN_ROOT}` 路径变量)。Codex CLI / App / IDE 通过兼容层支持:

| 能力 | Claude Code(first-class) | Codex(兼容层) |
| --- | --- | --- |
| Bootstrap 注入 | SessionStart hook 自动 | native skill discovery + LLM 按需取全文 |
| Subagent fork | Task tool 一键自主 fork | 主 LLM 用 `spawn_agent` 等内置工具模拟 |
| 插件路径变量 | `${CLAUDE_PLUGIN_ROOT}` 注入 | LLM 按"当前 skill root 的相对路径"自解析 |
| Slash command | `/cadence-handoff` | `$cadence:cadence-handoff` |

Codex 形态下部分行为**依赖 LLM 自适应**(尤其是路径解析与 subagent 调用形式),corner case 可能需要主 LLM 推断到位。详细 mapping + 调度铁律见 [`skills/project-discuss/references/codex-tools.md`](skills/project-discuss/references/codex-tools.md)。

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

## License

MIT
