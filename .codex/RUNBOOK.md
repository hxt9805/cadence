# cadence on Codex CLI — Acceptance Test Runbook

> 配套 [`INSTALL.md`](./INSTALL.md)。装完后跑下面 **4 个测试**，确认 cadence 在 Codex 上正常工作。
> 任何一项失败 → 暴露具体障碍，可在 issue 中反馈。

## 前提清单

- [ ] Codex CLI v0.117.0+ 已装
- [ ] `~/.agents/skills/cadence` symlink 指向 `~/.codex/cadence/skills`（按 INSTALL.md 步骤完成）
- [ ] `~/.codex/config.toml` 已设 `[features].multi_agent = true`
- [ ] Codex CLI 已重启

---

## 测试 1：Skill 元数据自动注入

**步骤**：
1. 在任意目录跑 `codex` 启动新 session
2. 输入 `/skills` 列出已注册 skills

**期望**：输出列表中能看到至少这 5 个：
- `cadence-bootstrap`
- `project-discuss`
- `cadence-init`
- `cadence-handoff`
- `cadence-resume`

**失败信号**：
- 完全看不到任何 cadence skill → symlink 没生效 → 跑 `ls ~/.agents/skills/cadence` 检查
- 只看到部分 skill → 某个 SKILL.md frontmatter 不合 Codex schema → 贴 stderr 报错

---

## 测试 2：Skill 自动触发（progressive disclosure）

**步骤**：
1. 在 cadence 仓库目录（或任意装了 cadence 的项目目录）跑 `codex`
2. 用自然语言对 LLM 说：

   > 我想在这个项目里开始一段讨论，按 cadence 协议来。

**期望**：LLM **主动加载** `cadence-bootstrap` skill 全文（不需要你 `$cadence-bootstrap` 显式调），并在回复中引用 cadence 协议术语（"记/整/查"、"已被承接"、"_ACTIVE.md" 等）。

**失败信号**：
- LLM 不知道 cadence 是啥 / 没引用任何术语 → cadence-bootstrap 的 description 触发词不够强 → 回主 session 讨论调强 description
- LLM 知道 cadence 但加载不出 body → SKILL.md body 格式问题 → 贴 LLM 的回复

---

## 测试 3：`$cadence-init` 触发跑通

**步骤**：
1. 找一个**全新空目录**（如 `mkdir /tmp/cadence-test && cd /tmp/cadence-test`）
2. 跑 `codex`
3. 输入 `$cadence-init`

**期望**：
- LLM 启动 `cadence-init` skill 主流程
- 在当前目录建出至少这 3 个文件：
  - `cadence/_INDEX.md`
  - `cadence/_ACTIVE.md`
  - `cadence/_CONVENTIONS.md`
- 不报错、不卡住

**失败信号**：
- `$cadence-init` 不被识别 → Codex 的 `$skillname` 语法跟我们假设不一致 → 贴 Codex 完整输出
- skill 被识别但跑到一半要求 CC 特有工具或路径（如解析 `${CLAUDE_PLUGIN_ROOT}` 失败）→ skill body 里有 CC 残留 → 列出报错的具体文件路径行号

---

## 测试 4：Subagent spawn 跑通（**最关键**）

这一项检验 cadence 的"暗仓库" UX 在 Codex 上是否成立。

**步骤**：
1. 接续测试 3 的目录（已有 `cadence/` 骨架）
2. 手动写一段假的 streaming entry：

   ```bash
   mkdir -p cadence/streaming
   cat > cadence/streaming/2026-05-06-test.md << 'EOF'
   ---
   topic: cache-test
   created_at: 2026-05-06
   status: active
   ---

   # Cache test

   ## ^entry-001 (2026-05-06)
   决定用 Redis 做 cache，因为也要做 rate limiting，Memcached 不支持。
   EOF
   ```

3. 在 `codex` session 里跟 LLM 说：

   > 上次 cache 我们最后决定怎么搞的来着？

**期望**：
- 主 session LLM 识别这是历史检索 query
- LLM 调用 `spawn_agent(explorer, message=<XML wrapped recall-retriever prompt>)`
- subagent 跑完返回 ≤500 tokens 的 summary + pointers
- 主 session 给出最终答案 "用 Redis（pointer: streaming/2026-05-06-test.md#entry-001）"，并显式提到调过 retriever subagent

**失败信号**：
- LLM 不 spawn subagent，直接读文件 → Codex session policy 太保守 / 触发词不够强 → 回 codex-tools.md § 2 加强 spawn 强祈使句
- spawn 报错 `multi_agent` 不可用 → 回前提清单检查 `~/.codex/config.toml`
- subagent 跑通但回流 token 数远超 500 → 暴露 Codex 的 consolidated output 行为，要重新设计 retriever 输出契约

---

## 反馈格式

跑完 4 个测试后，把结果按这个模板贴回主 session：

```markdown
### 测试 1: PASS / FAIL
- 实际看到的 skill 列表: ...
- 失败 stderr (if any): ...

### 测试 2: PASS / FAIL
- LLM 回复摘要: ...
- 是否引用 cadence 术语: ...

### 测试 3: PASS / FAIL
- 实际生成的文件清单: ...
- 失败时 LLM 输出: ...

### 测试 4: PASS / FAIL
- 是否调用 spawn_agent: 是 / 否
- subagent 输出 token 数估计: ...
- 主 session 最终答案: ...
```
