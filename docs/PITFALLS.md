# Stock Assistant 踩坑记录 & 面试级表达

> **目的**：复盘每一个踩过的坑，沉淀为"面试能讲清楚"的表达。
> **用法**：每次踩新坑立即追加；面试前通读一遍把"面试级表达"过一遍嘴。

## 目录

- [Phase 2: RAG 基础建设](#phase-2-rag-基础建设)
- [Phase 3: Chat + RAG 联调](#phase-3-chat--rag-联调)
- [Phase 4: Multi-Agent 启动热身](#phase-4-multi-agent-启动热身)
- [Phase 5: Multi-Agent 骨架搭建](#phase-5-multi-agent-骨架搭建)
- [Day 3: Provider 层精修（2026-04-26 夜）](#day-3-provider-层精修2026-04-26-夜)
- [全局核心原则](#全局核心原则)

---

## Phase 2: RAG 基础建设

### Python 基础类

#### 1. `encoding=str` vs `encoding="utf-8"`
- **错误**：`open(file, encoding=str)` — 传了类型对象
- **正确**：`open(file, encoding="utf-8")` — 传字符串值
- **Why**：`str` 是 Python 的类型对象，不是字符串值

#### 2. `"texts"` vs `texts`（引号 vs 变量）
- **错误**：`input="texts"` — 把 "texts" 五个字母当文本发送
- **正确**：`input=texts` — 传变量
- **Why**：加引号就是字符串字面量；不加引号才是引用变量

#### 3. `append` vs `extend`
- `append([4,5])` → `[1,2,3,[4,5]]` — 放了一个袋子进去
- `extend([4,5])` → `[1,2,3,4,5]` — 把袋子里的东西倒进去
- **Why**：分批调 API 时要用 `extend` 把每批结果合并成扁平列表

#### 4. `response.data[0]` 只取了第一条
- **错误**：传了列表进去，只取 `data[0]`
- **正确**：`[item.embedding for item in response.data]` 取所有
- **Why**：批量请求返回多个结果，要遍历

### 路径类

#### 5. Windows 上用 Linux 绝对路径
- **错误**：`/data/docs/file.md`（Linux 风格）
- **正确**：`data/docs/file.md`（相对路径）
- **Why**：Windows 上 `/` 开头会被解析为盘符根目录

#### 6. 运行脚本时工作目录不对
- **错误**：直接运行 `src/rag/main.py`，相对路径找不到 `data/`
- **正确**：`cd E:\Study\project\stock-assistant && uv run python main.py`
- **Why**：相对路径是相对于工作目录，不是脚本所在目录

### 拼写 / 自动补全类

#### 7. PyCharm 自动导入垃圾
- `from http.client import responses` — 没用的导入
- `from sympy.multipledispatch.dispatcher import source` — 没用的导入
- **How**：写完代码检查顶部 import，删掉不认识的

#### 8. 拼写错误
- `metadates` → `metadatas`
- `chorma` → `chroma`
- `pormpts` → `prompts`
- **How**：变量名/参数名拼错不会报语法错，运行时才 KeyError

### ChromaDB 类

#### 9. `ids` 必须是字符串
- **错误**：`ids=[i]`（整数）
- **正确**：`ids=[str(i)]`

#### 10. `documents` 要传文本，不是字典
- **错误**：`documents=[chunk]`（整个字典）
- **正确**：`documents=[chunk["text"]]`

#### 11. `metadatas` 必须是字典列表
- **错误**：`metadatas=[chunk["source"]]`（字符串）
- **正确**：`metadatas=[{"source": chunk["source"]}]`

#### 12. `embeddings` 要取对应的那一个
- **错误**：`embeddings=[vectors]`（整个列表）
- **正确**：`embeddings=[vectors[i]]`（第 i 个向量）

### 正则 / 分割类

#### 13. 中英文冒号不同
- `re.split(r"第\d+课：")` 用英文 `:` 但文档用中文 `：`
- **Why**：中文标点和英文标点是不同字符

#### 14. 粘贴代码时多了隐藏字符
- `split("\n---\n")` 返回 1 段，因为粘贴时多了放大镜字符
- **How**：分割不生效时，先 `print(repr(...))` 检查原始字符

### 配置类

#### 15. `.env` 格式
- **错误**：直接写 `sk-xxx`
- **正确**：`DASHSCOPE_API_KEY=sk-xxx`（KEY=VALUE，等号无空格）

#### 16. `.gitignore` 漏了 `.idea/` 和 `data/docs/`
- **How**：`git init` 后先配好 `.gitignore` 再 `add`

### Phase 2 核心教训

- **引号问题最常见** — 该传变量的地方别加引号
- **PyCharm 自动补全要警惕** — 检查每一行 import
- **拼写错误不报语法错** — 运行时才炸，难排查
- **先用小数据测试** — `chunks[:3]` 验证通过再全量跑

---

## Phase 3: Chat + RAG 联调

### 数据结构类

#### 17. `set` vs `list`（花括号 vs 方括号）
- **错误**：`questions = {"q1", "q2"}` — 集合，无序
- **正确**：`questions = ["q1", "q2"]` — 列表，有序
- **Why**：set 是无序集合，循环顺序不可预测；看到"输出顺序跟想的不一样"第一反应查结构类型

#### 18. retrieve 返回 dict 是 list of list
- **结构**：`results["documents"][0]` 才能拿到文本列表
- **Why**：ChromaDB 支持批量查询，外层 list 是"问题批次"，内层 list 是"每个问题的 top_k"
- 迭代整个 `results` 拿到的是 key 名（`ids/embeddings/documents/...`），不是内容

### 函数调用类

#### 19. `retrieve("q")` vs `retrieve(q)`（重大 bug）
- **错误**：`retrieve("q")` — 永远在检索字母 "q" 的 embedding
- **正确**：`retrieve(q)` — 真正检索当前循环变量
- **Why**：和 Phase 2 #2 同根同源 —— 该传变量的地方别加引号
- **特别危险**：这个 bug 不报错，还会偶尔输出看似合理的结果（假阳性），极难察觉

#### 20. 传错参数类型：dict vs str
- **错误**：`chat(q, results)` — 传整个 ChromaDB 返回 dict
- **正确**：`chat(q, context)` — 传拼好的字符串
- **Why**：`f"资料：{dict}"` 不报错，但会变成一大坨转义字符，LLM 读不懂

### RAG 调优类

#### 21. distance 高不等于内容不相关
- **反例**：查"什么是第一类买点"，distance 最高的 chunk 2 反而包含完整定义
- **How**：千万别用 distance 阈值简单过滤；**人工翻 chunk 永远比信数字可靠**
- embedding 只看语义"表面相似"，不懂哪段真正回答问题

#### 22. 模型性格 ≠ 模型能力（重要洞察）
- `qwen3.6-plus`（CodingPlan 免费）：为代码任务调教，极度保守，宁可说"未找到"也不整合零散信息
- `qwen-plus`（标准）：通用型，更愿意综合上下文 → RAG 正常答
- **How**：RAG 场景选模型不能只看 benchmark，要测它在"零散信息整合"上的表现

#### 23. 假阳性 bug 是最危险的 bug
- **现象**：`retrieve("q")` 的 bug 下，"什么样的人不能炒股"居然答得像那么回事
- **原因**：embedding("q") 的随机 3 段里刚好有《教你炒股票 6》，问题足够模糊，能硬扯答案
- **How**：看到输出"差不多对"不代表代码对；对不同输入要输出差异化结果才算真的对

### Debug 方法论

#### 24. Debug 第一步：看 LLM 的真实输入
- **误区**：LLM 答不好 → 先调 prompt / 换模型
- **正确**：先在 `chat.completions.create` 之前 print 发给 LLM 的 messages
- **Why**：80% 的"LLM 不听话"是输入有问题（context 空、context 截断、格式错误），不是模型锅

#### 25. 数据结构搞不清时先 print 结构
- 拿到陌生 dict/object → `for k in obj: print(k)` 或 `print(obj.keys())`
- 别猜，看一眼

### Phase 3 核心心得（面试可用）

- **RAG 调优优先级：数据 > 检索 > prompt > 模型**。别反着来。
- **成本优化方向**：调 top_k、切 chunk、加意图路由（router）、缓存 → 贵模型只给关键问答用
- **免费模型的陷阱**：厂商按场景调教，CodingPlan 的 qwen 做 RAG 不如花钱的通用版
- **本地模型 + 微调**是下一步加分项：私有数据敏感 + 降本 + 可控行为，都是面试亮点

---

## Phase 4: Multi-Agent 启动热身

本节是 Multi-Agent 改造的第一次热身练习：给 `chat()` 加 `tools` 参数。20 行改动，但暴露了 4 个值得沉淀的点。

### 26. Python 可变默认参数陷阱

**现象**：
```python
def add_item(x, bag=[]):       # 坑!
    bag.append(x)
    return bag

add_item(1)   # [1]
add_item(2)   # [1, 2]  ← 不是 [2]!
add_item(3)   # [1, 2, 3]  ← 不是 [3]!
```

**Why**：默认值 `[]` 只在**函数定义时创建一次**。所有未传参的调用**共享同一个 list**，任何 mutate 都会累积。

**正解**：
```python
def add_item(x, bag=None):
    if bag is None:
        bag = []
    bag.append(x)
    return bag
```

**面试级表达**：
> "Python 里默认参数 `[]` 只在**函数定义时创建一次**，所有没传参的调用**共享同一个 list**，如果函数内部有 append 或修改，会污染后续调用。用 `None` 作默认值，进函数体再判断创建，保证每次调用独立。"

关键词：**"只创建一次"** + **"共享同一个"**。

---

### 27. 参数命名要跟 API 约定一致

**现象**：一开始把参数叫 `tool`（单数），但 OpenAI API 的 key 是 `"tools"`（复数）。

**Why**：
- **API 约定一致**：变量名跟官方文档对齐，读代码的人一眼能对上。
- **语义正确**：传进来是 list，复数形式语义准。

**面试级表达**：
> "OpenAI API 规范里参数名就是 `tools`，变量名跟 API 保持一致降低认知负担。另外 list 装多个工具，复数形式语义更准。"

---

### 28. 条件传参 + 组合爆炸规避

**问题**：`tools=None` 不同 SDK 行为不统一——有的过滤掉，有的报错。怎么办？

**反面写法 A（分支爆炸）**：
```python
if tools:
    client.chat.completions.create(model=..., messages=..., temperature=..., stream=..., tools=tools)
else:
    client.chat.completions.create(model=..., messages=..., temperature=..., stream=...)
```

未来再加 `response_format`、`tool_choice`、`max_tokens` 三个可选参数 → **2^4 = 16 个分支**。

**正解 B（dict + 展开）**：
```python
kwargs = {
    "model": "qwen-plus",
    "messages": messages,
    "temperature": temperature,
    "stream": True,
}
if tools:
    kwargs["tools"] = tools
# 未来加可选参数只要再加一个 if
response = client.chat.completions.create(**kwargs)
```

**面试级表达**：
> "两个原因。一是 `tools=None` 在不同 SDK 行为不一致，'有才传'避免未定义行为。二是用 dict 组装 + `**` 展开的模式，未来加可选参数只要加一个 `if`，不会导致分支组合爆炸。"

---

### 29. `if __name__ == "__main__":` 不是单元测试

**误解**：把 `if __name__ == "__main__":` 当成"单元测试"。**不是**。

**真相**：这是 **Python 的脚本/模块双模式机制**：

```python
# 运行 python chat.py 时:
# __name__ == "__main__"  → 块内代码执行

# 别的文件 from chat import chat:
# __name__ == "chat"      → 块内代码不执行
```

**单元测试**是用 `pytest`/`unittest` 框架写的独立测试文件（`test_chat.py`），有断言、mock、能批量跑。

**不加会怎样**？假设你在文件末尾直接写 `chat("你好")`，那任何 `from chat.chat import chat` 都会**意外触发一次对话**——烧 API 钱，拖慢启动。

**面试级表达**：
> "`if __name__ == '__main__':` 是 Python 的脚本/模块双模式入口。块里的代码只在**直接运行**这个文件时执行；被**作为模块 import** 时不执行。用来做最小自测，避免污染其他 import 这个模块的代码。它**不是单元测试**，单元测试是用 pytest/unittest 写的独立测试文件。"

---

### Phase 4 核心心得

- **改 20 行代码能暴露 4 个基础盲点** → 小练习比大项目更能发现知识漏洞
- **"方向对"和"讲得清"差很远** → 代码能跑 ≠ 你真懂。复盘时能精准说出 Why 才算吃透
- **面试级表达的训练**：每个坑都练一遍 "用一两句话说清楚"。关键词要命中（如"只创建一次"/"共享同一个"/"组合爆炸"）

---

## Phase 5: Multi-Agent 骨架搭建

本节是 Week 1 Day 1：建立 `src/llm/provider.py` —— 把 LLM 调用从 RAG 专用的 `chat()` 里抽出来，做成与业务无关的基础设施层。核心产出：`LLMResponse` dataclass + `LLMProvider` Protocol + `QwenProvider` 实现。

### 30. `messages` 参数必须是 list[dict]，传 str 会回 500

**现象**：
```python
Qwen.generate("你好吗", None, 0.8)     # ❌ messages 是 str
# 报错:openai.InternalServerError: Error code: 500
```

**正解**：
```python
Qwen.generate(
    messages=[{"role": "user", "content": "你好吗"}],
    tools=None,
    temperature=0.3,
)
```

**Why**：OpenAI API 的 `messages` 字段就是 list of dict，每个 dict 至少有 `role` + `content`。传 str 进去，SDK 序列化成 JSON body 时 server 端校验挂了，Dashscope 偷懒返回 500（应该返 400）。

**Debug 教训**：500 错误第一反应**先怀疑自己**，不是"服务器挂了"。Dashscope 尤其爱把客户端错误返 500。

**面试级表达**：
> "OpenAI-compatible API 的 messages 是 list of role-content dicts，传错类型时客户端 SDK 不会拦截，要到 HTTP 请求阶段才暴露，服务端返回信息可能误导——debug 时先怀疑自己的请求格式对不对。"

---

### 31. Python 类型注解是 advisory，不在运行时强制

**现象**：签名写了 `messages: list`，但传 `"你好吗"`（str）进去，**运行时不报错**，一直到 SDK 层才炸。

**Why**：Python 的类型注解（PEP 484）**只是提示信息**，不在运行时强制。检查靠：
- **静态工具**：mypy / PyCharm 的黄色警告
- **运行时断言**：自己写 `assert isinstance(...)`（少见）
- **下游边界**：SDK / HTTP 层 / pydantic 等主动检查的地方

**对比**：
| 语言 | 类型强度 | 传错类型 |
|------|---------|----------|
| Python | advisory | 运行时 OK，下游才炸 |
| TypeScript | compile-time | 编译器直接阻止 |
| Go | strict compile-time | 无法编译 |
| Rust | strict compile-time | 无法编译 |

**面试级表达**：
> "Python 的 type hints 是 PEP 484 引入的**静态提示**，不在运行时强制。要真正的类型安全得用 mypy / pydantic / 或手动 assert。'签名写了 list，传 str 没报错'不是 bug，是设计。"

---

### 32. OpenAI SDK 返回对象的层级结构

**现象**：
```python
tool_calls = response.tool_calls
# AttributeError: 'ChatCompletion' object has no attribute 'tool_calls'
```

**Why**：`response` 顶层是 `ChatCompletion`，`tool_calls` 不在顶层，在 message 层：

```
ChatCompletion (= response)
├── choices: list
│   └── [0]: Choice
│       ├── message: ChatCompletionMessage
│       │   ├── content: str | None       ← 文字答案在这
│       │   ├── tool_calls: list | None   ← 工具调用在这
│       │   └── role
│       └── finish_reason
├── id
├── model
└── usage
```

**正解**：
```python
message = response.choices[0].message
content = message.content
tool_calls = message.tool_calls
```

**Debug 教训**：`AttributeError: '<Type>' object has no attribute '<x>'` 第一反应：**我访问的层级对吗**？不是"字段不存在"，是"你找错了层级"。

**面试级表达**：
> "OpenAI ChatCompletion 返回的是多层嵌套结构：`response.choices[0].message`。`content` 和 `tool_calls` 挂在 `message` 上，不是顶层 response。新人常把 tool_calls 错写到顶层——看到 AttributeError 第一反应是访问层级错了，不是字段不存在。"

---

### 33. 函数参数 ≥ 3 个必用关键字参数

**现象**：
```python
Qwen.generate("你好吗", None, 0.8)
#             ↑       ↑    ↑
#             谁?     谁?   谁?
```

对着签名 `def generate(self, messages, tools=None, temperature=0.3)` 才能对出来参数对应。读代码摩擦大，传错顺序还不报错。

**正解**：
```python
Qwen.generate(
    messages=[{"role": "user", "content": "你好吗"}],
    tools=None,
    temperature=0.3,
)
```

**硬规则**：函数有 3 个或更多参数时一律用**关键字参数**，位置参数只给前 1-2 个最核心的必选参数保留。

**Why**：
- **自解释**：看调用点不用跳到定义
- **防错**：传反顺序立刻报错
- **易扩展**：未来加参数不会让现有位置参数错位

**面试级表达**：
> "函数参数 ≥ 3 个时一律用关键字传参——可读性、防错、可扩展性三赢。位置参数留给 1-2 个最核心的必选参数。"

---

### 今日架构心得（面试级）

这些不是"坑"，是**设计决策**。按重要度排：

#### A. 业务层 vs 基础设施层（分层设计）

| 层 | 文件 | 职责 | 耦合 |
|----|------|------|------|
| 业务层 | `chat.py` | RAG 专用：固定 system prompt + messages 结构 | 耦合业务场景 |
| 基础设施层 | `provider.py` | 纯调用：传 messages 回 LLMResponse，不关心调用者干什么 | 业务无关 |

**面试级表达**：
> "chat.py 是业务层，耦合了 RAG 场景的 system prompt 和 messages 结构；provider.py 是基础设施层，只负责把 messages 发给 LLM、把响应还回来。分层是为了让 Agent 场景复用 provider，不用动 RAG 代码——**关注点分离**。"

#### B. Protocol vs ABC（结构化 vs 名义子类型）

```python
from typing import Protocol

class LLMProvider(Protocol):
    def generate(self, messages, tools=None, temperature=0.3) -> LLMResponse: ...
```

`QwenProvider` **不需要显式继承** `LLMProvider` —— 只要长得像（有同名方法、同样签名），Python 类型系统就认。

**对比**：
- **ABC / 继承**：名义子类型（nominal）——必须显式 `class X(LLMProvider):`
- **Protocol**：结构化子类型（structural）——"长得像就是"

**面试级表达**：
> "Protocol 是 Python 3.8+ 的**结构化子类型**，对应 Go interface / TypeScript interface。它描述**行为契约**（方法签名），不关心属性或实现细节。关键词：duck typing 的**静态化**——运行时随便 duck，静态检查器也认。"

#### C. dataclass 返回 > dict 返回 > str 返回

```python
@dataclass
class LLMResponse:
    content: str | None = None
    tool_calls: list | None = None
```

**为什么不用 dict**：
- 打错字段名不会立刻报错（`response["tool_cals"]` 运行时才 KeyError）
- IDE 不能补全
- 改字段名所有调用方悄悄坏掉

**为什么不用 str**：
- 丢失结构信息（tool_calls 无法塞进 str）
- 调用方要手动 parse，回到 stringly-typed

**面试级表达**：
> "返回值用 `@dataclass` 而不是 dict/str：IDE 能补全、字段改名立刻红线、类型检查器能拦错。避免 **stringly-typed**——把结构信息用字符串传是 anti-pattern。"

#### D. 身份配置 vs 业务参数

```python
# 身份：创建时定死
QwenProvider(model="qwen-plus", api_key="...", base_url="...")

# 业务：每次调用都不一样
provider.generate(messages=..., tools=..., temperature=...)
```

**原则**：实例的"身份"（model / endpoint / credentials）放 `__init__`，每次"业务请求"（messages / tools / temperature）放方法参数。

**面试级表达**：
> "`__init__` 放**身份配置**——确定这个实例是什么（哪个模型、哪个 endpoint、哪个密钥）。方法参数放**每次业务参数**——这次要问什么、用哪些工具。身份不变，业务变。"

---

### Phase 5 核心心得

- **"抽象"不是凭空加一层，是看到重复** —— 写完 XiaomiProvider 才真正看到 QwenProvider 抽象的必要性。在"需要之前抽象"就是过度设计。
- **接口优先，实现其次** —— Protocol + dataclass 先定义清楚"对外承诺"，实现再填空。接口定好，实现可以随便换。
- **每个设计决策都要答得出 Why** —— 面试官不问"你用了什么"，问"为什么这么选"。Protocol 为什么不用 ABC？dataclass 为什么不用 dict？这些才是考点。
- **非流式是 Agent 基础设施的默认选择** —— Agent 要拿到完整响应（含 tool_calls）才能决策下一步，streaming 让 tool_calls 分片拼接复杂。流式作为可选能力未来再加。

---

## Day 3: Provider 层精修（2026-04-26 夜）

> 在原计划"5 分钟清坑"任务中意外发现一个抽象层级错位的设计 bug，把"3 个 Provider 类"重构成"1 个类 3 次实例化"，并锁定 5 条新的可迁移原则。Day 1 LLMProvider DI 抽象到 Day 3 实战的闭环兑现。

### 34. 类型标注松到 `list`

- **错误**：`messages: list`、`tool_calls: list | None`
- **正确**：`messages: list[dict]`、`tool_calls: list[dict] | None`
- **Why**：bare `list` 让元素类型沦为 `Any`，IDE 不补全 dict 的 `.items()/.keys()`，mypy 漏检 `[1, 2, 3]` 这类"是 list 但元素错"的错误
- **决策**：Impedance Matching —— 输入跟 SDK 边界对齐用 `dict`，因为 OpenAI API 契约就吃 `list[dict]`。再细标（如 `list[ChatCompletionMessageParam]`）会泄漏 SDK 内部类型，破坏 DIP

**面试一句话**：
> 我在 LLMProvider Protocol 上输入用 `list[dict]` 对齐 OpenAI SDK 约定，输出用 `LLMResponse` dataclass 给下游静态类型检查 —— 这叫 Impedance Matching，边界两端各用最合适的类型，不要为了"一致"在所有地方都用 dataclass 或都用 dict。

**附:tool_calls 的特例**：tool_calls 是 round-trip 字段（从 LLM 来要回 LLM 去），两端都顶着 SDK 边界，所以也用 `list[dict]`，理由不是"输出该用 dataclass"，而是"两端都是 SDK 边界，留 dict 形式省一次双向转换"。

### 35. 必填参数加默认值 = 签名说谎

- **错误**：`messages: list[dict] | None = None`
- **正确**：`messages: list[dict]`（必填，无默认）
- **Why**：类型签名要诚实反映语义。给默认值 = 告诉调用者"省略是有意义的"。messages 不传 LLM 啥也没收到，加 `None` 是签名层撒谎
- **跟 Day 2 第二轮"文档诚实"原则同脉**

### 36. Client 在 generate 里 new = 浪费连接池

- **错误**：
  ```python
  def generate(self, messages, ...):
      client = OpenAI(api_key=self.api_key, base_url=self.base_url)  # 每次 new
      response = client.chat.completions.create(...)
  ```
- **正确**：
  ```python
  def __init__(self, model, base_url, api_key):
      self.client = OpenAI(api_key=api_key, base_url=base_url)        # __init__ 一次

  def generate(self, messages, ...):
      response = self.client.chat.completions.create(...)              # 复用
  ```
- **Why**：每次 generate 都 new client = TLS/TCP 握手重复，connection pool 失效。10 轮对话至少多 500ms 净浪费，服务端可能识别为异常流量

**关键概念区分**（用户原本以为 client 跟"对话/token"有关）：

| 概念 | 是什么 | 在哪 | 跟 token 关系 |
|---|---|---|---|
| `OpenAI Client` 实例 | Python 端的 HTTP 客户端封装（含 connection pool） | 进程内存 | **无关** |
| 对话上下文 / 会话 | LLM 这次 chat 的历史 | 每次靠 `messages` 参数传 | 决定 token |

**Lifetime Matching 总原则**：依赖的生命周期 ≥ 持有者。能做到 = 时，在 `__init__` 里创建或注入，不要在方法体里临时 new。

**面试一句话**：
> OpenAI Client 是个 HTTP 客户端封装，内部含 connection pool，不是会话状态。会话靠 messages 每次传，API 本身无状态。每次 new client 等于扔掉 connection pool，造成 TLS 握手重复开销。

### 37. 形参回写 self = 污染对象状态

- **错误**：
  ```python
  def __init__(self, model, base_url, api_key):
      self.api_key = api_key                                # 存了
      self.base_url = base_url                              # 存了
      self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
  ```
- **正确**：
  ```python
  def __init__(self, model, base_url, api_key):
      self.client = OpenAI(api_key=api_key, base_url=base_url)  # 直接读形参
  ```
- **Why**：最小作用域 / Locality 原则。`self.X` 是"以后还要用"的存储，不是"现在要用"的便利。形参在函数体内本来就是局部变量，用完即弃

**自检表**：

| 数据 | 用几次 | 在哪用 | 该放哪 |
|---|---|---|---|
| `api_key` | 1 次 | 只在 `__init__` 创建 client | 留在形参 |
| `base_url` | 1 次 | 同上 | 留在形参 |
| `model` | N 次 | `generate` 每次都要 | `self.model` |
| `client` | N 次 | `generate` 每次都要 | `self.client` |

**跟 Day 2 第二轮第 1 条"封装栅栏"是同一脉** —— 都是"最小化"原则的不同投影：
- 封装栅栏 → 对外可见性最小化（`_` 前缀）
- 最小作用域 → 内部寿命最小化（不存形参到 self）

### 38. 抽象层级错位 / 三个空壳类是同一实现的 N 个配置

- **错误**：三个 `Provider` 类（`QwenProvider` / `XiaomiProvider` / `DeepseekProvider`），实现完全一样，只有 `model` / `base_url` / `api_key` 不同
- **正确**：一个 `OpenAICompatibleProvider` 类，使用层 3 次实例化：
  ```python
  qwen     = OpenAICompatibleProvider("qwen-plus",     "https://dashscope...",   os.getenv("DASHSCOPE_API_KEY"))
  deepseek = OpenAICompatibleProvider("deepseek-chat", "https://api.deepseek...", os.getenv("DEEPSEEK_API_KEY"))
  xiaomi   = OpenAICompatibleProvider("xiaomi-model",  "https://xiaomi...",       os.getenv("XIAOMI_API_KEY"))
  ```
- **Why**：当三个"实现"behavior 一致只是 config 不同，**"多类"就是错的抽象层级**。正确形状是"一个类 + 多个实例"

**`LLMProvider` Protocol 还要不要**？要，但用法变了：

| 情况 | Protocol 角色 |
|---|---|
| 三个都是 OpenAI 兼容 | Protocol 暂时只有 1 个实现 `OpenAICompatibleProvider`，**显得多余，但是为下一个真正不同的 provider 准备** |
| 加 Claude（Anthropic 原生 SDK） | `class ClaudeProvider:` —— Protocol 才真正兑现价值 |
| 加 Gemini（Google 原生 SDK） | 同上 |

**心法**：Protocol 是为"真正不同的实现"准备的，不是为"同一实现的不同配置"准备的。

**这条修正了 Phase 5 心得里的一个潜在误解**：Phase 5 写"通过写 XiaomiProvider 看到 QwenProvider 抽象的必要性"，但 Day 3 发现 XiaomiProvider 跟 QwenProvider 是**同一抽象的不同实例**，**不能用作抽象验证**。真正能验证 LLMProvider 抽象的，是加一个跟 OpenAI 不兼容的 provider（如 Claude 原生 SDK）。

**面试一句话**：
> Day 3 修 provider.py 时发现 Xiaomi/Qwen/Deepseek 三个"实现"其实是同一个 OpenAI 兼容客户端的不同配置。这是抽象层级错位 —— Protocol 该为真正不同的实现服务，不该为同一实现的不同配置服务。所以我合成一个 `OpenAICompatibleProvider`，在使用层用三次实例化区分。这是 DRY 跟"抽象层级判断"的一次实战。

### Day 3 延伸坑（已识别，留 Day 4 修）

#### X1. tool_calls 字段类型撒谎（运行时 vs 标注不符）

- **现状**：`tool_calls: list[dict] | None`，但运行时 `tool_calls = message.tool_calls` 塞的是 OpenAI SDK 对象 `list[ChatCompletionMessageToolCall]`
- **修法选项**：
  - (a) `generate` 里加转换：`[tc.model_dump() for tc in message.tool_calls]` ✅ 推荐
  - (b) 改标 `list[ChatCompletionMessageToolCall] | None`（破坏 DIP，不推荐）

#### X2. 公开属性没加 `_` 前缀（原 Day 3 plan 坑 4，未做）

- **现状**：`self.model`、`self.client` 都是公开属性
- **修法**：`self._model`、`self._client`，封装栅栏

#### X3. PEP 8 空格漏处 / `ruff format` 没装

- **现状**：`= None`（等号两边没空格）、`tool_calls:list`（冒号后没空格）等
- **修法**：Day 4 装 `ruff format`，一键扫整个项目
- **原则**：格式化工具化，人脑不该背 PEP 8 空格规则

### Day 3 拉高视角:5 条原则归到 3 个母原则

```
"最小化" 母原则
├─ 对外可见性 → 封装栅栏（`_` 前缀）        ← 留 Day 4（X2）
└─ 内部寿命   → 最小作用域（形参不存 self） ← #37 实战

"边界匹配" 母原则
├─ 类型匹配 → Impedance Matching            ← #34 实战
└─ 寿命匹配 → Lifetime Matching              ← #36 实战

"诚实表达" 母原则
├─ 签名诚实   → 必填参数无默认               ← #35 实战
└─ 抽象层级诚实 → 同行为同配置不该多类       ← #38 实战
```

**面试合体故事点**：
> 我在 stock-assistant 的 LLMProvider 这一层遇到过 5 个真实的设计决策（类型标注、参数默认值、客户端复用、形参作用域、抽象层级判断），每个决策背后对应 1 条可迁移原则。这些原则可以归到 3 个母原则:最小化（可见性 / 寿命）、边界匹配（类型 / 寿命）、诚实表达（签名 / 抽象层级）。我能从单点修复到原则到母原则的完整传导链回溯。

---

## 全局核心原则

### 编码
1. **该传变量的地方别加引号** — Phase 2 #2 / Phase 3 #19 同根问题
2. **可变对象当默认参数用 `None` + 内部创建** — Phase 4 #26
3. **参数名跟 API/外部规范对齐** — Phase 4 #27
4. **函数 ≥ 3 个参数必用关键字传参** — Phase 5 #33
5. **必填参数不该有默认值，签名要诚实反映"能不能省"** — Day 3 #35
6. **形参用完即弃，不要无谓回写 self（最小作用域）** — Day 3 #37
7. **类型标注要紧到元素层（`list[dict]` 而非 `list`）** — Day 3 #34

### 调试
1. **先 print 真实输入**（发给 API 的 messages / 发给函数的参数），再怀疑模型/库 — Phase 3 #24
2. **数据结构搞不清就 print 结构**（`.keys()` / `type()` / `repr()`） — Phase 3 #25 / Phase 2 #14
3. **输出"看起来对"≠ 真的对** — 对不同输入要输出差异化才算对 — Phase 3 #23
4. **AttributeError 先查访问层级，不是猜字段不存在** — Phase 5 #32
5. **500 错误先怀疑自己请求格式，不轻信服务端** — Phase 5 #30

### 架构
1. **避免分支组合爆炸** — 用 dict + 条件 key，不用嵌套 if/else — Phase 4 #28
2. **模块要区分"被运行"和"被导入"** — `if __name__ == "__main__":` 隔离副作用 — Phase 4 #29
3. **模型选型看场景不看 benchmark** — Phase 3 #22
4. **业务层 vs 基础设施层分离** — 关注点分离 — Phase 5 A
5. **Protocol 描述行为契约，ABC 强制名义继承，优先 Protocol** — Phase 5 B
6. **避免 stringly-typed，返回值用 dataclass** — Phase 5 C
7. **身份配置放 `__init__`，业务参数放方法签名** — Phase 5 D
8. **Lifetime Matching：依赖寿命 ≥ 持有者，可用 `=` 时构造器创建** — Day 3 #36
9. **Impedance Matching：边界两端各用最合适类型，SDK 边界用 dict，内部用 dataclass** — Day 3 #34
10. **抽象层级判断：同行为不同配置 → 一个类多实例；Protocol 为真正不同实现服务** — Day 3 #38

### 验证
1. **小数据先跑通再全量** — Phase 2 教训
2. **改完必须有最小闭环自测** — Phase 4 #29
3. **RAG 调优优先级：数据 > 检索 > prompt > 模型** — Phase 3 心得
4. **类型注解是 advisory，关键边界要手动 assert 或用 pydantic** — Phase 5 #31

---

## 附录 A：OpenAI Chat API 请求/响应样本速查

> 本项目所有 LLM 调用都走 OpenAI-compatible API（qwen / xiaomi / openai 皆同）。
> 这份速查是传入 `messages` / `tools` 和拿到 `LLMResponse` 的标准形态，写代码对着翻。

### A.1 messages 参数

**单轮用户问题**：
```python
messages = [
    {"role": "user", "content": "什么是第一类买点?"}
]
```

**带 system prompt（RAG 场景）**：
```python
messages = [
    {"role": "system", "content": "你是缠论专家，只根据资料回答..."},
    {"role": "user", "content": "结合资料回答：什么是第一类买点?"},
]
```

**Agent 多轮（带工具调用来回）**：
```python
messages = [
    {"role": "system", "content": "你是能调工具的 agent..."},
    {"role": "user", "content": "查下贵州茅台最新股价"},

    # LLM 上一轮的回复（它要调工具）
    {"role": "assistant", "content": None, "tool_calls": [...]},

    # 工具执行后喂回去的结果
    {"role": "tool", "tool_call_id": "call_abc123", "content": "贵州茅台最新价 1820 元"},

    # LLM 下一轮基于 tool 结果给最终答案
]
```

**4 个 role 速记**：
- `system`：设定人格/规则（通常只在第一条）
- `user`：用户输入
- `assistant`：LLM 的回复（无论是文字还是要调工具）
- `tool`：工具执行结果（喂给 LLM 看）

### A.2 tools 参数

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "查询股票最新价",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码或名称，如 '贵州茅台' 或 '600519'"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    # 第二个工具...
]
```

格式是 **JSON Schema**，描述"这个工具叫啥、干啥用、要什么参数"。LLM 看着这个 schema 决定调不调、怎么调。

### A.3 LLMResponse 返回体

**Case 1：LLM 直接给文字答案**（RAG / 聊天场景）
```python
LLMResponse(
    content="你好！我很好，谢谢你的关心。😊",
    tool_calls=None
)
```

**Case 2：LLM 要调工具**（Agent 场景）
```python
LLMResponse(
    content=None,    # 注意！调工具时 content 是 None
    tool_calls=[
        ChatCompletionMessageToolCall(
            id="call_abc123",                   # 调用 ID，回传时要对应
            type="function",
            function=Function(
                name="get_stock_price",         # 要调哪个工具
                arguments='{"symbol":"贵州茅台"}' # ⚠️ 这是 JSON 字符串,不是 dict!
            )
        )
    ]
)
```

### A.4 两个关键坑（Agent 场景提前预警）

**坑 1：`content` 和 `tool_calls` 互斥**
要么有文字、要么有工具调用，几乎不会两个都有。Agent 代码用 `if response.tool_calls:` 分流。

**坑 2：`arguments` 是 JSON 字符串不是 dict**
调工具前必须 `json.loads(arguments)` 才能拿到真正的参数。OpenAI SDK 的坑设计，很多新人在这炸。

**典型 Agent 分流代码**：
```python
if response.tool_calls:
    for tc in response.tool_calls:
        name = tc.function.name
        args = json.loads(tc.function.arguments)   # ← 必须 parse
        result = dispatch_tool(name, args)          # 执行
        # 把 result 作为 role=tool 消息喂回去,LLM 下一轮继续
else:
    print(response.content)   # 直接输出文字答案
```
