import chromadb
import hashlib
from src.knowledge.embedder import embed_texts



class Knowledge:
    """研报知识库,封装 ingest 和 retrieve。供 agent tool 调用。"""

    def __init__(self, collection_name: str = "research", persist_path: str = "data/chroma"):
        self._client = chromadb.PersistentClient(path=persist_path)
        self._collection = self._client.get_or_create_collection(collection_name)

    def ingest_chunks(self, chunks: list[dict]) -> int:
        """
        Args:
            chunks: list of {"text": str, "source": str}
        Returns:
            实际入库数
        """
        if not chunks:
            return 0

        texts = [chunk["text"] for chunk in chunks]
        vectors = embed_texts(texts)

        self._collection.upsert(
            ids=[
                f"{c['source']}#{hashlib.md5(c['text'].encode('utf-8')).hexdigest()[:8]}"
                for c in chunks
            ],
            documents=texts,
            embeddings=vectors,
            metadatas=[{"source": c["source"]} for c in chunks],
        )

        return len(chunks)

    def retrieve(self, question: str, top_k: int = 3) -> list[dict]:
        """
        Returns:
            list of {"text": str, "source": str, "distance": float}
            distance 越小越相关
        """
        question_vector = embed_texts([question])
        results = self._collection.query(
            query_embeddings=question_vector,
            n_results=top_k,
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            {
                "text": document,
                "source": metadata["source"],
                "distance": distance,
            }
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]

