# Stock Assistant 项目原则速查 · Day 2 版

**最后更新:** 2026-04-24 夜(Day 2 第二轮)
**用途:** 所有设计原则、代码约定、术语索引、面试话术的单一入口。
**使用方式:**
- 睡前扫一遍(今天学的东西进长期记忆的最后一步)
- Day X 开工前扫一遍(接续上晚的思路)
- 面试前 30 分钟扫一遍(激活术语,确保张口就来)
- 写新代码时对照:每个设计决策能对上哪条原则?对不上就是"凭感觉写"的信号

---

## 📚 目录

- [一、架构原则(5 条)](#一架构原则5-条)
- [二、代码一致性约定(6 条)](#二代码一致性约定6-条)
- [三、边界设计(1 条)](#三边界设计1-条)
- [四、项目架构(Multi-Agent)](#四项目架构multi-agent)
- [五、面试合体故事](#五面试合体故事)
- [六、术语快速索引](#六术语快速索引)

---

## 一、架构原则(5 条)

### 1. CQS — Command-Query Separation(命令-查询分离)

**提出者:** Bertrand Meyer(1988)

**一句话:** 一个方法要么改状态(Command,返回 None),要么查状态(Query,返回数据),**不能两兼**。

**在你代码里:**

| 方法 | 分类 | 签名 |
|---|---|---|
| `add_message()` | Command | `-> None` |
| `summarize()` | Command | `-> None` |
| `get_messages()` | Query | `-> list[dict]` |

**反面教材:** Python 的 `list.sort()` 如果返回新 list,就是双兼。Python 坚决让它返回 None,反对 `new_list = old.sort()` 的误用。

**面试答法:**
> "我在 WorkingMemory 里用 CQS 保持方法职责单一 —— add_message 和 summarize 只改状态不返数据,get_messages 只返数据不改状态。调用者看方法名就知道安不安全重复调用。"

---

### 2. Signature Honesty — 签名诚实反映语义

**一句话:** 方法签名是和调用者签的合同。签名说返回 X,就必须返回调用者会用的 X。

**在你代码里:**
```python
def summarize(self) -> None:
    """达到阈值时压缩旧消息。

    调用者无需接收返回值,压缩完后用 get_messages() 拿更新后的列表。
    """
```
docstring **主动说明**"我不返回是故意的",防止后人误改。

**反面教材:**
```python
def summarize(self) -> str:     # 签名说谎 —— 返回的 str 调用者不用
```
调用者看到 `-> str` 会以为"要用",写出 `summary = wm.summarize(); log(summary)`,但 summary 已经在 wm 里,外部存一份就是**重复状态**,一旦不同步就是 bug。

**面试答法:**
> "Signature Honesty 是我做签名决策的基准线 —— 不返回值,就必须写 `-> None` 并 docstring 说明。不是签名洁癖,是避免误导下一个读代码的人。"

---

### 3. Lifetime Matching — 生命周期匹配

**一句话:** 依赖生命周期 ≥ 对象生命周期 → **构造函数注入**;依赖每次调用可能变 → **方法参数注入**。

**速算:** 问自己"这个依赖会不会存成 `self._xxx`?"—— 会,就 `__init__` 里收下。

**在你代码里:**
```python
class WorkingMemory:
    def __init__(self, llm: LLMProvider):
        self._llm = llm                    # 构造器注入:llm 全生命周期都用

    def summarize(self) -> None:
        # 用 self._llm,方法签名干净
```

**反面场景(应该用方法注入):**
```python
def translate(text: str, target_llm: LLMProvider) -> str:
    # target_llm 每次调用可能变(今天英语用 gpt-4,明天日语用 qwen)
    ...
```

**面试答法:**
> "依赖注入位置我用 Lifetime Matching 决定 —— llm 整个对象生命周期都要用,放构造器。这也顺便让 summarize 的签名保持干净,Agent 层调用不用每次传 llm。"

---

### 4. DIP — Dependency Inversion Principle(依赖倒置)

**出处:** SOLID 五原则之 **D**(Robert C. Martin)

**一句话:** 高层模块不应该依赖低层模块,两者都应该依赖**抽象**(Protocol / 接口)。

**在你代码里:**
```python
# Day 1
class LLMProvider(Protocol):           # 抽象
    def generate(self, messages, tools, temperature) -> LLMResponse: ...

class QwenProvider:                    # 具体实现 1
    def generate(self, ...): ...

class XiaomiProvider:                  # 具体实现 2(计划中)
    def generate(self, ...): ...

# Day 2
class WorkingMemory:
    def __init__(self, llm: LLMProvider):   # 依赖抽象,不依赖具体
        self._llm = llm
```

**价值兑现:**
- 主对话 qwen-plus(贵但强)
- 压缩调用 qwen-turbo / Xiaomi CodingPlan(便宜)
- 测试用 MockLLMProvider
- **WorkingMemory 代码永远不用改**

**面试答法:**
> "Day 1 我抽 LLMProvider 是 Protocol,Day 2 的 WorkingMemory 构造器只收 Protocol 不收具体类。这是 SOLID 里的 D(依赖倒置)—— 成本优化(plus/turbo 分离)和测试(Mock 注入)两个目标一套代码同时满足,WorkingMemory 不改一行。"

---

### 5. SRP — Single Responsibility Principle(单一职责)

**出处:** SOLID 五原则之 **S**

**一句话:** 一个类应该只有一个**让它改变的理由**。

**在你代码里:**

| 模块 | 职责 | 让它改变的理由 |
|---|---|---|
| `WorkingMemory` | 管消息(存储/压缩/组装) | 压缩策略变了 |
| `Orchestrator` | 编排主对话 | 多 Agent 路由逻辑变了 |
| `LLMProvider` | 调 LLM API | 换模型/换厂商 |
| `tools/knowledge.py` | RAG tool 封装 | 检索方式变了 |

**反面教材:** 如果 `WorkingMemory` 同时持有 main_llm 和 compression_llm,就有两个改变理由(主对话逻辑变 + 压缩逻辑变)→ 违反 SRP。

**面试答法:**
> "WorkingMemory 只持有 compression_llm,不持 main_llm,是 SRP 的应用 —— 这个类的职责是'把消息收拾成 OpenAI messages 格式',主对话调用不是它的职责。SRP 让我一眼能看出'改压缩逻辑只动一个文件,改主对话逻辑也只动一个文件'。"

---

## 二、代码一致性约定(6 条)

### 速查表

| # | 约定 | 正例 | 反例 |
|---|---|---|---|
| 1 | 不对外暴露的依赖加 `_` 前缀 | `self._llm` | `self.llm` |
| 2 | import 必须被本文件引用 | 用到就 import | `from typing import Protocol` 但没用 |
| 3 | docstring 风格项目级统一 | 全仓 Google style | 这个文件 Sphinx,那个 Google |
| 4 | 技术文档标点永远半角 | `Args:` | `Args:`(全角) |
| 5 | 空 `:return:` / `:param:` 字段删掉 | 写就写满,否则删 | `:return:` 后面空着 |
| 6 | 格式工具化 | `uv run ruff format` | 手动调空格 |

### 底层原则

**一致性本身就是价值。** 不是追求某种特定风格最优,而是让整个项目的代码风格**可预测**,新人来了不用猜。

**面试答法:**
> "优质代码的一致性体现在多个层面 —— 命名约定、import 清洁、docstring 风格、标点用法、签名与文档匹配。新人写代码盯'跑得通',老手盯'和团队约定一致'。"

---

## 三、边界设计(1 条)

### Impedance Matching — 阻抗匹配

**一句话:** 你控制不了的边界(外部 SDK/API)用**它要求的原生类型**;你控制的边界用**自己的结构化类型**。

**在你代码里:**

| 方向 | 类型 | 理由 |
|---|---|---|
| 喂给 OpenAI SDK 的 `messages` | `list[dict]` | SDK 要求 dict,包 dataclass 每次要 `asdict()` 转,多一层无用工作 |
| LLMProvider 的返回 | `LLMResponse` dataclass | 下游是你自己的 Agent 代码,用 dataclass 换类型安全 + IDE 补全 |

**类比:** 你不会用 dataclass 包一个 `print()` 的参数,因为 print 吃字符串;但你会用 dataclass 表达自己的领域模型(User、Order)。同一个道理。

**面试答法:**
> "在 LLMProvider 设计里,输入端用 OpenAI SDK 原生的 list[dict] —— SDK 是第三方边界,对齐它的约定减少转换成本。输出端用自定义 dataclass —— 从 generate 返回之后到 Agent 层都是我自己的代码,dataclass 给我静态类型检查和 IDE 补全。这叫 impedance matching,边界两端各用最合适的类型。"

---

## 四、项目架构(Multi-Agent)

### 1. Multi-Agent 单线程总控

**反的是什么:** 上下文爆炸。
**场景:** 如果 Intel Agent 返回自然语言 handoff 给 Orchestrator,Orchestrator 的上下文会被 Intel 的工具调用历史塞满。

**解法:**
1. Orchestrator 单线程持有对话历史
2. Intel 每次 fresh context,无对话记忆
3. Intel 返回**结构化 JSON**(不是自然语言),Orchestrator 按需展开

### 2. Working Memory Hybrid 压缩

**反的是什么:**
- 滑动窗口 → 丢早期用户身份/偏好
- 纯 summary → 压没精度(股票代码、人名、金额)

**解法:** `[总结段]` + `[最近 N 条原文]`
- 索引 `[0]` = 总结
- 索引 `[1..N]` = 最近原文(按时间正序)

### 3. 50% Token 阈值

**为啥不是 90%?** 要给以下预算:
- 压缩调用本身的 input + output
- 下一轮 user 输入
- 下一轮 assistant 输出
- `tool_result` 尖峰(比如 K 线数据返回很长)

顶到 90% 触发压缩,**压缩的 prompt 本身都没空间放了**。

### 4. 三条不压缩规则

| 规则 | 为啥不压 | 实现归属 |
|---|---|---|
| `system prompt` 不压 | 压了 agent 身份丢失 | Agent 层(物理隔离,WorkingMemory 扫不到) |
| 最近 N 轮不压 | 压了对话精度丢失 | WorkingMemory 内部存 N |
| `tool_call` ↔ `tool_result` 成对保留 | API 结构要求(单压一边会报错) | summarize 里做成对检测 |

### 5. Drift 守护(Phase 2,MVP 不做)

增量总结(`summary_v2 = summarize(summary_v1 + new)`)会有"复印件的复印件"精度漂移。**Phase 2 加守护**(如每 M 次增量后做一次全量重摘),**MVP 不碰**。

---

## 五、面试合体故事

### 问:"讲讲你这个股票助手项目?"

> "我做了一个个人投研 Multi-Agent 助手,**面向个人散户兼职投研者** —— 白天工作没空盯盘、每次对话都要从头讲背景、akshare 数据和研报 RAG 和新闻分散调用不过来。
>
> 我设计了**单线程 Orchestrator + 情报 Agent + Working Memory + Function Calling** 的架构,**刻意不用 LangGraph/AutoGen**,目的是面试能讲清每层原理。
>
> **在 WorkingMemory 这个模块上,我同时应用了五条设计原则:**
> - **CQS** 保证方法职责单一(add_message/summarize 是 Command,get_messages 是 Query)
> - **Signature Honesty** 让签名诚实反映语义(`-> None` 就是不返回给调用者用的东西)
> - **Lifetime Matching** 决定依赖注入位置(llm 放 `__init__` 而不是方法参数)
> - **DIP** 让 WorkingMemory 依赖 LLMProvider Protocol 而不是具体实现(主对话 qwen-plus / 压缩 qwen-turbo 可以分开,WorkingMemory 不改一行)
> - **SRP** 决定这个类只持有 compression_llm,主对话 LLM 归 Orchestrator —— 一个类只一个改变理由
>
> **压缩策略用 Hybrid(总结+最近 N 条原文),50% token 阈值而不是 90%**,因为要给压缩调用本身、下一轮对话、tool_result 尖峰都留预算。三条不压缩规则:system prompt / 最近 N 轮 / tool_call↔tool_result 成对。"

### 问:"为什么不用 LangGraph/AutoGen?"

> "我看过它们。LangGraph 把状态图和 Agent 定义揉一起,方便快速搭,但丢掉对'Orchestrator 如何单线程控制 / 上下文如何压缩'的**显式把控**。这个岗位要'精通 Agent 架构核心组件原理',所以我手搓 —— 每一层我都能解释为啥这么写。真要上生产,框架当然值得加,但面试考的是原理理解。"

### 问:"50% 阈值为啥不顶高点?"

> "顶 90% 意味着压缩触发时,已经没空间放压缩的 prompt 了。50% 是给以下预算留空间:压缩调用本身的 input+output、下一轮 user 输入、下一轮 assistant 输出、tool_result 尖峰。单位用 token 不用消息数,因为 context window 是 token 计的,消息长度方差极大。"

### 问:"你这个项目的 Agent 记忆系统是什么?"

> "MVP 只做 Working Memory,也就是**会话内**记忆。Episodic / Semantic / Procedural 这些跨会话记忆在 Roadmap 的 Phase 2。原因是 MVP 阶段不能证明产品价值的功能就不该做 —— 这个 trade-off 记录在 ARCHITECTURE.md。但我在接口设计时预留了扩展点(memory.manager 的统一 write/recall/compress 接口),Phase 2 加其他记忆层不用改 Working Memory。"

---

## 六、术语快速索引

| 术语 | 一句话 | 本项目位置 |
|---|---|---|
| **CQS** | 方法要么改状态要么查状态不能两兼 | WorkingMemory 三方法 |
| **Signature Honesty** | 签名要诚实反映返回值用途 | `summarize -> None` |
| **Lifetime Matching** | 生命周期≥对象→构造器注入 | `__init__(self, llm)` |
| **DIP** | 依赖抽象不依赖具体(Protocol) | `LLMProvider` |
| **SRP** | 一个类只一个改变理由 | WorkingMemory 只管消息 |
| **Impedance Matching** | 外部边界用原生类型,内部用结构化类型 | `list[dict]` in / `LLMResponse` out |
| **Hybrid 压缩** | `[总结]+[最近 N 条原文]` | Working Memory 策略 |
| **50% Token 阈值** | 给压缩本身+下轮+tool_result 留预算 | summarize 触发条件 |
| **Orchestrator** | 单线程持有对话历史,调度子 Agent | `agents/orchestrator.py` |
| **Intel Agent** | 每次 fresh context,返回结构化 JSON | `agents/intel.py` |
| **Function Calling** | LLM 按需调工具获取数据 | `tools/` 目录 |
| **Protocol** | Python 3.8+ 结构化类型 | `LLMProvider(Protocol)` |
| **Dataclass** | 自动生成 `__init__`/`__repr__` 的轻量类 | `LLMResponse` |
| **YAGNI** | 暂时用不上的代码别留 | |
| **NotImplementedError** | 计划做但未实现的占位 | XiaomiProvider.generate |
| **TypedDict** | 比 `dict` 更严的字典类型标注 | 目前不用,知道存在 |
| **Drift 守护** | 防止增量总结精度漂移 | Phase 2,MVP 不做 |

---

## 📝 演进记录

- **v0.1 (2026-04-24 Day 2 夜):** 首次生成,覆盖 Day 1 + Day 2 内容
- 明晚 Day 3 后追加:三条不压缩规则的实现选择、N 的存储单位决策等
