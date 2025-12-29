from .chroma_client import client

collection=client.get_or_create_collection("documents")

def add_chunks(doc_id,chunks,embeddings,metadatas):
    collection.add(
        ids=[f"{doc_id}_{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,

    )

def search(query_embedding,k=5):
    return collection.query(query_embeddings=[query_embedding],n_results=k)