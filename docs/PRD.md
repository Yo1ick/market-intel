# Stock Assistant PRD - Multi-Agent 投研助手

**版本**: v1.0
**日期**: 2026-04-19
**作者**: 陈啸扬
**状态**: 草案 / 待评审

---

## 1. 背景与目标

### 1.1 为什么做

已完成 Phase 1-3 的 RAG 对话系统(ChromaDB + qwen + 意图路由),但存在三个局限:

1. **单 Agent 结构** → 只能"问一答一",无法主动监控盘中异动、无法定时产出复盘
2. **无记忆系统** → 每次对话独立,无法记住用户持仓、偏好、历史判断
3. **工具碎片化** → akshare 数据、研报 RAG、新闻检索彼此孤立,无法组合调用

### 1.2 目标

从零设计一套 **Multi-Agent 投研系统**,**刻意不使用 LangGraph / AutoGen / CrewAI 等上层框架**,手搓核心调度、记忆、上下文管理,目标:

- **求职**:对标 Accio LLM 应用开发工程师 JD,覆盖 Multi-Agent / 记忆系统 / 上下文工程 / RAG / Function Calling 全部关键词
- **长期**:成为个人实盘投研底层基础设施,后续策略层在其上演进

### 1.3 非目标(明确不做)

- ❌ 实盘下单(只做分析和建议,不做执行)
- ❌ 高频交易场景(分钟级以下)
- ❌ 多用户 / 权限系统(单机单用户)
- ❌ 框架层开源策略层代码(策略私有)

---

## 2. 用户画像与核心场景

### 2.1 用户画像

**主用户**:个人散户 / 兼职投研者
- 白天工作,无法全程盯盘
- 关注少数股票(<50 只)
- 希望 AI 协助"时间外沉淀 + 时间内提醒"
- 有一定编程能力,接受需自行配置 API Key

### 2.2 核心场景

| 场景 | 触发方式 | 期望结果 |
|---|---|---|
| **盘中异动提醒** | 交易时段自动 | 自选股涨跌幅超阈值 / 放量 / 涨跌停时推送 |
| **收盘复盘** | 每日 15:30 自动 | 生成当日持仓表现 + 市场总结 + 明日重点 |
| **主动问答** | 用户对话 | "宁德时代今天为什么涨?"→ 综合行情+研报+新闻回答 |
| **策略筛选** | 用户请求 | "帮我找 PE<20 且近期放量的创业板"→ 返回候选股 |
| **偏好记忆** | 自然产生 | "我之前说不看新能源",下次推荐自动过滤 |

---

## 3. 功能需求(FR)

### 3.1 Agent 清单

| Agent | 职责 | 触发 | 输出 |
|---|---|---|---|
| **总控 Agent** | 用户对话入口,意图识别,调度其他 Agent,聚合结果 | 用户输入 | 自然语言回复 |
| **盯盘 Agent** | 监控自选股实时行情,识别异动 | APScheduler 交易时段 30s 轮询 | 事件写入 Event Log |
| **复盘 Agent** | 生成当日持仓 + 市场复盘报告 | 每日 15:30 | Markdown 报告写入 SQLite |
| **选股 Agent** | 按策略筛选股票(基本面/技术面/题材) | 总控调度 | 候选股 JSON 列表 |
| **情报 Agent** | 研报/新闻/公告 RAG 检索 | 总控调度 | 相关文档片段 + 摘要 |

### 3.2 记忆系统(4 层)

| 层级 | 存储 | 内容示例 | 更新策略 |
|---|---|---|---|
| **Working** | in-context messages | 当前会话消息 | 满窗 LLM 压缩 |
| **Episodic** | SQLite + ChromaDB 向量索引 | "上周三用户说看空新能源" | 追加 + 时效衰减 |
| **Semantic** | SQLite 结构化表 | 持仓表、自选股表、偏好表 | CRUD |
| **Procedural** | JSON 规则文件 | "PE>50 自动过滤"、"不推荐军工" | 用户显式编辑 |

**统一接口**:
```python
memory.write(type: str, content: str, metadata: dict) -> id
memory.recall(query: str, types: list, k: int, filters: dict) -> list[Memory]
memory.compress(threshold_tokens: int) -> None
```

### 3.3 共享状态层(Blackboard)

