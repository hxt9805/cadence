# 项目扫描策略

> 本文件供 project-scanner subagent 参考。定义扫描范围、产物模板、一致性检测规则。

## 扫描内容来源

| 文件/目录 | 提取信息 |
|---|---|
| `README.md` / `README.zh.md` / `README.*.md` | 项目定位摘要 |
| `package.json` | JS/TS 依赖、技术栈 |
| `pyproject.toml` / `requirements.txt` / `setup.py` | Python 依赖 |
| `Cargo.toml` | Rust 依赖 |
| `go.mod` | Go 依赖 |
| `pom.xml` / `build.gradle` | Java 依赖 |
| `src/` `app/` `lib/` 等顶层目录 | 架构划分推断 |
| `.env.example` / `config/` / `settings.py` | 配置和外部依赖 |
| `docs/` 已有文档（首层） | 历史产出摘要 |
| `docker-compose.yml` / `Dockerfile` | 服务依赖（数据库、缓存等） |
| `git log --oneline \| head -50` | 近期活跃区域 |

## 项目快照模板

输出到 `cadence/discussions/00-project-snapshot.md`：

```markdown
# 项目现状快照（YYYY-MM-DD 扫描生成）

> ⚠️ 这是 cadence 自动生成的初版档案，可能有错漏。
> 请阅读后手动修正。标 [TBD] 的部分需要你补充。

## 规模概览
- 主要语言：...
- 文件数：~N 个（不含 node_modules 等）

## 一句话定位
[从 README 摘要，找不到则 [TBD]]

## 技术栈
- 前端：...  [来源：package.json]
- 后端：...  [来源：package.json]
- 数据库：...  [来源：docker-compose.yml]
- 关键依赖：...

## 主要目录结构
[扫描顶层，列 2 层]

## 关键模块推断
[基于目录名和文件内容，标注"推断"]

## 识别到的配置 / 外部依赖
[.env.example、config/]

## 已有文档摘要
- docs/xxx.md: 简要摘要
- ...

## 设计意图（来源：docs/architecture.md，YYYY-MM 撰写）
⚠️ 以下内容来自手写文档，可能与当前代码不一致，查询时请验证
- ...

## 最近 3 个月活跃的模块
[基于 git log 热度]

## 未知 / 待补充
- 项目目标和目标用户：[TBD]
- 核心业务逻辑：[TBD]
- 已知技术债：[TBD]
- 历史关键决策：[TBD]
```

## 一致性检测规则

对比 README / docs 中的声明和代码实际状态，分**二级**：

- **🔴 关键**：会让 Claude 给出错误事实性回答
  - 技术栈/主要依赖版本不匹配
  - 核心模块存在与否描述错误
  - 主要服务依赖描述错误
- **⚪ 其他**：其他所有不一致
  - 架构描述细节不符
  - 次要功能未更新文档
  - 示例代码过时

## 不一致清单模板

输出到 `cadence/discussions/01-inconsistencies.md`：

```markdown
# 文档-代码不一致清单

> cadence 扫描时识别。使用 `[ ]` 复选框标记处理状态。

## 🔴 关键（待处理 N / 已处理 M）

- [ ] **技术栈版本不一致：React**
  - 说法 A（README.md L12）：React 18
  - 说法 B（package.json）：^16.8.0
  - 建议：以 package.json 为准，更新 README

- [ ] ...

## ⚪ 其他（待处理 N / 已处理 M，默认折叠）

<details>
<summary>展开查看</summary>

- [ ] ...

</details>

## ✓ 已处理 / 已忽略

（每次用户标记完成时移动到这里）
```

## 硬上限

- 不一致总条数：30 条。超出则截断，在清单末尾写：
  "⚠️ 另有 N 条中低优先级不一致未详细列出。修完现有再扫可查看。"

## 关键决策

- **代码是事实，文档是意图**。扫描出的技术栈/依赖以代码为准。
- **从不自动修改项目源代码或已有文档**。只生成 cadence/ 下的档案。
- **每个事实字段要标注 [来源：xxx]**，让用户/Claude 判断可信度。
