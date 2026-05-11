"""Knowledge search tool — agent 调用此 tool 检索研报 KB。"""
from src.knowledge.store import Knowledge


SCHEMA  ={
    "type": "function",
    "function": {
        "name": "search_knowledge",
        "description": "在研报知识库中检索相关内容。当用户询问股票业绩、机构评级、行业分析等需要参考研报数据时,优先调用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                "type": "string",
                "description": "检索关键词,例如 '茅台 2026Q1 业绩'",
            },
                "top_k":{
                "type": "integer",
                "description": "返回 top N 条结果,默认 3",
                "default": 3,
            }
            },
        "required": ["query"],
        },

    },
}


# Lazy 单例 Knowledge 实例(避免每次 tool 调用都新建 chromadb 连接)
_knowledge : Knowledge | None = None


def _get_knowledge() -> Knowledge:
    global _knowledge
    if _knowledge is None:
        _knowledge = Knowledge()
    return _knowledge



def search_knowledge(query: str, top_k: int = 3) -> str:
    """
        Tool 实现:检索 KB,返回纯文本结果(LLM 易消化)。

        Returns:
            多行字符串,每行 = "[source] text..."
    """
    results = _get_knowledge().retrieve(query, top_k=top_k)
    if not results:
        return "知识库无相关结果。"

    lines = []
    for r in results:
        lines.append(f"[{r['source']}] {r['text']}")
    return "\n".join(lines)