from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def _normalize_contexts(contexts):
    """
    Accepts:
    - list[str]
    - list[dict] with {"text": "..."}
    Returns:
    - list[str]
    """
    normalized = []
    for c in contexts:
        if isinstance(c, str):
            normalized.append(c)
        elif isinstance(c, dict) and "text" in c:
            normalized.append(c["text"])
    return normalized


def generate_answer(query, contexts):
    contexts = _normalize_contexts(contexts)

    context_text = "\n\n".join(contexts)

    prompt = f"""
Answer the question based only on the context.

Context:
{context_text}

Question:
{query}
"""

    res = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return res.output_text


def generate_answer_with_history(query, contexts, history):
    contexts = _normalize_contexts(contexts)

    context_text = "\n\n".join(contexts)

    messages = [
        {
            "role": "system",
            "content": "You are a helpful RAG assistant. Use only the provided context to answer."
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
        temperature=0.2
    )

    return res.choices[0].message.content
