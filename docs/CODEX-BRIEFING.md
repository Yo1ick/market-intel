# Codex 启动 Briefing — Stock Assistant (代号: 赛博解馋 / GitHub: market-intel)

**日期**: 2026-05-10
**死线**: 2026-05-20 投简历(剩 10 天 ≈ 9 晚)
**当前节点**: Day 9 进行中,summarize 已落地,准备进 knowledge.py + research agent

---

## 项目目标

构建**单 agent + tools** 的投资研究助手 demo,用于:
1. 简历项目(目标 JD: LLM Agent 工程师 / Finance AI 工程师)
2. 学习 LLM 应用工程实践

**不是**量化交易,**不是**股价预测。

---

## 简历定位 (写在 README 里的 5 个关键词,踩 JD)

- **stateful agent with auditable conversation trace** (working memory + summarize)
- **multi-model routing with fallback** (LLMProvider Protocol)
- **retrieval-grounded reasoning with source attribution** (RAG over real akshare research reports)
- **deterministic evaluation harness** (pytest with mock LLM)
- **rule-based guardrails for agent behavior** (tool_call/tool_result invariant 在 summarize 内强制)

**roadmap 里有但今天不做**: multi-agent orchestration (Phase 0.2)、long-term memory (Phase 0.3)。
理由见 `docs/ADR-001-second-agent.md`。

---

## 技术栈

- Python 3.12+ / uv 包管理
- **主 LLM**: qwen-turbo / qwen-plus 经 OpenAI 兼容接口
- **Embedding**: dashscope text-embedding-v4
- **向量库**: chromadb (PersistentClient,path="data/chroma")
- **数据源**: akshare(已在 deps,刚跑通 `ak.stock_research_report_em`)
- **测试**: pytest + ruff
- **Token 计数**: tiktoken cl100k_base(qwen 近似,README 标注)

**项目路径**: `E:\Study\project\stock-assistant\`
**GitHub**: `https://github.com/Yo1ick/market-intel` (private, main 分支)

---

## 已完成模块

```
src/
├── llm/provider.py        ✅ LLMProvider Protocol + OpenAICompatibleProvider
│                             generate(messages: list[dict], tools, temp) -> LLMResponse
├── memory/working.py      ✅ WorkingMemory: __init__(llm), add_message, get_messages, summarize
├── rag/
│   ├── embedder.py        ✅ embed_texts(list[str]) -> list[list[float]]
│   ├── loader.py          ✅ load_and_split(path) -> list[{text, source}],按 \n---\n 切
│   ├── store.py           ⚠️ collection 名是 "chanlun",要改 "research"
│   └── retriever.py       ⚠️ 同上 + 返回 chromadb 原始嵌套,要包装
tests/
└── test_working.py        ✅ 3 测 pass: add_message / summarize_no_trigger / summarize_trigger
docs/
├── PRD-MVP.md             ✅ Day 4 写
├── ADR-001-second-agent.md ✅ 今天写,锁 d → f → e 顺序
├── PITFALLS.md            ⚠️ Day 8 写,Day 9 有新增待补
└── CHANLUN-QUANT.md       ⚠️ .gitignored,本地保留不上传
```

---

## summarize() 设计要点 (Day 9 落地, 2.5h)

**位置**: `src/memory/working.py::WorkingMemory.summarize`

```python
def summarize(self, keep_recent_n=4, compress_threshold_ratio=0.5, context_window_size=32000):
```

- **Policy(会变)进参数**: keep_recent_n / compress_threshold_ratio / context_window_size
- **Invariant(破了就 bug)硬编码**:
  - tool_call ↔ tool_result 必须成对(切点处若为 role="tool" → 切点 -1)
  - system role 不入 self._messages(__init__ / Agent 层管)
- **in-place mutation**: self._messages = [summary_msg] + recent,return None
- **触发**: total_tokens >= context_window_size × ratio
- **总结生成**: self._llm.generate([{"role":"user","content":"总结..."+conv_str}]) → response.content

---

## 今日剩余任务

| # | 任务 | 估时 | 文件 |
|---|---|---|---|
| 1 | 走 akshare → 拉 5 只票 × 5 份研报 = 25 chunks 入 Chroma | 30min | `tools/data_fetcher.py` 新增 |
| 2 | `src/knowledge/store.py` Knowledge 类(ingest/retrieve)| 30min | 新增 |
| 3 | `src/agents/research.py` 单 agent + N 个 function call tools | 2h | 新增 |
| 4 | `main.py` `python main.py "query"` 端到端 | 30min | 新增 |
| 5 | `README.md` v1(架构图 + 安装 + 5 关键词)| 1h | 更新 |

