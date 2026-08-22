import hashlib
import os
from pathlib import Path

from app.rag.loaders import iter_document_chunks
from app.rag.vector_store import upsert_texts

DEFAULT_DATA_DIR = (Path(__file__).resolve().parents[1] / "rag_data").resolve()


def _get_approved_data_root() -> Path:
    configured_root = os.getenv("RAG_DATA_DIR")
    if configured_root:
        return Path(configured_root).expanduser().resolve(strict=False)
    return DEFAULT_DATA_DIR


def _chunk_id(path: str, index: int) -> str:
    raw = f"{path}:{index}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()


def _resolve_ingest_root(data_dir: str | Path | None = None) -> Path:
    approved_root = _get_approved_data_root()
    candidate = Path(data_dir).expanduser().resolve(strict=False) if data_dir is not None else approved_root
    if not candidate.exists():
        raise FileNotFoundError(f"Approved ingestion root does not exist: {candidate}")
    if not candidate.is_dir():
        raise ValueError(f"Approved ingestion root is not a directory: {candidate}")
    try:
        candidate.relative_to(approved_root)
    except ValueError as exc:
        raise ValueError(f"Refusing to ingest outside the approved document root: {approved_root}") from exc
    return candidate


def ingest_directory(data_dir: str | Path | None = None) -> dict:
    root = _resolve_ingest_root(data_dir)

    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    chunk_index = 0
    for chunk in iter_document_chunks(root):
        if not chunk.text.strip():
            continue
        texts.append(chunk.text)
        metadatas.append(chunk.metadata)
        ids.append(_chunk_id(chunk.metadata.get("source", "unknown"), chunk_index))
        chunk_index += 1

        if len(texts) >= 100:
            upsert_texts(texts, metadatas, ids)
            texts, metadatas, ids = [], [], []

    if texts:
        upsert_texts(texts, metadatas, ids)

    return {"ingested": chunk_index, "data_dir": str(root)}


if __name__ == "__main__":
    result = ingest_directory()
    print(result)
