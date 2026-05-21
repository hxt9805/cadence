# Changelog

All notable changes to cadence are documented here. This project adheres to [Semantic Versioning](https://semver.org/) starting from v0.2.0.

## [0.3.2] - 2026-05-21

### Changed
- **recording-protocol.md §2**：在「写入原则：假设读者无上下文」章节后新增 `#### 信息密度正反例` 子节，把 v0.3.1 引入的 context-loss awareness 原则具象化为可对照的真实例子（❌ 密度过低 vs ✅ 密度足够，使用 UX 决策案例）。设计意图：让"密度足够"的标准从抽象描述变为视觉对照，降低 LLM 在写 entry 时的"自由发挥"空间。本次纯文档改动，不动 schema、validator、字段必填要求。

## [0.3.1] - 2026-05-19

### Fixed
- **跨 session 信息衰减**：streaming entry 被写入的 LLM（拥有完整讨论上下文）和下游 session 读取的 LLM（无上下文）之间存在信息不对称，导致下游基于不完整记录产出设计文档时出现遗漏或错误（如字段类型缺失、决策细节丢失）。本次通过两条协议层修改消解此问题：

### Changed
- **recording-protocol.md §2**：新增「写入原则：假设读者无上下文」，要求 entry 写入时设身处地为下游读者考虑——`chosen` 包含足够特异性、技术规格写出类型/签名/约束、依赖约束在 `context` 注明。附加"特异性 ≠ 冗长"桥接句，防止原则被误解为鼓励冗长。
- **recording-protocol.md §7 + project-discuss/SKILL.md §6**：反驳 #5 措辞对齐 bootstrap 立场（"漏记 > 噪音"），从"漏写的代价远大于写了不读"改为"判断不重要的标准是承接信号而非主观感觉，噪音风险由整合阶段处理"。此前三处文件存在自相矛盾（record §5 说不确定时倾向不记、§7 反驳说漏写代价大、bootstrap 说漏记 > 噪音），本次统一消除。

## [0.3.0] - 2026-05-18

引入 **OpenCode 形态 first-class 支持**,cadence 现在跨三个 harness 平台:Claude Code(first-class)、OpenCode(first-class)、Codex CLI / App / IDE(兼容层)。

### Added
- **`.opencode/plugin/cadence.js`** — OpenCode JS plugin。`config` hook 注入 `skills.paths` + 注册 3 个 named subagent(`recall-retriever` / `recall-consolidator` / `recall-analyzer`)到 `cfg.agent[]`,system prompt 从 `skills/project-discuss/agents/*.md` 预加载;`experimental.chat.messages.transform` hook 在 cadence-managed 项目(根含 `cadence/_INDEX.md`)里自动注入 cadence-bootstrap 内容到首条 user message。
- **`package.json`** — 让 OpenCode 能通过 `cadence@git+https://github.com/hxt9805/cadence.git` 安装。
- **`.opencode/INSTALL.md`** — OpenCode 安装指南(含 Windows install 故障排查、版本锁定、卸载步骤)。
- **`skills/project-discuss/references/opencode-tools.md`** — OpenCode 形态工具映射(SessionStart 注入 / Subagent fork / Slash command / `${CLAUDE_PLUGIN_ROOT}` 解析 / context 预算的等价机制)。

### Changed
- `README.md` 顶部从「推荐 Claude Code,Codex 兼容」改为「Claude Code 与 OpenCode 均 first-class,Codex 兼容层」;新增 OpenCode 安装段;命令对照表加 OpenCode 列;平台兼容性对比表扩展为三平台。
- `cadence-bootstrap` 「Codex 形态调度铁律」标题维持(CC / OpenCode 形态可忽略本节),OpenCode 形态下不需要等价铁律——Task tool 原生支持 named subagent fork + context 隔离,与 CC 等价。

### Platform Status
| Harness | 形态 | Bootstrap 注入 | Subagent fork | Slash command |
| --- | --- | --- | --- | --- |
| Claude Code | first-class | SessionStart hook | Task tool + named agent | `/cadence-*`(`commands/` routing) |
| OpenCode | first-class | plugin message transform hook | Task tool + plugin 注册 named subagent | `/cadence-*`(skill name 自动生成) |
| Codex CLI / App / IDE | 兼容层 | native skill discovery | `spawn_agent` + XML 包裹 | `$cadence:cadence-*` |

## [0.2.1] - 2026-05-14

### Fixed
- **handoff 路径文档不一致**(自 v0.1.0 起遗留):多处 SKILL.md / agents 文档对 `.handoff/` 位置字面描述不一致(`cadence/.handoff/` vs 裸 `.handoff/`),导致不同 Claude 实例可能将 handoff 文件写到项目根而非 `cadence/.handoff/`。统一所有路径引用为 `cadence/.handoff/` + 在 `cadence-handoff` / `cadence-resume` 顶部加路径约定声明 + `cadence-resume` Step 1 加前置检测护栏(发现项目根 `.handoff/` 提示迁移)。
- **迁移**:若你的项目里 `.handoff/` 在项目根 → 一行 `mv .handoff cadence/.handoff`(参 `cadence-resume` Step 1 前置检测的提示)。沿用现有"不强迁老 handoff"策略,不提供一键脚本。

## [0.2.0] - 2026-05-08

首个正式发布版本(带 git tag 和 GitHub Release)。

### Added
- SessionStart hook gates bootstrap injection on `cadence/_INDEX.md` presence
- Codex CLI / App / IDE compatibility layer with full install docs

### Fixed
- Hook line endings pinned for cross-platform consistency (CRLF/LF)
- `cadence-handoff` validator bundled into plugin (write-time check works)
- README troubleshooting for SSH auth failures on plugin install

### Changed
- Marketplace renamed from `cadence-dev` to `cadence` (install command becomes `/plugin install cadence@cadence`)
- README repositions Claude Code as primary harness, Codex as compatibility layer
- `.claude-plugin/marketplace.json` `source` now uses object form with `ref: "v0.2.0"` (pins to git tag)

### Known Issues
- **Codex marketplace mode is blocked by [Codex issue #17066](https://github.com/openai/codex/issues/17066)** — Codex 0.129's plugin path resolver rejects marketplaces whose plugin sits at the repo root (cadence's layout). CLI `marketplace add` succeeds but plugin is never loaded into session. **Workaround**: use Symlink mode (see [`.codex/INSTALL.md`](.codex/INSTALL.md) and the Codex section in README). Once OpenAI lands a fix, marketplace mode will become recommended again.
- **CC marketplace rename is not auto-migrated** — CC binds the git URL to the old `cadence-dev` marketplace name in `known_marketplaces.json`. Users who installed v0.1.x must clear that entry manually before the new `cadence` marketplace can register. See "从早期版本迁移" in README.

### Note
v0.1.0 was a pre-tag stage release (no git tag, no formal release notes). Starting from v0.2.0, cadence enforces strict SemVer with immutable tags and proper release notes.
