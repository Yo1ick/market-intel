import chromadb
from src.rag.embedder import embed_texts


def retrieve(question: str, top_k: int = 3) -> list[dict]:
    client = chromadb.PersistentClient(path="data/chroma")  # 持久化存储到本地
    collection = client.get_or_create_collection("chanlun")  # 查看集合

    question_vector = embed_texts([question])
    results = collection.query(query_embeddings=question_vector, n_results=top_k)

    return results
