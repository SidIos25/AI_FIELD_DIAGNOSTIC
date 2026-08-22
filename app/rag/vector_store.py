import os
import chromadb

from app.rag.embeddings import embed_texts

DEFAULT_STORE_DIR = os.getenv("RAG_STORE_DIR", "rag_store")
COLLECTION_NAME = os.getenv("RAG_COLLECTION", "field_diagnostics")
DEFAULT_QUERY_INCLUDE = os.getenv("RAG_QUERY_INCLUDE", "documents,metadatas")

_CLIENT = None
_COLLECTION = None


def _get_collection():
    global _CLIENT, _COLLECTION
    if _COLLECTION is not None:
        return _COLLECTION
    if _CLIENT is None:
        _CLIENT = chromadb.PersistentClient(path=DEFAULT_STORE_DIR)
    _COLLECTION = _CLIENT.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    return _COLLECTION


def upsert_texts(
    texts: list[str],
    metadatas: list[dict],
    ids: list[str]
) -> None:
    collection = _get_collection()
    embeddings = embed_texts(texts)
    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
        embeddings=embeddings
    )


def query_text(query: str, n_results: int = 4) -> dict:
    collection = _get_collection()
    embeddings = embed_texts([query])
    include = [item.strip() for item in DEFAULT_QUERY_INCLUDE.split(",") if item.strip()]
    if not include:
        include = ["documents", "metadatas"]
    return collection.query(
        query_embeddings=embeddings,
        n_results=n_results,
        include=include
    )
