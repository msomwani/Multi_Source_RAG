def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
):
    if not text:
        return []

    if overlap >= chunk_size:
        overlap = chunk_size // 2

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks
