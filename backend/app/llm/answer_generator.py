from openai import OpenAI
from app.config import settings

client=OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_answer(query,contexts):
    context_text="\n\n".join(contexts)

    prompt=f"""
    Answer the question based only on the context.

    Context:
    {context_text}

    Question:
    {query}
    """

    res=client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return res.output_text
