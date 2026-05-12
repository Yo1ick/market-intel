"""main.py — Stock Assistant CLI 入口.

用法:
    uv run python main.py "茅台 2026Q1 业绩怎么样?"
"""

import sys
import os

from dotenv import load_dotenv
from src.llm.provider import LLMProvider, OpenAICompatibleProvider
from src.memory.working import WorkingMemory
from src.agents.research import ResearchAgent

def main():
    """CLI 入口:解析命令行 query,跑 agent,打印结果。"""

    load_dotenv()

    if len(sys.argv) < 2:
        print('Usage: python main.py "your query"')
        print('Example: python main.py "茅台 2026Q1 业绩怎么样？"')
        sys.exit(1)

    query = sys.argv[1]

    api_key = os.getenv("STOCK_ASSISTANT_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("Error: 未找到 API key(STOCK_ASSISTANT_API_KEY 或 DASHSCOPE_API_KEY)")
        sys.exit(1)

    llm = OpenAICompatibleProvider(
        model=os.getenv("STOCK_ASSISTANT_MODEL", "qwen-plus"),
        base_url=os.getenv(
            "STOCK_ASSISTANT_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
        api_key=api_key,
    )


    wm = WorkingMemory(llm=llm)
    agent = ResearchAgent(llm=llm, working_memory=wm)

    print(f"问题: {query}")
    print("=" * 60)
    answer = agent.run(query)
    print(answer)
    print("=" * 60)
    print(f"对话轮次: {len(wm.get_messages())}")


if __name__ == "__main__":
    main()
