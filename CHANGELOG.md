# Changelog

All notable changes to cadence are documented here. This project adheres to [Semantic Versioning](https://semver.org/) starting from v0.2.0.

## [0.6.0] - 2026-07-20

cadence v0.6:domain-neutral recording fidelity(记录保真度协议)+ 项目发现泛化 + Kimi Code CLI 支持。

**核心成果**:决定记录从"记了就行"升级为"按重要性分级、可校验的保真度协议"——记 阶段自适应保真度、整 阶段归档前强制 canonical coverage、查/resume 阶段走 verified canonical pointers,三阶段全部有 validator 兜底。同时 cadence-init 项目扫描不再假设特定项目形态,任意领域项目均可初始化。

### Added
- **Recording fidelity 分级协议** — 新增 `project-discuss/references/recording-fidelity.md`:记 阶段按决定的重要性自适应记录粒度(关键决定必须带 rationale,琐碎决定允许简记),`cadence-bootstrap` / `project-discuss` L0 层同步接入
- **归档前 canonical coverage 强制校验** — `recall-consolidator` 生成的归档计划必须证明 streaming entry 已被 canonical 文档覆盖才允许 archive,`validate_consolidator_plan.py` 新增 coverage 校验(缺覆盖直接 fail)
- **Handoff / Resume 走 verified canonical pointers** — `cadence-handoff` 写 snapshot 时校验指针指向真实 canonical 内容,`cadence-resume` 恢复时先验证指针有效性,防止从失效书签恢复出错误上下文(`validate_handoff.py` 同步升级)
- **Streaming entry 保真度校验** — `validate_streaming.py` 新增 domain-neutral decision fidelity 检测(如高重要性决定缺 rationale 会被标出)
- **Kimi Code CLI 安装支持** — 新增 `kimi.plugin.json` manifest + `.kimi-plugin/marketplace.json` 自定义 marketplace,README 增加 Kimi Code 安装说明(兼容层,与 Codex 同级)
- 跨 runtime(CC / OpenCode / Codex)recording fidelity 回归测试 + domain-neutral project 契约测试

### Changed
- **cadence 项目发现泛化** — `cadence-init` 的 `project-scanner` / `scan-rules` 重写:不再假设软件项目形态,任意领域(写作、研究、生活规划等)项目均可 `/cadence-init`;`query-behavior.md` 同步去领域化
- `recording-protocol.md` 接入 fidelity 分级引用,`project-discuss/SKILL.md` / `cadence-bootstrap/SKILL.md` 相应精简重排

### Fixed
- **Codex preview marketplace 无法安装** — 移除损坏的 `.agents/plugins/marketplace.json`,preview channel 在 Codex 下恢复可装(附 runtime loading 契约测试防回归)

### Migration notes
- 从 v0.5.0 升级:`/plugin marketplace update cadence` + `/plugin update cadence@cadence` + `/clear`,无需额外操作
- 已有 cadence 档案完全兼容;fidelity 校验只约束新写入的 entry

---

## [0.5.0] - 2026-05-24

cadence v0.5 协议三层化改造完成 + dual-channel marketplace 引入。

**核心成果**: 删 `_CONVENTIONS.md` scaffold + cadence-init 大幅简化(230 → 125 行)+ L2 references 合并(6 个 → 3 个)+ 借口反驳表 L0/L1 双层 inline + G 信息密度强化(YAML frontmatter recommended)。

> ⚠️ **跳过 v0.4.x**: v0.4.0 是 dev-local 上的 internal milestone commit (d471060 "prepare v0.4.0"),**从未 tag / release**。v0.5.0 是从 v0.3.1 stable 升级的下一个正式 release,包含 v0.4 + v0.5 全部累积改动。本 CHANGELOG `[0.4.0]` entry 保留作 historical record。

### Added
- **Dual-channel marketplace** — `cadence@cadence` (stable) + `cadence-preview@cadence` (preview 分支 latest),用户按需选 channel
- **L2 `harness-adapters.md`** — 合并 codex-tools + opencode-tools 为单文件(6×3 适配表 + Codex 调度铁律 + XML wrapping 模板 + OpenCode 差异 + 调试 tips)
- **G § 5a/5b/5c (L0)** — YAML frontmatter entry example + 信息密度对照 + 自检 prompt
- **借口反驳表 inline 到 L0/L1** — Mode B 防御零延迟(#1/#2/#4/#5 在 L0; #3 在 L1 § 4)
- **`docs/adr/`** — ADR-001 (opt-in via cadence-init) + ADR-002 (L0 inline happy path)

### Changed
- **`cadence-init/SKILL.md`**: 230 → 125 行 (-46%) — 删 Step 1a.4 / 补全模式 / 已废弃第 4 步; v0.2.x 迁移 inline
- **`cadence-bootstrap/SKILL.md` (L0)**: 104 → 161 行 — inline 借口反驳表 4 项 + G § 5a/5b/5c
- **`recording-protocol.md` (L2)**: 368 → 467 行 — §8 incidents 附录(合并 incident-handling.md)+ §2 dual schema 说明
- **`query-behavior.md` (L2)**: 248 → 322 行 — §11 文档可信度 L1-L4(合并 doc-reliability-protocol.md)

### Removed
- `cadence-init/scaffolds/_CONVENTIONS.md` (455 行) — bootstrap 注入承担其作用
- `cadence-init/agents/scaffold-upgrader.md` (123 行) — 迁移逻辑 inline 到主 skill
- `project-discuss/references/incident-handling.md` (合并到 `recording-protocol.md` § 8)
- `project-discuss/references/doc-reliability-protocol.md` (合并到 `query-behavior.md` § 11)
- `project-discuss/references/codex-tools.md` (合并到 `harness-adapters.md`)
- `project-discuss/references/opencode-tools.md` (合并到 `harness-adapters.md`)

### Migration notes
- 从 v0.3.x 升级: `/plugin marketplace update cadence` + `/plugin update cadence@cadence` + `/clear`,无需额外操作
- 协议三层化对用户透明 — happy path 完全 backward compatible
- 旧 streaming entry (markdown 段落格式) 仍合法,新 entry 推荐 YAML frontmatter

净削减约 908 行(505+ / 1413-) 跨 17 文件。72 pytest 全部通过。

---

## [0.4.0] - 2026-05-21

正式承认 cadence 协议 v0.4 milestone,**消除 plugin SemVer 与 `recording-protocol.md` 内部协议号自 v0.3.0 起累积的双轨错位**(此前 SKILL.md / agents 跨 5 文件 29 处提及 "v0.4 状态机 / 三阶段 / 单判据",但 CHANGELOG 无 [0.4.0]、git tag 只到 v0.3.1)。

本次 minor bump 不引入新功能——而是**追认 v0.4 协议在 v0.3.x 期间已落地的语义升级**。plugin 包号与 protocol version 自此对齐:协议语义变化触发包号 minor 或 major bump,文档微调走 patch。

### Changed
- **plugin SemVer 0.3.2 → 0.4.0**:同步 `package.json` / `.claude-plugin/plugin.json` / `.codex-plugin/plugin.json` / `.claude-plugin/marketplace.json`(version + ref)。

### Protocol v0.3 → v0.4 milestone(已落地)

下列协议变化在 v0.3.0 / v0.3.1 / v0.3.2 期间陆续合入,本次统一承认为 milestone:

- **三阶段直白命名** α/ε/ρ → 记 / 整 / 查
- **承接对象扩展**:用户对中间决定的承接("嗯,先排除 C")纳入判据
- **状态机引入**:`accepted` / `implemented` / `stale` / `superseded`(决策);`pending` / `done`(TODO);`open` / `resolved`(待决);`validate_consolidator_plan.py` `DECISION_STATUSES` 等已实现
- **Phase 化骨架**:`project-discuss/SKILL.md` 从散装 13 节重构为 8 节
- **强 schema 降建议**:`consolidator_plan` 中 `decision_id` / `source_streaming_file` / `body` 等从必填降建议,`status` 仍必填
- **借口反驳表**:`project-discuss/SKILL.md` § 6 新增
- **段独立 70/100 阈值 trigger**:`_ACTIVE.md` 各段独立条数上限 + 70% 软警告 / 100% 硬阈值
- **undo_hint warning(v0.4 双 API)**:`validate_plan_with_warnings()` 收集软警告
- **handoff content_hashes(v0.3 起)**:handoff 改为书签 + sha1 校验,resume 时检测 _INDEX / _ACTIVE 漂移
- **Step 6 archive cleanup**:`cadence-resume` 归档旧 handoff(B1 修复)

### TBD(下个 patch 完成)

- **Task B5:VALID_TRIGGERS 集合扩展**:`recording-protocol.md` 已列 `section_70` / `section_100` / `cold_n_rounds` / `mtime_change` 4 类 v0.4 新 trigger,但 `validate_consolidator_plan.py` 仍是 v0.3 集合 `{llm_initiated, handoff_sweep}`,会拒绝 lifecycle plan。fixture `tests/schema/fixtures/consolidator_plan_lifecycle_archive.yaml` 顶部注释已记录此 gap。计划在 0.4.1 扩展 VALID_TRIGGERS 集合 + 允许 lifecycle trigger 下 `target_streaming_file` / `target_topic_slug` / `streaming_file_updates` 为 null。

### Migration

无破坏性变化。已安装 0.3.x 的用户卸载重装即可(marketplace ref 已更新到 v0.4.0)。protocol 层在 v0.3.x 期间已实质生效,既有 streaming / discussions / handoff 文件继续合法。

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
