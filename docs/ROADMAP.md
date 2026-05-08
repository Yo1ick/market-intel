# Stock Assistant 项目路线图 v1.2

**版本:** v1.2(Day 3 后实况校准,7 晚 → 10 晚)
**生成时间:** 2026-04-26 夜(v1.2);2026-04-24(v1.1 初版)
**关联文档:** [PRD.md](./PRD.md)(完整远景) / [PRD-MVP.md](./PRD-MVP.md)(2 周冲刺版) / [PITFALLS.md](./PITFALLS.md)

---

## 1. 产品层(PRD 提炼,面试必答)

| 问 | 答 |
|---|---|
| 面向谁 | 个人散户 / 兼职投研者。白天工作无法盯盘,关注 <50 只股 |
| 核心痛点 | (1) 单 Agent 问一答一,没法主动盯盘;(2) 无记忆,每次对话独立从头讲;(3) 工具碎片化 —— akshare 数据 / 研报 RAG / 新闻彼此孤立,无法组合调用 |
| 功能边界(可投版) | ✅ 2 Agent(Orchestrator + Intel)+ 1 层 Working Memory + 2 tools(`rag_search` + `get_realtime_quote`)+ README<br>❌ 盯盘 / 复盘 / 选股 Agent、Episodic / Semantic / Procedural memory、APScheduler、Streamlit、语义缓存、Docker、K 线 tool、ARCHITECTURE.md(进投后继续) |
| 成功标准 | 混合对话通过:"宁德时代今天价格?研报怎么看它?" → 触发 `get_realtime_quote` + `rag_search`。P95 < 8s,单对话 < ¥0.15,单测核心模块 ≥ 70% |

### 30 秒电梯讲述(面试标准答案)

> 我做了一个个人投研 Multi-Agent 助手,解决三个问题:单 Agent 只能问一答一没法主动盯盘、每次对话都从头讲没记忆、akshare 数据 / 研报 RAG / 新闻彼此孤立没法组合调用。我用**单线程 Orchestrator + 情报 Agent + Working Memory + Function Calling** 手搓了一套,刻意不用 LangGraph / AutoGen,目的是能在面试讲清每一层原理。MVP 是 2 Agent + 1 层记忆 + 2 个工具,端到端能跑,开源可演示。

---

## 2. 时间窗决策:10 晚混合路径(原 7 晚 + 3 晚 slip)

**策略演进:**

- PRD-MVP v2(2026-04-19):14 晚做完整 2 Agent + 3 tools 才投 → 故事完整但延迟 10 晚
- Roadmap v1.0(2026-04-23):4-5 晚 working.py + 1~2 tool 就投 → 快但第一版故事弱
- **v1.1 混合(2026-04-24):7 晚**,兼顾完美和速度
- **v1.2 实况校准(2026-04-26):10 晚** —— Day 2 整晚被 JD 打断;Day 3 五分钟"清坑"任务意外撞见抽象层级错位 bug,顺势重构 Provider 层并锁定 5 条新原则,但 add_message + pytest 未达成 ← 当前策略

**10 晚分配(v1.2):**

| 晚 | 日期 | 状态 | 任务 / 实际产出 |
|---|---|---|---|
| 1 | 2026-04-24 | ✅ 完成 | PRD 对齐 + summarize 设计 + LLMProvider DI 讨论 → `working.py` 骨架 + summarize 决策表 |
| 2 | 2026-04-25 | ⏸️ 跳过 | 整晚处理新 JD(嘉兴九州),无代码进展;路径 A/B/C 决策仍未做 |
| 3 | 2026-04-26 | 🟡 部分 | provider.py 修 5 坑,意外重构出 `OpenAICompatibleProvider`(原 3 类合 1);锁定 5 条新原则;**add_message + pytest 未达成** |
| 4 | 2026-04-27 | ⏳ 待做 | 清 Day 3 延伸坑(`_` 前缀 X2 + tool_calls 转 dict X1 + 装 ruff format X3)+ `add_message` 实现 + 第一个 pytest |
| 5 | 2026-04-28 | ⏳ 待做 | `summarize` 压缩实现 + WM 完整单元测试(原 Day 2 目标) |
| 6 | 2026-04-29 | ⏳ 待做 | `tools/registry.py` + `schema.py` + `tools/knowledge.py`(rag_search)(原 Day 3 目标)|
| 7 | 2026-04-30 | ⏳ 待做 | `tools/market.py` `get_realtime_quote` + `agents/base.py`(原 Day 4)|
| 8 | 2026-05-01 | ⏳ 待做 | `agents/intel.py` + `agents/orchestrator.py`(原 Day 5)|
| 9 | 2026-05-02 | ⏳ 待做 | `main.py` CLI + 端到端联调 + 5 轮循环保护(原 Day 6)|
| 10 | 2026-05-03 | ⏳ 待做 | README(含 vs LangGraph / AutoGen 选型对比)+ 简历 v5 更新 → **可投材料**(原 Day 7) |
| 11+ | 投后 | — | K 线 tool / ARCHITECTURE.md / PITFALLS 扩展 / 盯盘 Agent → Roadmap Phase 5+ |

**节奏保护:每晚 20:00-22:30,单次 2.5 小时预算。某晚如果某个任务跑超,不要硬磕,改用"下一晚优先把这块收尾,其他顺延"的节奏。**