- **Event Log**(SQLite 表):盯盘 / 复盘 Agent 写入,总控 Agent 按需读取
- **Semantic Memory**(SQLite 表):持仓 / 自选股 / 偏好,所有 Agent 可读,总控可写
- **Knowledge Base**(ChromaDB):研报 / 新闻向量库,情报 Agent 主写主读

**关键规则**:Agent 间**不直接通信**,全部通过黑板读写。

### 3.4 Tool 清单(Function Calling)

**行情类**(akshare 封装):
- `get_realtime_quote(symbol)` — 实时行情
- `get_kline(symbol, period, start, end)` — K 线
- `get_financial_report(symbol, report_type)` — 财报
- `get_industry_list()` — 行业列表

**分析类**:
- `calc_technical_indicators(symbol, indicators)` — 技术指标
- `screen_stocks(conditions)` — 条件选股

**知识类**:
- `rag_search(query, top_k, filters)` — 研报/新闻 RAG 检索
- `get_news(symbol, limit)` — 最新新闻

**记忆类**:
- `memory_recall(query, types, k)` — 召回记忆
- `memory_write(type, content)` — 写入记忆

---

## 4. 非功能需求(NFR)

| 指标 | 目标 | 理由 |
|---|---|---|
| 对话响应延迟 | P95 < 5s | 交互可接受范围 |
| 单次对话成本 | < ¥0.10 | 个人使用可持续 |
| 盯盘轮询间隔 | 30s | akshare 频率限制 + 异动可接受延迟 |
| Agent 循环保护 | 单对话最多 5 轮 Tool 调用 | 防止死循环烧 token |
| 单元测试覆盖率 | ≥ 70%(核心模块 ≥ 85%) | 基础质量保障 |
| 上下文窗口管理 | 超 50% 触发压缩 | 防止爆炸 |

---

## 5. 技术架构

### 5.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户(Streamlit UI)                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │   总控 Agent      │ ← 单线程,唯一持有对话记忆
                   │  (Orchestrator)   │
                   └─────────┬─────────┘
                             │
          ┌──────────────┬───┴───┬──────────────┐
          │              │       │              │
     ┌────▼────┐   ┌────▼────┐  ┌▼─────┐   ┌───▼────┐
     │ 盯盘     │   │ 复盘     │  │选股  │   │ 情报    │
     │(daemon) │   │ (cron)  │  │(tool)│   │ (tool) │
     └────┬────┘   └────┬────┘  └──┬───┘   └────┬───┘
          │             │           │            │
          └─────────────┴───────────┴────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │       共享状态层(Blackboard)        │
          │  ┌──────────┐ ┌─────────┐ ┌──────┐ │
          │  │EventLog  │ │Semantic │ │ RAG  │ │
          │  │ (SQLite) │ │ (SQLite)│ │(ChromaDB)│
          │  └──────────┘ └─────────┘ └──────┘ │
          └─────────────────────────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │         Tool 层(Function Calling)   │
          │  行情 akshare / 分析 / RAG / 记忆    │
          └─────────────────────────────────────┘
```

### 5.2 关键技术决策

| 决策 | 选择 | 理由 |
|---|---|---|
| Agent 通信方式 | 共享状态层(黑板) | 避免自然语言 handoff 导致上下文爆炸 |
| 总控模式 | 单线程 Orchestrator | 叙事连贯,易 debug,参考 Anthropic Research Agent |
| 子 Agent 返回格式 | 结构化 JSON | 总控按需展开,节省上下文 |
| LLM 框架 | OpenAI SDK 原生 | 不用 LangChain 以免失去原理理解 |
| Agent 框架 | **手搓**(不用 LangGraph/AutoGen/CrewAI) | 对齐 JD "精通原理和调优" |
| 向量库 | ChromaDB | Phase 2/3 已有,无切换成本 |
| 结构化存储 | SQLite | 单机零运维,WAL 支持并发读 |
| 定时任务 | APScheduler | 轻量,足够覆盖盯盘/复盘 |
| Web UI | Streamlit | 快速原型,足够演示 |
| LLM Provider | qwen-plus(主) + qwen-turbo(成本敏感场景) | 成本可控 + 中文强 |

### 5.3 LLM Provider 抽象

```python
class LLMProvider(Protocol):
    def chat(messages: list, tools: list = None, **kwargs) -> Response
    def embed(texts: list[str]) -> list[list[float]]
