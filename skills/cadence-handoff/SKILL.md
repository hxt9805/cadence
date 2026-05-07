---
name: cadence-handoff
description: "整理当前 session 讨论内容到 cadence 档案(v0.4:触发整 阶段（ε 整合）兜底 + 写 sha1 书签式 snapshot,15-30 行)。用户说 'handoff'/'整理 session'/'换新 session' 或跑 /cadence-handoff 时触发。"
---

# cadence-handoff（v0.4）

## 定位(v0.3 重构)

v0.3 前 handoff 承担"决策/待决/约束/TODO/incidents"五类提取 + 9 步写链;writer subagent context 随 session 大而膨胀。

v0.3/v0.4 后记/整/查三阶段覆盖这些职责:
- 记 阶段（α 流式）记录已承载"讨论内容持久化"(五类提取不再需要)
- `recall-retriever` 查 阶段（ρ）<500 tokens 契约负责跨 session 检索(注入历史不再需要)
- 整 阶段（ε 整合）触发(含 handoff 兜底)自动收敛零散(补漏不再需要)

**新本质**:短小书签——提供"游标"(讨论到哪 / 卡在哪)和"soft context"(语气、未明说的注意事项)。体量目标 15-30 行。

## 5 步流程(主 agent 执行,不派 writer subagent)

### Step 1:扫 active streaming → 触发整 阶段（ε 整合）兜底

```
Glob cadence/streaming/*.md
  → 读每个文件 front-matter
  → 对每个 status: active 文件,检查 entry 数与时间新鲜度
  → 成熟主题 → 派 recall-consolidator subagent(trigger_reason: handoff_sweep)
  → 接收 plan → 走两阶段写(复用 project-discuss 整 阶段流程)
  → 把整合产出的 discussion doc 路径收集到 `produced[]`
```

若所有 streaming 都刚起步(entry <2 条 / 距今 <10 分钟)→ 跳过,`consolidation.triggered: false`。

**Partial success 语义**:若至少一个主题整合成功 → `consolidation.triggered: true`,`produced[]` 仅含成功项;全部失败或跳过 → `triggered: false`,`produced: []`。

### Step 2:扫对话产生 cursor + soft_context

主 agent 自己做(不派 subagent,因为新 schema 体量小,主 context 胜任):

- `cursor.last_discussed`:session 最近一段讨论话题,一句话
- `cursor.pending_questions`:未决问题,0-3 个
- `cursor.next_step`:下次接着做什么,一句话(可空)
- `soft_context.tone`:对话语气(如"紧凑" / "探索中")(可空)
- `soft_context.notes`:特殊注意事项,0-N 条(可空)

### Step 3:计算 content_hashes(I-1)

使用 `git hash-object -w --stdin` 跨平台计算(**跨平台首选**,cadence 项目已依赖 git):

```bash
INDEX_HASH=$(git hash-object cadence/_INDEX.md)
ACTIVE_HASH=$(git hash-object cadence/_ACTIVE.md)
```

**备用路径**(若 git 不可用):
- Windows(PowerShell):`(certutil -hashfile <path> SHA1 | Select-String -NotMatch "SHA1\|CertUtil").Line.Trim().Replace(" ","")` — 取哈希行,剥离空格
- Windows(cmd):`for /f "tokens=1" %%i in ('certutil -hashfile ^<path^> SHA1 ^| findstr /v ":"') do @echo %%i` — 取无冒号行第一列
- Linux:`sha1sum <path> | awk '{print $1}'` — 取前 40 字符字段
- macOS:`shasum -a 1 <path> | awk '{print $1}'` — Mac 默认无 sha1sum,用 shasum
- Python fallback:`python -c "import hashlib,sys; print(hashlib.sha1(open(sys.argv[1],'rb').read()).hexdigest())" <path>`(命令名:Windows `python` / macOS,Linux `python3`)

结果:40 字符小写 hex;不匹配 `^[0-9a-f]{40}$` → 写入前报错停止。

### Step 4:写 `.handoff/<handoff_id>.md` snapshot

按 design doc § 12.2 schema:

```yaml
---
handoff_id: <ISO 时间戳无冒号,如 20260423T180000+0800>
created_at: <ISO-8601 TZ>
topic: <一句话主题>
content_hashes:
  _INDEX.md: <sha1>
  _ACTIVE.md: <sha1>
cursor: { last_discussed, pending_questions, next_step }
soft_context: { tone, notes }
consolidation: { triggered, produced }
---

# Handoff: <topic>

## 游标
<1-3 行>

## 注意事项
<0-N 行 soft context,可空>

## 已触发整合(若 triggered=true)
streaming 中若干条已整合为 <produced[0]>,详见该 doc
```

**体量目标**:15-30 行(frontmatter + body)。超 30 行 → 压缩 cursor 为单句、soft_context.notes 限 ≤3 条。

**写入前校验**:`python ${CLAUDE_PLUGIN_ROOT}/skills/cadence-handoff/scripts/validate_handoff.py .handoff/<handoff_id>.md`(macOS / Linux 把 `python` 换成 `python3`)必须通过;不通过则停止写入 + 告知用户。

### Step 5:更新 `.handoff/index.json`

追加新 entry:`{handoff_id, created_at, topic, path}`。保持 json array 形态。

## 失败处理

- Step 1 consolidator 失败 → 日志告知,跳过未能整合的 streaming(保持 active),继续 Step 2-5
- Step 3 sha1 计算失败 → 停止,告知用户检查环境
- Step 4 schema 校验失败 → 停止,不更新 index.json
- 不引入 partial recovery(同 Phase B § 16.3)

## writer subagent(可选降级)

`agents/handoff-writer.md` 保留作为"主 agent context 意外超载"时的降级路径(如 soft_context 冗长且主 agent 拒绝裁剪)。**默认不启用**。启用条件:用户显式 `/cadence-handoff --use-writer`(可选实现,MVP 不强制)。

## 版本兼容

v0.2.2 老 handoff 文件(含 `item_counts` / 五类 entries)**不做迁移**;由 cadence-resume 识别后走 legacy 分支(`is_legacy_v22()` → mtime fallback)。
