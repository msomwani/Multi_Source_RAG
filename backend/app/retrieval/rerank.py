from sentence_transformers import CrossEncoder

model=CrossEncoder("mixedbread-ai/mxbai-rerank-xsmall-v1")

def rerank(query:str,docs:list[str],top_k:int=5):
    if not docs:
        return[]
    
    pairs=[(query,d) for d in docs]
    scores=model.predict(pairs)

    ranked=sorted(zip(docs,scores),key=lambda x:x[1],reverse=True)
    return[doc for doc, _ in ranked[:top_k]]