```

预留接口,后续可切换到本地 MLX / ollama 不改上层代码。

### 5.4 上下文工程策略

**防爆炸五条**:
1. 子 Agent 返回结构化 JSON,不返回自然语言长文
2. 子 Agent 不持有对话历史,每次 fresh context
3. Event Log 用 id 引用,总控按需检索具体事件
4. Working Memory 超 50% 窗口触发 LLM 总结压缩
5. Tool 结果超 2000 token 自动截断 + 保留 id 供追溯

---

## 6. 数据模型

### 6.1 SQLite 表结构

```sql
-- 事件日志(盯盘/复盘写入)
CREATE TABLE event_log (
    id INTEGER PRIMARY KEY,
    event_type TEXT NOT NULL,  -- 'price_alert' | 'volume_surge' | 'limit' | 'review'
    symbol TEXT,
    payload JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME
);

-- 持仓
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    shares INTEGER NOT NULL,
    cost_price REAL NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    note TEXT
);

-- 自选股(观察不持仓)
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    reason TEXT,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 用户偏好(Semantic Memory)
CREATE TABLE preferences (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Episodic 记忆(向量化由 ChromaDB 管,这里存原文+引用)
CREATE TABLE episodic_memory (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    importance REAL DEFAULT 0.5
);

-- 对话会话
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active DATETIME,
    message_count INTEGER DEFAULT 0
);

-- 消息(会话内 Working Memory 持久化)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    role TEXT NOT NULL,  -- 'user' | 'assistant' | 'tool' | 'system'
    content TEXT,
    tool_calls JSON,
    tool_call_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 复盘报告
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    review_date DATE UNIQUE NOT NULL,
    content_md TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 ChromaDB Collection

- `knowledge_base`:研报 / 新闻向量(已有,Phase 2/3 沿用)
- `episodic_index`:对话事件向量索引(新增)

---

## 7. 目录结构(Public / Private 分离)

### 7.1 Public 仓库 `stock-assistant`(开源)

```
stock-assistant/
├── src/
│   ├── agents/                    # Multi-Agent 核心
│   │   ├── base.py                #   Agent 抽象基类
│   │   ├── orchestrator.py        #   总控 Agent
│   │   ├── watcher.py             #   盯盘 Agent
│   │   ├── reviewer.py            #   复盘 Agent
│   │   ├── screener.py            #   选股 Agent(接口 + 示例均线)
│   │   └── intel.py               #   情报 Agent
│   ├── memory/                    # 记忆系统
│   │   ├── manager.py             #   统一接口 write/recall/compress
│   │   ├── working.py             #   会话内窗口管理
│   │   ├── episodic.py            #   事件记忆(SQLite+向量)
│   │   ├── semantic.py            #   结构化记忆
│   │   └── procedural.py          #   规则引擎
│   ├── rag/                       # 现有,升级为情报 Agent 的检索层
│   │   ├── embedder.py
│   │   ├── loader.py
│   │   ├── retriever.py
│   │   └── store.py
│   ├── tools/                     # Function Calling 工具
│   │   ├── registry.py            #   工具注册表
│   │   ├── schema.py              #   schema 生成器
│   │   ├── market.py              #   行情类工具
│   │   ├── analysis.py            #   分析类工具
│   │   └── knowledge.py           #   知识类工具
│   ├── llm/                       # LLM Provider 抽象
│   │   ├── provider.py            #   Protocol
│   │   ├── qwen.py                #   qwen 实现
│   │   └── cache.py               #   语义缓存
│   ├── data/                      # 数据源封装(现有)
│   │   └── fetcher.py
│   ├── blackboard/                # 共享状态层
│   │   ├── event_log.py
│   │   └── store.py               #   SQLite 封装
│   ├── scheduler/                 # 定时任务
│   │   └── jobs.py
│   ├── chat/                      # 对话层(现有,重构)
│   │   └── chat.py
│   └── ui/                        # Streamlit UI
│       └── app.py
├── examples/                      # 演示用策略(可开源)
│   └── strategy_ma_demo.py        #   简单均线策略,示例接口
├── tests/
│   ├── agents/
│   ├── memory/
│   ├── tools/
│   └── integration/
├── docs/
│   ├── PRD.md                     # 本文档
│   ├── ARCHITECTURE.md            # 架构详解
│   ├── PITFALLS.md                # 踩坑记录(Phase 2/3 整理)
│   └── API.md                     # 工具 schema 清单
├── data/
│   └── docs/                      # 研报存放(gitignore)
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── main.py
```

### 7.2 Private 仓库 `stock-strategies`(私有)

