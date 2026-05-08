# Stock Assistant MVP PRD - 2周冲刺版

**版本**: v2 (MVP)
**目标周期**: 2 周
**完整版 PRD**: `PRD.md`(作为 Roadmap 远景,MVP 完成后逐步展开)

---

## 1. 目标与原则

### 目标

2 周内交付一个可演示、可上简历、可开源的 **Multi-Agent 投研助手 MVP**,对标 Accio LLM 应用开发工程师 JD 的**核心能力项**:Multi-Agent + Function Calling + RAG + 上下文工程。

### 3 条铁律

1. **做得完 > 做得大** — 砍到能 2 周做完的最小集
2. **核心概念完整 > 功能多** — 哪怕只有 2 个 Agent,Multi-Agent 的核心原理(单线程总控 + 结构化 JSON + 反上下文爆炸)必须讲得清
3. **所有代码自己写过** — 面试时每一行都能解释

---

## 2. 范围

### ✅ MVP 做

- **2 个 Agent**
  - 总控 Agent(Orchestrator):用户对话入口,意图识别,调度子 Agent
  - 情报 Agent(Intel):包装现有 RAG,返回结构化 JSON
- **1 层记忆**
  - Working Memory:会话窗口管理 + 超阈值 LLM 压缩
- **3 个工具**(Function Calling)
  - `rag_search(query, top_k)` — 复用现有 RAG
  - `get_realtime_quote(symbol)` — akshare 实时行情
  - `get_kline(symbol, period)` — akshare K 线
- **CLI 界面**(不做 UI)
- **单元测试** ≥ 70%
- **README + 架构图 + 踩坑记录**

### ❌ MVP 不做(进 Roadmap)

- 盯盘 Agent、复盘 Agent、选股 Agent
- Episodic / Semantic / Procedural 记忆
- 定时任务、事件日志
- Streamlit UI
- 语义缓存
- Docker 部署

---

## 3. 架构图(简化)

```
用户(CLI)
   │
   ▼
┌─────────────────────┐
│  总控 Agent          │ ← 持有 Working Memory
│  (Orchestrator)      │
│  - 意图识别           │
│  - 调度情报 Agent     │
│  - 聚合结果           │
│  - 窗口压缩           │
└────────┬────────────┘
         │ 像调函数一样调
         ▼
┌─────────────────────┐
│  情报 Agent (Intel)  │ ← 无对话记忆,每次 fresh context
│  - 查 RAG            │
│  - 返回结构化 JSON    │
└────────┬────────────┘
         │
    ┌────▼─────┐    ┌──────────────┐
    │ RAG 层   │    │  Tools 层     │
    │ (已完成)  │    │ rag_search   │
    │ ChromaDB │    │ quote / kline│
    └──────────┘    └──────────────┘
```

---

## 4. 核心设计原则(面试可讲的硬货)

### 原则 1:单线程 Orchestrator
只有总控 Agent 持有对话历史,情报 Agent 每次调用都是 fresh context。
**理由**:防止子 Agent 之间自然语言 handoff 导致上下文膨胀。

### 原则 2:结构化 JSON 返回
情报 Agent 不返回"宁德时代今天涨停,原因是..."这种自然语言,返回:
```json
{
  "docs": [
    {"id": "doc_42", "title": "...", "snippet": "...", "score": 0.87}
  ],
  "summary_key_points": ["点1", "点2"],
  "source_count": 3
}
```
**理由**:总控按需展开,token 可控。

### 原则 3:Working Memory 压缩
超过窗口 50% 触发 LLM 总结压缩旧消息,保留 system + 最近 N 条 + 总结。
**理由**:这是"上下文工程"最基础实现,面试必问。

### 原则 4:Tool 结果截断
Tool 返回超 2000 token 自动截断,保留原始引用 id。
**理由**:akshare 返回 K 线可能很长,要防爆。

### 原则 5:手搓不用框架
只用 OpenAI SDK + ChromaDB + SQLite,不用 LangGraph / AutoGen / CrewAI。
**理由**:面试要能讲清每一层原理。

---

## 5. 目录结构

```
stock-assistant/                 # Public 仓库
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # Agent 抽象基类
│   │   ├── orchestrator.py      # 总控 Agent
│   │   └── intel.py             # 情报 Agent
│   ├── memory/
│   │   ├── __init__.py
│   │   └── working.py           # Working Memory + 压缩
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py          # 工具注册表
│   │   ├── schema.py            # OpenAI function schema 生成
│   │   ├── market.py            # quote / kline
│   │   └── knowledge.py         # rag_search
│   ├── llm/
│   │   ├── __init__.py
│   │   └── provider.py          # qwen 调用封装
│   ├── rag/                     # 已有,不动
│   ├── data/                    # 已有,不动
│   └── chat/                    # 已有,后续由 Orchestrator 替代
├── tests/
│   ├── test_agents.py
│   ├── test_memory.py
│   └── test_tools.py
├── docs/
│   ├── PRD.md                   # 完整版(Roadmap)
│   ├── PRD-MVP.md               # 本文档
│   ├── ARCHITECTURE.md          # MVP 完成后写
│   └── PITFALLS.md              # 新增 Phase 4-5 踩坑
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── main.py                      # CLI 入口
```

