from rank_bm25 import BM25Okapi
from app.vectorstore.store import collection
from app.llm.embeddings import embed
import numpy as np
import re

def simple_tokenize(text:str):
    return re.findall(r"w+",text.lower())

def build_bm25_index():
    #pulling docs form chroma
    docs=collection.get()["documents"]
    tokenized=[simple_tokenize(d) for d in docs]
    return BM25Okapi(tokenized)

bm25=build_bm25_index()

def bm25_search(query:str,k=5):
    tokens=simple_tokenize(query)
    scores=bm25.get_scores(tokens)

    #sorting top k indices
    topk=np.argsort(scores)[::-1][:k]
    docs=collection.get()["documents"]

    return [(docs[i],scores[i]) for i in topk]

def dense_search(query:str,k=5):
    if collection.count()==0:
        return []
    vecs=embed([query])
    q_vec=vecs[0]
    res=collection.query(query_embeddings=[q_vec],n_results=k)

    return list(zip(res["documents"][0],res["distances"][0]))

def hybrid_search(query:str,k=5,alpha=0.5):
    """
    alpha=weight of dense similarity
    (1-alpha)=weight of bm25 score
    """
    bm25_res=bm25_search(query,k*2)
    dense_res=dense_search(query,k*2)

    scores={}

    #normalizing BM25
    bm25_max=max([s for _,s in bm25_res]) or 1
    for doc,s in bm25_res:
        scores.setdefault(doc,0)
        scores[doc]+=(1-alpha)*(s/bm25_max)

    #normalizing dense
    dense_max=max([s for _,s in dense_res]) or 1
    for doc,s in dense_res:
        scores.setdefault(doc,0)
        scores[doc]+=alpha*(1-s/dense_max)

    ranked=sorted(scores.items(),key=lambda x:x[1],reverse=True)

    return[doc for doc, _ in ranked[:k]]