from src.rag.loader import load_and_split

chunks = load_and_split("data/docs/file.md")
print(f'总共{len(chunks)}段')
for i,c in enumerate(chunks[:5]):
    print(f"[{i}] {c['source']} | {len(c['text'])}字")
