def load_and_split(file_path:str) -> list:

    with open(file_path,'r',encoding="UTF-8") as f:
        text = f.read()

    parts = text.split('\n---\n')

    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        chunks.append({
            "text":part,
            "source": part.split('\n')[0][:30],
        })

    return  chunks