```
stock-strategies/                  # 独立 repo,不公开
├── strategies/
│   ├── factors/                   # 私有因子
│   │   ├── momentum_v3.py
│   │   └── value_custom.py
│   └── live/                      # 实盘策略组合
│       └── my_config.json
├── backtest/
│   └── results/                   # 历史回测结果
├── trading_log/                   # 实盘记录
└── config/
    └── live.json                  # 真实 API key / 参数
```

通过 `pyproject.toml` 将 `stock-strategies` 声明为可选依赖,public 仓库不依赖但可加载。

### 7.3 .gitignore(Public 仓库)

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.pytest_cache/

# IDE
.idea/
.vscode/

# Env & secrets
.env
.env.local
config/live.json
*.secret.json

# Data
data/docs/                         # 研报原文
data/chroma/                       # 向量库
data/trading_log/
*.db
*.sqlite

# Private strategies (即使误放在 public 也拦住)
strategies/live/
strategies/factors/my_*.py
backtest/results/

# Outputs
logs/
reviews/*.md
!reviews/example_*.md              # 示例保留

# OS
.DS_Store
Thumbs.db
```

---

## 8. Phase 拆分

### 当前状态(Phase 1-3 已完成)
- ✅ Phase 1:RAG 基础(ChromaDB + embedding + chunking)
- ✅ Phase 2:RAG 完整链路踩坑并修复(16 个坑记录)
- ✅ Phase 3:Chat + RAG 联调 + 意图路由(9 个坑记录)

### Phase 4:Agent 框架骨架(Week 1,本期 MVP 最小集)

**目标**:可跑通"用户问 → 总控 → 单个情报 Agent → 返回"的最小闭环。

**交付**:
- `src/agents/base.py` — Agent 抽象基类(LLM 调用 + Tool 执行)
- `src/agents/orchestrator.py` — 总控基础框架
- `src/agents/intel.py` — 情报 Agent(包装现有 RAG)
- `src/tools/registry.py` + `schema.py` — 工具注册与 schema 生成
- `src/blackboard/store.py` — SQLite 封装(基础表)
- `src/memory/working.py` — 会话内窗口管理
- `src/memory/manager.py` — 接口定义(其他层桩实现)
- `tests/` — 单元测试 ≥ 70%

**验收**:
- [ ] 用户 CLI 输入 "第一类买点是什么" → 总控调用情报 Agent → 返回结果
- [ ] 对话超过窗口自动压缩
- [ ] 单元测试跑通

### Phase 5:选股 Agent + Semantic Memory(Week 2)

**交付**:
- `src/agents/screener.py` — 选股 Agent(先实现简单条件筛选)
- `src/memory/semantic.py` — 持仓/自选股/偏好 CRUD
- `src/tools/market.py` — akshare 工具封装(realtime/kline/fundamental)
- `src/tools/analysis.py` — 技术指标计算(MA/MACD/RSI)
- `examples/strategy_ma_demo.py` — 演示策略

**验收**:
- [ ] "帮我找 PE<20 的银行股"→ 选股 Agent 返回 5 只
- [ ] "我持有宁德时代 100 股成本 200" → 写入 positions 表
- [ ] "我的持仓"→ 读 positions 表返回

### Phase 6:盯盘 + 复盘 Agent(Week 3)

**交付**:
- `src/agents/watcher.py` — 盯盘 Agent
- `src/agents/reviewer.py` — 复盘 Agent
- `src/scheduler/jobs.py` — APScheduler 配置
- `src/blackboard/event_log.py` — 事件日志读写
- `src/memory/procedural.py` — 规则引擎(阈值配置)

**验收**:
- [ ] 盯盘在交易时段轮询,异动写入 Event Log
- [ ] 15:30 自动生成复盘报告,落盘到 reviews 表
- [ ] 总控能读 Event Log 回答"今天有什么异动"

### Phase 7:总控增强 + Episodic Memory(Week 4)

**交付**:
- `src/agents/orchestrator.py` 升级:意图路由、多 Agent 聚合、循环保护
- `src/memory/episodic.py` — 事件记忆(SQLite + ChromaDB 向量索引)
- `src/llm/cache.py` — 语义缓存(从之前的缓存项目复用思路)

**验收**:
- [ ] 多轮对话记忆连贯("你刚说的那只股"能解析)
- [ ] 相似问题命中语义缓存,无需走 LLM
- [ ] 循环保护:单对话超 5 轮 Tool 调用自动中止

### Phase 8:Streamlit UI + 打磨(Week 5)

**交付**:
- `src/ui/app.py` — 对话界面 + 持仓面板 + 复盘查看
- Docker 容器化
- `README.md` 完整化(含架构图、快速开始、面试亮点)
- `docs/ARCHITECTURE.md` + `docs/PITFALLS.md`

**验收**:
- [ ] 本机 `docker-compose up` 一键启动
- [ ] GitHub Public 仓库可展示
- [ ] 简历可投

### Phase 9+:策略层(私有仓库,不计入本 PRD 范围)

在 public 框架之上,自建 `stock-strategies` 私有仓库,填入真实因子、参数、实盘配置。

---

## 9. 验收标准(整体)

**必须**:
1. 所有 Phase 4-8 的 checklist 通过
2. 核心模块单元测试覆盖率 ≥ 85%
3. 端到端演示:一次完整对话(问答+记忆召回+工具调用+聚合)
4. 文档完整(README + PRD + ARCHITECTURE + PITFALLS)
5. Public 仓库在 GitHub 可访问,License 明确

**应该**:
- 代码无 TODO/FIXME 遗留
- Pitfalls 文档包含 Phase 4-8 新踩的坑(作为 Phase 2/3 的延续)
- 有 1-2 篇技术博客(Multi-Agent 架构 + 记忆系统)草稿

---

## 10. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|---|---|---|---|
| Agent 死循环烧 token | 中 | 高 | 循环保护 + token 预算 + 异常熔断 |
| 上下文爆炸 | 中 | 高 | 5 条防爆炸策略(见 5.4) |
| 手搓工作量超预期 | 高 | 中 | 严格 Phase 边界,Phase 4 只求最小闭环 |
| akshare 限频/数据质量 | 中 | 中 | 本地缓存 + 失败降级 |
| qwen API 费用失控 | 低 | 中 | 语义缓存 + 成本监控日志 |
| 拖延 / 半途放弃 | 高 | 极高 | 每 Phase 有明确验收,对齐简历节奏 |

---

## 11. JD 对齐表(Accio LLM 应用开发工程师)

| JD 要求 | 本项目覆盖 | 对应模块 |
|---|---|---|
| Multi-Agent 架构设计和落地 | ✅ | `src/agents/` 全部 |
| 上下文工程优秀实践 | ✅ | 5 条防爆炸 + 结构化 JSON 返回 |
| Agent 记忆系统的设计和落地 | ✅ | `src/memory/` 四层记忆 |
| Python 精通 | ✅ | 全栈 Python |
| Agent 架构核心组件原理 | ✅ | **手搓不用框架** |
| 开源 Agent 框架了解 | ✅ | README 对比 LangGraph/AutoGen 的选型说明 |
| Prompt 调优 | ✅ | 各 Agent 的 system prompt 迭代记录 |
| Function Calling | ✅ | `src/tools/` + schema |
| RAG | ✅ | `src/rag/` + 情报 Agent |
| 上下文工程及压缩 | ✅ | Working Memory 压缩 + LLM 总结 |
| 批判性思维 | ✅ | 技术决策表 + 风险应对 |

---

## 12. 附录

### 12.1 README.md 模板(Public 仓库)

```markdown
# Stock Assistant

个人投研 Multi-Agent 助手 - 手搓版,对标 Anthropic Research Agent 架构

## 架构亮点

- 5 个专业 Agent + 单线程总控(反上下文爆炸)
- 4 层记忆系统(Working / Episodic / Semantic / Procedural)
- 共享状态层通信(Blackboard 模式)
- 手搓调度,不依赖 LangGraph / AutoGen / CrewAI

## 与其他框架的权衡

| 框架 | 优势 | 本项目选择理由 |
| --- | --- | --- |
| LangGraph | 状态图可视化 | 不用,失去原理理解 |
| AutoGen | 多 Agent 对话 | 不用,过重 |
| CrewAI | 角色化 | 不用,灵活性差 |

## 快速开始
...

## License

MIT - 框架部分。**不包含任何实盘策略/因子参数/回测结果**。
examples/ 下仅为演示用,不构成投资建议。
```

### 12.2 下一步

PRD 评审通过后,启动 **Phase 4 代码骨架生成**,交付 `src/agents/base.py` + `src/agents/orchestrator.py` + `src/agents/intel.py` 空壳,你填逻辑。

---

**文档结束**
