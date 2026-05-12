# market-intel(代号:赛博解馋)

> 基于 LLM agent + 研报知识库的极简投研问答助手。
>
> 单 agent + function calling + RAG over 真实研报数据,**全部手搓不依赖 LangChain / LlamaIndex 类框架**。

## ✨ 核心能力

- **有状态对话 + 可审计上下文**(stateful agent with auditable conversation trace)——`WorkingMemory` 持有完整消息序列,阈值触发 summarize 压缩,**严格保留 `tool_call ↔ tool_result` 配对**这一不变量(invariant)
- **Function-calling agent loop** —— `ResearchAgent` 最多 5 轮 `LLM → tool_call → tool_result → LLM`,带 rule-based guardrails(强制引用来源机构 + 日期)
- **检索增强生成 + 来源归因**(retrieval-grounded reasoning with source attribution)—— RAG 基于 akshare 真实研报数据(5 只票 × 5 篇 = 25 chunks),用 `text-embedding-v4` 入 ChromaDB 持久化
- **多模型路由 + Fallback**(multi-model routing with fallback)—— `OpenAICompatibleProvider` 兼容任何 dashscope / OpenAI-compatible 端点,模型 / base_url / api_key 全 env 可配
- **确定性评估框架**(deterministic evaluation harness)—— pytest + mock LLM,验证压缩阈值触发逻辑 + invariant 保持

## 🎬 Demo

```text
$ uv run python main.py "茅台 2026Q1 业绩怎么样?"

问题: 茅台 2026Q1 业绩怎么样?
============================================================
根据研报信息,贵州茅台(600519)2026 年第一季度业绩呈现稳健增长态势。

* 收入与利润:根据【中邮证券】(2026-04-28)的研报,公司 2026 年第一季度
  实现了收入和利润的双重稳健增长,整体表现符合市场预期。
* 核心驱动力:【华鑫证券】(2026-05-05)指出,i 茅台数字营销平台持续放量
  是公司业绩的重要增长点,改革效果初步显现。
* 经营与改革:【山西证券】(2026-04-28)的研报显示,公司的渠道重构已经落地,
  改革初现成效,为经营提供了支撑。

综合来看,贵州茅台 2026 年第一季度在收入利润、平台发展及渠道改革方面均
表现出积极信号。
============================================================
对话轮次: 10
```

## 🏗 架构

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   用户 Query                                                 │
│        │                                                     │
│        ▼                                                     │
│  ┌────────────────────┐   function calling   ┌────────────┐  │
│  │   ResearchAgent    │  ─────────────────►  │    LLM     │  │
│  │   (agent loop)     │  ◄─────────────────  │  qwen-plus │  │
│  └────────────────────┘   tool_calls         └────────────┘  │
│        │                                                     │
│        │ search_knowledge(query)                             │
│        ▼                                                     │
│  ┌────────────────────┐                                      │
│  │     Knowledge      │  ─► ChromaDB (持久化向量库)          │
│  │   (RAG retrieval)  │  ─► text-embedding-v4 (dashscope)    │
│  └────────────────────┘                                      │
│        │                                                     │
│        ▼                                                     │
│   WorkingMemory  ◄──  阈值触发 summarize 压缩                 │
│   (严格保持 tool_call ↔ tool_result 配对不变量)               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 📦 技术栈

- **Python 3.12+**,**uv** 管理依赖
- **主 LLM**:qwen-plus(默认,经 dashscope OpenAI-compatible 接口)
- **Embedding**:dashscope `text-embedding-v4`
- **向量库**:ChromaDB(本地持久化)
- **数据源**:akshare `stock_research_report_em`(东方财富实时研报)
- **测试**:pytest + ruff
- **Token 计数**:tiktoken `cl100k_base`(作为 qwen 的近似)

## 🚀 快速开始

### 1. 安装

```bash
git clone https://github.com/Yo1ick/market-intel.git
cd market-intel
uv sync
```

### 2. 配置 `.env`

项目根目录新建 `.env`:

```env
DASHSCOPE_API_KEY=你的-dashscope-key

# 可选:覆盖默认 model / endpoint(调试用其他模型时设置)
# STOCK_ASSISTANT_MODEL=qwen-plus
# STOCK_ASSISTANT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# STOCK_ASSISTANT_API_KEY=备用-key
```

### 3. 一次性 ingest 研报数据

```bash
uv run python -m scripts.ingest_research
```

期望输出:`✅ 入库完成,25 条`(5 只票 × 各 5 篇最新研报)。

### 4. 提问

```bash
uv run python main.py "茅台 2026Q1 业绩怎么样?"
uv run python main.py "招商银行最近研报评级如何?"
uv run python main.py "白酒板块和银行板块的盈利预期对比"
```

## 🧪 测试

```bash
uv run pytest tests/ -v
```

测试覆盖:

- `WorkingMemory.add_message` —— 追加正常 + role / `tool_call_id` 断言生效
- `summarize` 不触发 —— token 低于阈值,`_messages` 不变
- `summarize` 触发 —— token 超阈值时压缩,且**严格保留 `tool_call ↔ tool_result` 配对**

## 📂 项目结构

```
market-intel/
├── src/
│   ├── llm/provider.py            # LLMProvider Protocol + OpenAI-compatible 实现
│   ├── memory/working.py          # WorkingMemory: add/get/summarize + invariant
│   ├── knowledge/store.py         # Knowledge: ingest_chunks + retrieve (ChromaDB)
│   ├── rag/                       # 底层 RAG primitive (embedder / loader)
│   └── agents/
│       ├── research.py            # ResearchAgent: function-calling agent loop
│       └── tools/knowledge.py     # search_knowledge tool (schema + 实现)
├── scripts/
│   └── ingest_research.py         # 一次性 ingest 脚本:akshare → Knowledge
├── tests/
│   └── test_working.py            # 单元测试(mock LLM)
├── docs/
│   ├── PRD-MVP.md                 # 产品需求文档
│   └── ADR-001-second-agent.md    # 架构决策记录(D5:为什么先单 agent)
├── main.py                        # CLI 入口
└── pyproject.toml
```

## 🗺 Roadmap

- **Phase 0.2** —— Multi-agent orchestration(dispatcher + 专家 agent:research / news / quant)
- **Phase 0.3** —— Long-term memory(跨 session 持久化,SQLite)
- **Phase 0.4** —— PDF 全文 RAG(解析研报 PDF,而非仅元数据)
- **Phase 0.5** —— 替换 tiktoken 近似为 qwen 官方 tokenizer

为什么先做单 agent,详见 [`docs/ADR-001-second-agent.md`](docs/ADR-001-second-agent.md)。

## ⚠️ 已知局限

- **Token 计数精度**:tiktoken `cl100k_base` 对 qwen 多估 5–15%。偏保守(提前触发压缩),不会爆 context window。
- **RAG 数据规模**:仅 5 只票 × 5 篇 = 25 chunks,演示用。生产应扩展到数百只票 × PDF 全文。
- **无重试机制**:akshare 限流时失败的票直接跳过。生产应加 exponential backoff。
- **单 agent**:多 agent 编排有意推迟到 Phase 0.2(见 ADR-001 决策理由)。
- **非投资建议**:这是研报检索 / 总结工具,**输出不构成任何买卖建议**。

## 📜 License

MIT
