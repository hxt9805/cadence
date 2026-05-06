# 文档可信度协议

> 帮助 Claude 在回答查询时正确处理不同来源的信息。本文件是 skill 的内部行为细则。

## 信息分级

| 级别 | 来源 | 可信度 | 举例 |
|---|---|---|---|
| **L1** | 代码、配置文件、package manifest | 最高（事实） | package.json、.env.example、src/ 代码 |
| **L2** | cadence 自动扫描生成 | 高（扫描时刻事实） | cadence/discussions/00-project-snapshot.md 标注 [来源：xxx] 的字段 |
| **L3** | cadence 讨论记录 | 高（决策意图） | cadence/discussions/05-tech/database.md |
| **L4** | 项目内手写文档 | 低（可能过时） | README.md、docs/architecture.md、docs/api.md |

## 查询行为规则

### 事实性问题（"用什么 X"）

- **L1 > L2，不盲信 L4**
- 如果档案来源是 L4（例如某字段标注"[来源：README.md]"），读一眼代码复核
- 答复时可以声明"根据代码"（不需要每次说"L1"这种内部术语）

### 意图性问题（"为什么选 X"）

- **L3 > L4**
- 当前代码可能已偏离初衷，答复时声明"这是当时的意图，具体实现可能已调整"

### 冲突时

- 提示用户选择以哪边为准
- 默认倾向以 L1（代码）为准更新 L3/L4

## 标注可信度

### cadence 自动扫描生成的档案

每个事实字段**必须**标注来源：

```markdown
## 技术栈
- 前端：React ^18.2.0  [来源：package.json]
- 后端：Express ^4.18  [来源：package.json]
```

来源来自 L4 时要加警示：

```markdown
## 设计意图（来源：docs/architecture.md，2024-06 撰写）
⚠️ 以下内容来自手写文档，可能与当前代码不一致，查询时请验证
- ...
```

### 不标来源的情况

- 纯从对话中产生的决策（L3）不需要每条标来源
- 但整个文档的顶部可以加日期（"本文于 YYYY-MM-DD 记录"）

## 实际举例

**用户问**："后端用的什么框架？"

**Claude 流程**：

1. 读 `cadence/_INDEX.md`，看「项目简述」或「话题词典」
2. 找到「后端：Express ^4.18 [来源：package.json]」→ L1 来源 → 直接答
3. 如果只在 `_INDEX.md` 里看到 L4 来源（如 "根据 README 说是 Express"），读 package.json 复核
4. 复核一致 → 直接答 "Express ^4.18"
5. 复核不一致 → 提示用户选择

**用户问**："为什么选 Express 而不是 Fastify？"

**Claude 流程**：

1. 读 `cadence/discussions/05-tech/backend-framework.md`（如果存在）
2. 找到理由，声明"这是当时的决策意图"
3. 档案里没有 → 查 `_INDEX-HISTORY.md` 或 `_archive/`
4. 还没有 → 说"没有记录具体理由，可能是直接用了默认选择。要现在讨论一下吗？"
