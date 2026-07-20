# Kimi Code CLI 安装支持 — 设计

> **日期**: 2026-07-20
> **分支**: preview
> **状态**: 已实施

## 背景

cadence 已支持 Claude Code(first-class)/ OpenCode(first-class)/ Codex(兼容层)。
目标:让插件也能通过 **Kimi Code CLI 的自定义插件市场**安装。

## 调研结论(Kimi Code 插件机制,Beta)

- 插件 manifest:repo 根 `kimi.plugin.json`(或 `.kimi-plugin/plugin.json`,root 优先)
- Plugin skill 即标准 Agentskills 格式(`<name>/SKILL.md`),manifest `"skills": "./skills/"` 直接复用 cadence 现有 `skills/` 目录,零改动
- 自定义市场:`/plugins marketplace <json-url-or-path>`,格式 `{"version":"1","plugins":[{id,tier,displayName,version,description,keywords,source}]}`,source 支持 GitHub URL(含 `/tree/<ref>`)
- 安装:`/plugins install <github-url>`(支持 `/tree/<ref>` `/releases/tag/<tag>` `/commit/<sha>`),或市场 UI 安装;安装后 `/reload` + 新会话生效
- `sessionStart.skill` 可在会话启动强制注入某 skill 全文,但**无 gating**,对所有项目无条件生效

## 关键决策

| # | 决策 | 理由 |
|---|---|---|
| K1 | manifest 只声明 `skills`,**不加 `sessionStart.skill`** | 与 Codex 兼容层同策略(软 gating):bootstrap description 自带触发条件「项目根存在 `cadence/_INDEX.md`」,LLM 按需加载全文;符合 ADR-001 opt-in 原则,非 cadence 项目零污染 |
| K2 | 软 gating 对 Kimi 成立 | Kimi 与 Codex 的 skill 发现同构(description 注入系统提示 + progressive disclosure);且 bootstrap §10 有双保险(先 `ls cadence/` 确认骨架) |
| K3 | 市场文件放 `.kimi-plugin/marketplace.json`,含 `cadence`(stable)+ `cadence-preview`(`/tree/preview`)两条 | 对齐 CC `.claude-plugin/marketplace.json` 的双轨策略 |
| K4 | subagent 不注册,依赖 LLM 自适应 | Kimi plugin manifest 无 agents 字段;`recall-*` 三个 agent 由主 LLM 读 `skills/project-discuss/agents/*.md` 后按 Kimi subagent(swarm)机制调度,与 Codex 兼容层同级 |

## 改动文件

| 文件 | 内容 |
|---|---|
| `kimi.plugin.json`(新增,repo 根) | name/version/description/keywords/author/homepage/license + `skills: ["./skills/"]` + interface |
| `.kimi-plugin/marketplace.json`(新增) | Kimi 市场格式,cadence + cadence-preview 两条 |
| `README.md`(修改) | 安装节加 Kimi 段(自定义市场 + 直接安装 + 验证)、命令对照表加 Kimi 列、Harness 形态表加 Kimi 列、首次使用流程/更新插件节补 Kimi |

## 已知缺口(follow-up,不在本次范围)

- `harness-adapters.md` 未加 Kimi 节(subagent 调度细节、工具映射);待 dogfood 后补充
- Kimi hooks(Beta)未来可用于硬 gating bootstrap 注入;当前 Beta 且增加复杂度,不做
- Kimi plugin 目前按用户级安装对所有项目生效(官方后续支持项目级)
