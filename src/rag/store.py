import chromadb

def store_chunks(chunks, vectors):

    client = chromadb.PersistentClient(path='data/chroma') # 持久化存储到本地
    collection = client.get_or_create_collection('chanlun')# 创建集合

    #存数据
    for i,chunk in enumerate(chunks):
        collection.add(
            ids=[str(i)],           # 每条数据的唯一ID
            documents = [chunk['text']],    #原文
            embeddings=[vectors[i]],         #向量
            metadatas=[{"source": chunk["source"]}]             #元数据
        )

    print(f"已存入 {collection.count()} 条数据")
