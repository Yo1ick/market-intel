from openai import OpenAI
from dotenv import load_dotenv
import os


def chat(question:str, context:str) -> str:
    load_dotenv()

    client = OpenAI(
        api_key = os.getenv("DASHSCOPE_CODING_API_KEY") ,
        base_url="https://coding.dashscope.aliyuncs.com/v1"
    )
    if context:
        messages = [
            {"role": "system", "content": "你是缠论专家，根据资料回答问题"},
            {"role": "user", "content": f"结合资料回答问题：\n\n 资料：{context}\n\n问题：{question}" },
        ]
    else:
        messages = [
            {"role": "system", "content": "你是缠论专家，根据资料回答问题"},
            {"role": "user", "content": question},
        ]

    response = client.chat.completions.create(
            model = "qwen3.6-plus",
            messages = messages,
            stream = True
        )
    answer = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            print(content, end="", flush=True)
            answer += content
    return answer