"""
EXPERIMENTAL MODULE
Used only for multi-query retrieval experiments.
Not part of the production pipeline.
"""

from openai import OpenAI
from app.config import settings
import logging

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def generate_query_variations(query: str, n: int = 3):
    """
    Generate query rewrites for retrieval.
    FAIL-SAFE: returns [] if LLM fails.
    """
    prompt = f"""
    Rewrite the user's search query in {n} different ways.
    Keep each variation short and natural.
    Do NOT number the list.
    Only return the rewritten queries, one per line.

    Query:
    {query}
    """

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You rewrite queries for information retrieval."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        text = res.choices[0].message.content or ""
        return [line.strip() for line in text.split("\n") if line.strip()]

    except Exception as e:
        logging.warning(f"[multiquery] LLM failed, fallback to single query: {e}")
        return []  # ✅ hard fallback