**Day 3 给的额外回报:** 时间 slip 3 晚不是浪费 —— 5 条新可迁移原则(Impedance Matching / Lifetime Matching / 最小作用域 / 签名诚实 / 抽象层级判断)归到 3 个母原则(最小化 / 边界匹配 / 诚实表达),面试合体故事点级别,详见 [PITFALLS.md Day 3 章节](./PITFALLS.md#day-3-provider-层精修2026-04-26-夜)。

---

## 3. 简历故事点(按 JD 命中度排序)

### T1:Multi-Agent 单线程总控(PRD 核心)

- Orchestrator 单线程持有对话历史,Intel Agent 每次 fresh context 无记忆
- 子 Agent 返回结构化 JSON(不是自然语言),Orchestrator 按需展开
- 手搓不用 LangGraph / AutoGen,目的:面试讲清每层原理
- → 命中 JD "Multi-Agent 架构设计和落地" + "上下文工程优秀实践"

### T2:Agent 记忆系统设计(Working Memory)

- Hybrid 压缩(总结 + 最近 N 条原文)—— 解决滑动窗口丢身份 & 纯 summary 压没精度
- 50% token 阈值(不是 90%,预留压缩调用 + 下一轮 + tool_result 尖峰)
- 三条不压缩规则(system prompt / 最近 N 轮 / `tool_call` ↔ `tool_result` 成对)
- 增量 drift 认知(Phase 2 加守护)
- → 命中 JD "Agent 记忆系统" + "上下文工程及压缩"

### T3:LLMProvider Protocol 依赖注入 + 抽象层级判断(Day 3 升级)

- Protocol + dataclass 分层设计
- 主对话 qwen-plus / 压缩调用 qwen-turbo 分离(成本优化 3-5 倍)
- **Day 3 重构亮点:** 原本写了 3 个 Provider 类(Qwen/Xiaomi/Deepseek),Day 3 发现三者都是 OpenAI 兼容 API,实际是同一抽象的不同实例,合成 `OpenAICompatibleProvider` 一类多实例。Protocol 真正兑现要等加 Claude / Gemini 原生 SDK 时
- 后续可切本地 MLX / ollama / 真正不同的 Claude provider 不改上层
- → 命中 JD "Agent 架构核心组件调优" + "上下文工程优秀实践"

### T4:RAG + Function Calling 联合

- 理论问题走 `rag_search`,数据问题走 `get_realtime_quote`
- 意图路由降成本
- → 命中 JD "RAG" + "Function Calling"

---

## 4. 面试必问预案

| 追问 | 标准答 |
|---|---|
| "为啥只做 Working 不做 Episodic?" | Working 到 Episodic 是从会话内到跨会话,需要 SQLite + 向量索引,增加两层复杂度。MVP 阶段不能证明产品价值就不该做 —— trade-off 记录在 ARCHITECTURE.md |
| "为啥不用 LangGraph?" | 看过,它把状态图和 Agent 定义揉一起方便快速搭,但丢掉对"Orchestrator 如何单线程控制 / 上下文如何压缩"的显式把控。岗位要"精通原理",所以手搓 |
| "盯盘 Agent 做了吗?" | MVP 已完成 Orchestrator + 情报 Agent + Working Memory + 2 个核心工具,盯盘在 Roadmap Phase 6,架构已预留扩展点(Event Log + APScheduler 接口) |
| "单 Agent 和 Multi-Agent 的区别?" | 反上下文爆炸 —— 单 Agent 所有工具调用记录都堆在主对话,Multi-Agent 让 Intel 每次 fresh context 只返回结构化 JSON,主对话只看"情报 Agent 返回了 3 篇文档",不看 RAG 的原文 |
| "为啥 50% 阈值不是 90%?" | 要给压缩调用本身的 input+output、下一轮 user 输入、下一轮 assistant 输出、tool_result 尖峰都留预算。顶 90% 意味着压缩触发时已经没空间放压缩的 prompt 了 |

---

## 5. JD 空白清单(v1.1 更新)

### 必补(投递前)

- ✅ 开源 Agent 框架了解 → README 里对比 LangGraph / AutoGen / CrewAI 选型段落(第 7 晚写)
- ✅ MultiAgent → v1.1 决定 MVP 就做 Orchestrator + Intel 两个,不延后

### 绕法

- 工程化 / 本地模型 / 日志:README 里提"已规划",面试说"时间窗优先验证核心"
- 2 年软工 + 1 年 Agent 经验:AMR 测试期间自动化 / 脚本经验折算 + 项目深度

---

## 6. 纪律提醒

- **节奏:** 已决定"边投边优化",不再走"学完整套再投"的长路径。7 晚到可投状态是硬目标
- **拒绝过度工程:** 简历用的 demo 不需要生产级,能讲清设计决策就够
- **每晚收工前过一眼这份地图**,确认"今晚推进了哪条线,离可投近了多少" —— 防止陷入细节忘记大方向

---

## 演进说明

### v1.0 → v1.1(2026-04-24)

- 产品层补齐(v1.0 空白,全从 PRD 提炼)
- 时间窗从 4-5 晚 → 7 晚混合
- MVP 功能边界从"1~2 tool"→ 明确"2 Agent + 2 tool",K 线工具移到投后
- 简历故事点从 3 个 → 4 个(T1 升级为 Multi-Agent 单线程,原 T1 Memory 变 T2)
- 新增"面试必问预案"章节

### v1.1 → v1.2(2026-04-26 夜实况校准)

- 时间窗从 7 晚 → 10 晚(Day 2 JD 打断 + Day 3 重构 Provider 层未完成原 plan)
- Day 3 新增 5 条原则归 3 个母原则(详见 PITFALLS.md Day 3 章节),作为时间成本的回报
- Provider 层从"3 类(QwenProvider / XiaomiProvider / DeepseekProvider)"重构为"1 类多实例(OpenAICompatibleProvider)"
- 简历故事点 T3(LLMProvider Protocol 依赖注入)更新表述:Protocol 是为"真正不同的实现"准备的,而非"同一实现的不同配置"
- 路径 A/B/C(stock-only / 多模态测试 / 双项目)决策仍未做,等 MVP 推进 + 下一波 JD 数据再决
