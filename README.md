# cadence

讨论驱动的软件开发工作流插件 — 通过 **记 / 整 / 查** 三阶段记录协议，把 Claude Code / Codex session 的讨论、决策、TODO 自动落地到项目档案中，支持长 session handoff 与跨 session resume。

> 双 harness 支持：Claude Code（SessionStart hook 注入 bootstrap）+ Codex CLI / App / IDE（native skill discovery + Codex 形态调度铁律）。

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
/plugin install cadence@cadence-dev
```

### Codex CLI / App / IDE

**Marketplace 模式**（推荐）：在 Codex App **Plugins** 面板点 `Add marketplace` → 给 source 路径（本地 repo 目录或 git URL，Codex 会自动找 `<root>/.agents/plugins/marketplace.json`）→ 安装 `cadence@cadence-dev`。配置自动写入 `~/.codex/config.toml` `[plugins]` 段。

**Symlink 模式**（开发者，免 marketplace 也能用）：详见 [.codex/INSTALL.md](.codex/INSTALL.md)。

> 详细 Codex 形态适配（subagent dispatch 铁律 / sandbox / `$plugin:skill` 触发语法 / context 预算）见 [`skills/project-discuss/references/codex-tools.md`](skills/project-discuss/references/codex-tools.md)。

## 使用

cadence 在 session 启动时自动接入：
- **Claude Code** 通过 SessionStart hook 注入 cadence-bootstrap 全文
- **Codex** 通过 native skill discovery 加载 cadence-bootstrap 描述并按需取全文

随后讨论自然进行，cadence 自动记录命中判据的决策。命令对照：

| 操作 | Claude Code | Codex |
| --- | --- | --- |
| 整理本 session 到档案 | `/cadence-handoff` | `$cadence:cadence-handoff` |
| 继续之前 session | `/cadence-resume` | `$cadence:cadence-resume` |
| 初始化新项目骨架 | `/cadence-init` | `$cadence:cadence-init` |

详细约定见 [`skills/cadence-bootstrap/SKILL.md`](skills/cadence-bootstrap/SKILL.md)。

## 故障排查

### `Permission denied (publickey)` — SSH 认证失败

如果你执行的是简写形式 `/plugin marketplace add hxt9805/cadence`，Claude Code 会在底层走 SSH 协议（`git@github.com:...`）clone 仓库；当你没有为 GitHub 配置 SSH key 时就会报这个错。**Windows 用户默认环境通常没有 SSH key，尤其容易遇到。**

两种解决办法，任选其一：

- **改用 HTTPS（推荐）**：直接用[安装段](#claude-code)给出的完整 URL 命令 `/plugin marketplace add https://github.com/hxt9805/cadence.git`，对所有人都通用，不依赖 SSH。
- **配置 GitHub SSH key**：参考 [GitHub 官方文档](https://docs.github.com/cn/authentication/connecting-to-github-with-ssh) 一次性完成配置，之后简写形式也能用。

## License

MIT
