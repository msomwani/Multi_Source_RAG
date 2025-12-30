from openai import OpenAI
from app.config import settings

client=OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_query_variations(query:str,n:int =3):
    prompt=f"""
    rewrite the user's search query in {n} different ways.
    Keep each variation short and natural.
    Do NOT number teh list.
    Only retrun the rewritten quesries,one per line.

    Query:
    {query}
    """

    res=client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"You rewrite queries for information retrieval."},
            {"role":"user","content":prompt},
        ],
        temperature=0.3
    )

    text=res.choices[0].message.content
    return[line.strip() for line in text.split("\n") if line.strip()]

