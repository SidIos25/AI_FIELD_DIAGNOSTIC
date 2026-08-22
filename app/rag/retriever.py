import os

from app.rag.vector_store import query_text

DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "4"))


def retrieve_context(input_data: dict) -> dict:
    device = input_data.get("device", "unknown device")
    error_code = input_data.get("error_code")
    description = input_data.get("description", "")

    query_parts = [f"Device: {device}"]
    if isinstance(error_code, str) and error_code.strip():
        query_parts.append(f"Error Code: {error_code}")
    query_parts.append(f"Description: {description}")
    query = "\n".join(query_parts)

    results = query_text(query, n_results=DEFAULT_TOP_K)
    docs = results.get("documents", [[]])[0] if results else []
    metas = results.get("metadatas", [[]])[0] if results else []

    context_parts = []
    sources = []
    for doc, meta in zip(docs, metas):
        source_type = meta.get("source_type", "document") if meta else "document"
        source = meta.get("source", "unknown") if meta else "unknown"
        sources.append(f"{source_type}: {source}")
        context_parts.append(f"[{source_type}] {doc}")

    return {
        "context": "\n\n".join(context_parts),
        "sources": sources
    }