**总: ~4.5h**,跟剩余预算几乎打满,会撞墙就砍录屏 / 简化 README。

---

## 已选数据策略 (避免你重新讨论)

- **akshare `stock_research_report_em(symbol)`** 已跑通,758 行/票 × 16 列
- **关键字段**: 报告标题 / 东财评级 / 机构 / 行业 / 日期 / 2026-2028 盈利预测 / PDF 链接
- **MVP 只 ingest 元数据拼字符串**(标题+评级+机构+预测),**不下载 PDF**
- **5 只票**: 600519茅台 / 000858五粮液 / 002415海康 / 600036招商银行 / 600276恒瑞医药
- **每只票取最近 5 份** = 25 chunks 总量(够 demo 不超时)
- 拼接格式建议: `"{title} | 评级:{rating} | 机构:{inst} | 行业:{industry} | 日期:{date} | 2026 EPS:{eps_2026}元 PE:{pe_2026}"`

---

## 用户工作风格(必读)

1. **千万别替用户写代码**——给伪代码 / 接口 / 错误诊断,**用户自己打字**。例外:简单 import / 一行模板可以贴板,实现逻辑用户写。
2. **不开口先夸**——直接评价对错,禁止"好——这是个对的思路"这类 cheerleading 开场。
3. **中文优先,英文术语括号补中文**——例如 invariant(不变量)/ encapsulation(封装)。
4. **苏格拉底节奏 + 每 3-4 轮拉高视角**——把散点连成原则,焦虑来自缺整合不是信息过量。
5. **指出严重度**: CRITICAL(crash/数据丢)/ HIGH(逻辑错)/ MEDIUM(可维护)/ LOW(风格)。
6. **atomic commits**: feat/fix/chore/style/docs/test 拆分,别一锅烩。
7. **下次开工暗号**: "Day 10 续"(学习项目每天 new session,不连续 /compact)。

---

## 已踩坑 Top 10 (避免重复)

1. 数据流先成像,签名后写
2. Policy(会变) vs Invariant(破了就 bug) 二分
3. 跨模块调用前先核对签名(看 def 那一行,不是猜)
4. Python 缩进 = 语义,缩错一格逻辑全反
5. docstring 不能跟代码撒谎(返回值要么有要么无,别两边贴)
6. `.gitignore` 模式: 含内部 `/` 默认锚定,无内部 `/` 必须前导 `/`
7. tiktoken 不支持 qwen,用 cl100k_base 近似(偏保守,提前触发压缩)
8. **`uv sync` 会清掉不在 pyproject 的 deps**,装新包用 `uv add` 而不是 pip install
9. mock 的价值是确定性(用死字符串测精确路径,别写 `!= ""` 这种宽松 assert)
10. **跳步 = bug 工厂**——用户连续 3 次跳过验签 → runtime crash 已踩。**Codex 见用户跳关键步要拦下来,别放行**

---

## 用户当前情绪 / 状态

- 今天 9:18 开始,已 7h+,带摸鱼属性
- 女朋友关系不稳定,可能电话打进来打断
- 想今晚 push 出"可投简历版" MVP
- 提过 LangChain / 切 Accio JD 这两次都是 cognitive load 下的逃跑反射,已被 Claude 拒绝。**别让他第 N 次用换框架 / 换方向来逃避难概念**——他卡住时往往是数据流概念没成像,不是工具问题。

---

## 跟 Claude 的协作分工

| 谁 | 做什么 |
|---|---|
| **Claude(我)** | 架构决策、跨模块设计、踩坑预警、commit/PR 文案、ADR 起草、长程规划、外部世界对接(memory) |
| **Codex(你)** | 行级代码指导、Python 语法 / API 答疑、本地命令运行帮手、即时 lint/format、SSH 不可达时的本地操作 |
| **用户** | 打字、跑测试、决策 |

**过渡机制**: 用户跟 Claude 定方向 → Claude 把任务列出 → Codex 陪写 → 用户实现 → 模块完成后用户回 Claude 同步。

**Final review**: 用户 main.py 跑通 + README 写完后告诉 Claude,Claude 做最终架构 review + commit 拆分建议。