**Private 仓库 `stock-strategies`**:MVP 阶段**不建**,Phase 9+ 做选股 Agent 时再分离。

---

## 6. Phase 拆分(2 周 = 2 个 Week)

### Week 1:Agent 框架骨架 + 情报 Agent

**Day 1-2**:
- `src/llm/provider.py` — qwen 调用封装,支持 messages + tools 参数
- `src/memory/working.py` — Working Memory 类(add / get_messages / compress)
- 单元测试

**Day 3-4**:
- `src/tools/registry.py` + `schema.py` — 工具装饰器 + schema 自动生成
- `src/tools/knowledge.py` — rag_search 工具(包装现有 retriever)
- 单元测试

**Day 5-7**:
- `src/agents/base.py` — Agent 基类(run / call_tool / handle_response)
- `src/agents/intel.py` — 情报 Agent
- `src/agents/orchestrator.py` — 总控 Agent
- `main.py` — CLI 主循环
- 端到端联调:CLI 问"第一类买点是什么"→ 总控 → 情报 Agent → 返回

**Week 1 验收**:
- [ ] CLI 输入 "第一类买点是什么" → 正确回答
- [ ] 对话超过 50% 窗口 → 自动压缩,日志可见
- [ ] 情报 Agent 返回结构化 JSON(打印可见)
- [ ] 单元测试覆盖率 ≥ 70%

### Week 2:行情工具 + 完善 + 文档

**Day 8-9**:
- `src/tools/market.py` — quote / kline 工具
- 集成到总控 Agent 的 tools 列表
- Tool 结果截断逻辑

**Day 10-11**:
- 循环保护:单对话超 5 轮 tool call 自动中止
- 错误处理:工具失败不崩溃,LLM 看到错误消息能重试
- 踩坑记录:新开 `docs/PITFALLS.md` 里的 Phase 4-5 章节

**Day 12-14**:
- `docs/ARCHITECTURE.md` — 架构详解(含图)
- `README.md` — 快速开始 + 架构亮点 + 对比 LangGraph/AutoGen 选型说明
- GitHub 公开仓库,MIT License
- 最终端到端 demo 录屏 / 截图
- 简历 v4 更新"面试可深挖技术点"列表

**Week 2 验收**:
- [ ] 混合场景对话通过:"宁德时代今天价格?然后研报里对它什么看法?"(触发 quote + rag_search)
- [ ] 5 轮工具调用上限生效
- [ ] GitHub README 展示到位
- [ ] 简历可投

---

## 7. 非功能需求(MVP 降标版)

| 指标 | MVP 目标 |
|---|---|
| 对话响应 | P95 < 8s(MVP 阶段不追求) |
| 成本 | 单次对话 < ¥0.15 |
| 单测覆盖率 | ≥ 70% |
| 文档完整度 | README + PRD + ARCHITECTURE + PITFALLS |

---

## 8. 简历映射

Week 2 完成后,简历 v4 项目一写法**保持不变**,但新增"**截止投递时已完成 MVP,Roadmap 持续迭代**"说明。

面试被问"盯盘/复盘 Agent 做了吗?":
> "MVP 已完成 Orchestrator + 情报 Agent + Working Memory + 3 个核心工具,盯盘/复盘在 Roadmap 的 Phase 6,架构已预留扩展点(Event Log + APScheduler 接口)。重点验证 Multi-Agent 调度 + 上下文管理的核心设计。"

**这个回答的价值**:
- 诚实(没做就说没做)
- 有规划(Roadmap 明确)
- 有架构思维(预留扩展点)

---

## 9. 风险

| 风险 | 应对 |
|---|---|
| 超过 2 周没做完 | 砍 Week 2 行情工具,只留 rag_search 也够演示 |
| 某天卡住 2 小时以上 | 停下来问,别硬磕 |
| 想加新功能 | **严禁** — 进 Roadmap,MVP 阶段只做清单内的 |

---

## 10. .gitignore

```
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.idea/
.vscode/
.env
.env.local
data/docs/
data/chroma/
*.db
*.sqlite
logs/
.DS_Store
```

---

**文档结束**。Week 1 Day 1 开始:先写 `src/llm/provider.py`,最基础的 qwen 调用封装。
