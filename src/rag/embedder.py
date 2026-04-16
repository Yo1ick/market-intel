from openai import OpenAI
from dotenv import load_dotenv
import os


def embed_texts(texts: list[str]) -> list[list[float]]:
    load_dotenv()

    all_vectors = []
    batch_size = 6
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    for i in range(0,len(texts),batch_size):
        batch = texts[i:i+batch_size]
        response = client.embeddings.create(
            model="text-embedding-v4",
            input=batch
        )

        all_vectors.extend(item.embedding for item in response.data)

    return all_vectors