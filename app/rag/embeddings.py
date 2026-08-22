import os
from functools import lru_cache

from openai import OpenAI

from app.models import get_provider_timeout_seconds

DEFAULT_EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "text-embedding-3-small")

_CLIENT: OpenAI | None = None


def _get_client() -> OpenAI:
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT
    api_key = os.getenv("OPENAI_KEY", "")
    timeout_seconds = get_provider_timeout_seconds()
    _CLIENT = OpenAI(api_key=api_key, timeout=timeout_seconds)
    return _CLIENT


@lru_cache(maxsize=512)
def _embed_one(text: str) -> list[float]:
    client = _get_client()
    response = client.embeddings.create(model=DEFAULT_EMBED_MODEL, input=[text], timeout=get_provider_timeout_seconds())
    return response.data[0].embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if len(texts) == 1:
        return [_embed_one(texts[0])]
    client = _get_client()
    response = client.embeddings.create(model=DEFAULT_EMBED_MODEL, input=texts, timeout=get_provider_timeout_seconds())
    return [item.embedding for item in response.data]
