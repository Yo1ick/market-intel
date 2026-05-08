from openai import OpenAI
from dotenv import load_dotenv
import os


def chat(question: str, context: str = "", temperature: float = 0.3, tools=None) -> str:
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    messages = [
        {
            "role": "system",
            "content": '你是缠论专家。只根据提供的资料回答。资料中的信息可能分散在多段文本中，请综合整理相关片段回答问题。如果资料没有任何相关内容,直接说"资料中未找到",不要编造。',
        },
        {"role": "user", "content": f"结合资料回答问题：\n\n 资料：{context}\n\n问题：{question}"},
    ]

    print("=== 发给 LLM 的 user message ===")
    print(context[:2000])
    print("=== end ===\n")

    kwargs = {
        "model": "qwen3.5-plus",
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = tools

    response = client.chat.completions.create(**kwargs)
    answer = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            answer += content
    return answer


if __name__ == "__main__":
    chat("你好")
