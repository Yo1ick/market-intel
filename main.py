from src.rag.loader import load_and_split
from src.rag.embedder import embed_texts
from src.rag.store import store_chunks
from src.rag.retriever import retrieve

# chunks = load_and_split("data/docs/file.md")
# print(f'总共{len(chunks)}段')
# # for i, c in enumerate(chunks):
# #       print(f"[{i}] {c['source']}")
#
# texts = [c['text'] for c in chunks]
# vectors = embed_texts(texts)
# print(f'向量数量：{len(vectors)}')
# print(f'向量维度：{len(vectors[0])}')
# store_chunks(chunks,vectors)

results = retrieve("什么是走势中枢")
print(results)