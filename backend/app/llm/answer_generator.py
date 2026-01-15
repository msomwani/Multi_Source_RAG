from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# --------------------------------------------------
# Shared helper
# --------------------------------------------------
def _normalize_contexts(contexts):
    normalized = []
    for c in contexts:
        if isinstance(c, str):
            normalized.append(c)
        elif isinstance(c, dict) and "text" in c:
            normalized.append(c["text"])
    return normalized


# --------------------------------------------------
# NON-STREAMING (used by /query)
# --------------------------------------------------
def generate_answer_with_history(query, contexts, history):
    contexts = _normalize_contexts(contexts)
    context_text = "\n\n".join(contexts)

    messages = [
        {
            "role": "system",
            "content": "You are a helpful RAG assistant. Use only the provided context."
        },
        {
            "role": "system",
            "content": f"Context:\n{context_text}"
        }
    ]

    for role, content in history:
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": query})

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2,
    )

    return res.choices[0].message.content


# --------------------------------------------------
# STREAMING (used by /query/stream)
# --------------------------------------------------
def stream_answer(query, contexts, history):
    contexts = _normalize_contexts(contexts)
    context_text = "\n\n".join(contexts)

    messages = [
        {
            "role": "system",
            "content": "You are a helpful RAG assistant. Use only the provided context."
        },
        {
            "role": "system",
            "content": f"Context:\n{context_text}"
        }
    ]

    for role, content in history:
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": query})

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
