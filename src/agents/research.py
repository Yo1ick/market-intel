"""ResearchAgent — 单 agent + function calling 投资研究助手。"""
import json
from src.llm.provider import LLMProvider
from src.memory.working import WorkingMemory
from src.agents.tools.knowledge import SCHEMA as KNOWLEDGE_SCHEMA, search_knowledge

SYSTEM_PROMPT = """你是一位专业的投资研究助手。

职责:
- 基于研报知识库回答用户关于股票、行业、公司业绩的问题
- 引用研报来源(机构 + 日期),增加可信度
- 不确定时如实说明,不编造数据

工具:
- search_knowledge:搜索研报知识库,**优先调用此工具**获取真实数据再回答

回答规则:
- **必须引用至少 1 个来源机构和日期**(从 search_knowledge 返回的 [source]
  中提取),格式:"根据【中邮证券】(2026-04-28)..."。无引用的回答直接重写,**这是硬性要求,不可省略**
- 简洁,有数据支撑
- 避免投资建议(不说"建议买入"等)
"""

TOOLS = {
    "search_knowledge": search_knowledge,
}

TOOL_SCHEMAS = [KNOWLEDGE_SCHEMA]

MAX_ITERS = 5

class ResearchAgent:
    """单 agent + function calling 投研助手核心。"""

    def __init__(self, llm:LLMProvider, working_memory:WorkingMemory):
        """
        Args:
           llm: 主对话 LLM(qwen-plus 等,要支持 function calling)
           working_memory: 会话记忆
        """
        self._llm = llm
        self._wm = working_memory

    def run(self, query: str) -> str:
        """
        处理用户 query,跑 agent loop,返回最终回答。

        Args:
            query: 用户问题

        Returns:
            最终 assistant content(string)
        """

        self._wm.add_message({"role": "user", "content": query})

        for iteration in range(MAX_ITERS):
            messages = [{"role": "system","content": SYSTEM_PROMPT}] + self._wm.get_messages()

            response = self._llm.generate(
                messages=messages,
                tools=TOOL_SCHEMAS,
            )

            assistant_msg = {"role": "assistant", "content": response.content or ""}
            if response.tool_calls:
                assistant_msg["tool_calls"] = response.tool_calls
            self._wm.add_message(assistant_msg)

            if not response.tool_calls:
                return response.content or ""

            for tc in response.tool_calls:
                tool_name = tc["function"]["name"]
                tool_args = json.loads(tc["function"]["arguments"])

                if tool_name in TOOLS:
                    try:
                        result = TOOLS[tool_name](**tool_args)
                    except Exception as e:
                        result = f"工具执行失败: {e}"
                else:
                    result = f"未知工具: {tool_name}"

                self._wm.add_message({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(result),
                })

        return "达到最大迭代次数,未能给出最终答案。"
