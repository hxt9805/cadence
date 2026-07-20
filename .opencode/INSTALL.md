# 在 OpenCode 中安装 cadence

## 前置条件

- [OpenCode.ai](https://opencode.ai) 已安装
- 项目已经跑过 `/cadence-init`（项目根存在 `cadence/_INDEX.md`）— bootstrap 自动注入只在 cadence-managed 项目里生效

## 安装

把 cadence 加到 `opencode.json` 的 `plugin` 数组（global 或 project-level 都可以）：

```json
{
  "plugin": ["cadence@git+https://github.com/hxt9805/cadence.git"]
}
```

重启 OpenCode。plugin manager 会自动 clone 仓库并：
- 把 `skills/` 路径注入 `config.skills.paths` → 5 个 cadence skill 自动暴露为 slash command（`/cadence-init` / `/cadence-handoff` / `/cadence-resume` / `/cadence-bootstrap` / `/project-discuss`）
- 注册 3 个 named subagent（`recall-retriever` / `recall-consolidator` / `recall-analyzer`）到 `config.agent[]`，agent system prompt 从 `skills/project-discuss/agents/*.md` 预加载
- 在 cadence-managed 项目里通过 `experimental.chat.messages.transform` hook 自动注入 cadence-bootstrap 内容到首条 user message（与 CC SessionStart hook 行为等价）

> **多 harness 用户注意**：同一项目同时给 Claude Code / Codex / OpenCode 用 cadence 时，每个 harness 都要按各自的方式装一次（CC 用 marketplace、Codex 用 symlink、OpenCode 用 opencode.json）。三边共用同一份 `skills/` 内容，行为对齐。

## 验证安装

启动 OpenCode 并打开一个 cadence-managed 项目，输入 `/` 应能看到 5 个 cadence skill：

- `/cadence-init`
- `/cadence-handoff`
- `/cadence-resume`
- `/cadence-bootstrap`
- `/project-discuss`

问主 session「你现在在 cadence 项目里吗？看到协议了吗？」，预期回答包含「记/整/查 三阶段、`_ACTIVE.md` / `_INDEX.md` 分文件管理」等内容。

## Usage

### Slash command

跟 CC 上一致：

- `/cadence-init` — 初始化 cadence 工作流
- `/cadence-handoff` — 长 session 换新 session 前整理到档案
- `/cadence-resume` — 恢复之前某次 session 上下文
- `/cadence-bootstrap` — 手动加载 cadence 协议（一般不用，bootstrap 已自动注入）
- `/project-discuss` — 显式触发讨论 / 决策 / 查询协议

### Subagent 调度

OpenCode 上调 cadence 的 named subagent，跟 CC 上写法一致：

```
Task tool:
  subagent_type: "recall-retriever"   # 或 recall-consolidator / recall-analyzer
  prompt: "<具体任务描述>"
  description: "<3-5 字短描述>"
```

agent 的 system prompt（`agents/*.md` body）已由插件预加载——**调用时只传 task input，不需要手动读 agent 文件再传**。

## 更新

OpenCode 通过 git-backed package spec 装 cadence。某些 OpenCode / Bun 版本会在 lockfile 或缓存里 pin 已解析的 git dependency，重启不一定拉到新 commit。如果更新没生效，清 OpenCode 包缓存或重装 plugin。

锁版本：

```json
{
  "plugin": ["cadence@git+https://github.com/hxt9805/cadence.git#v0.6.0"]
}
```

## Troubleshooting

### Plugin 没加载

```bash
opencode run --print-logs "hello" 2>&1 | grep -i cadence
```

应能看到 plugin 被发现并加载的日志。

### Windows 安装问题

某些 Windows OpenCode 版本在 `git+https://` plugin spec 上有 upstream installer 问题（Bun 找不到 `git.exe`、缓存路径异常等）。fallback 方案是先用系统 npm 装到 OpenCode 的本地路径：

```powershell
npm install cadence@git+https://github.com/hxt9805/cadence.git --prefix "$HOME\.config\opencode"
```

然后 `opencode.json` 指向本地路径：

```json
{
  "plugin": ["~/.config/opencode/node_modules/cadence"]
}
```

### Bootstrap 没注入

- 确认项目根有 `cadence/_INDEX.md`（这是 gating 条件）
- 如果是新项目，先跑 `/cadence-init`

### Subagent 跑不起来

如果 `recall-retriever` / `recall-consolidator` / `recall-analyzer` 在 `/` 列表里出现但 Task 调用失败：

- 检查 `skills/project-discuss/agents/` 下 3 个 .md 文件是否齐全
- 看 plugin 加载日志确认 `config.agent[]` 注册没报错

## 从 Codex symlink 安装迁移

如果之前在 OpenCode 上手工建了 symlink（如把 `~/.codex/cadence/skills` 链到 `~/.config/opencode/skills/cadence`），先清理旧 symlink 再装新 plugin：

```bash
# macOS / Linux
rm -f ~/.config/opencode/skills/cadence
rm -f ~/.config/opencode/plugins/cadence.js

# Windows (admin PowerShell 或开发者模式)
Remove-Item "$HOME\.config\opencode\skills\cadence" -Force
Remove-Item "$HOME\.config\opencode\plugins\cadence.js" -Force
```

然后按上方「安装」步骤走 opencode.json 路径。

## Getting Help

- Report issues: https://github.com/hxt9805/cadence/issues
- 完整跨平台对比：仓库根 [README.md](../README.md) 的「平台与兼容性」段
