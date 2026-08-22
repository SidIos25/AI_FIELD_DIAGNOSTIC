import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".pdf"}
DEFAULT_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))


@dataclass
class DocumentChunk:
    text: str
    metadata: dict


def _chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    chunks = []
    start = 0
    while start < len(cleaned):
        end = min(start + max_chars, len(cleaned))
        chunk = cleaned[start:end]
        if chunk:
            chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(end - overlap, 0)
    return chunks


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages.append(page_text)
    return "\n".join(pages)


def _read_json(path: Path) -> str:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        data = json.load(handle)
    return json.dumps(data, ensure_ascii=True)


def _detect_source_type(path: Path) -> str:
    lower = str(path).lower()
    if "manual" in lower:
        return "manual"
    if "ticket" in lower:
        return "past_ticket"
    if "repair" in lower:
        return "repair_log"
    if "failure" in lower or "known" in lower:
        return "known_failure"
    if "log" in lower:
        return "log"
    return "document"


def load_document_chunks(path: Path) -> list[DocumentChunk]:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return []

    if path.suffix.lower() == ".pdf":
        raw_text = _read_pdf(path)
    elif path.suffix.lower() == ".json":
        raw_text = _read_json(path)
    else:
        raw_text = _read_text_file(path)

    chunks = _chunk_text(
        raw_text,
        max_chars=DEFAULT_CHUNK_SIZE,
        overlap=DEFAULT_CHUNK_OVERLAP
    )
    source_type = _detect_source_type(path)

    return [
        DocumentChunk(
            text=chunk,
            metadata={
                "source": str(path),
                "source_type": source_type
            }
        )
        for chunk in chunks
    ]


def _is_within_root(path: Path, root_dir: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root_dir.resolve(strict=False))
        return True
    except ValueError:
        return False


def iter_document_chunks(root_dir: Path) -> Iterable[DocumentChunk]:
    resolved_root = Path(root_dir).expanduser().resolve(strict=False)
    if not resolved_root.exists() or not resolved_root.is_dir():
        raise ValueError(f"Invalid ingestion root: {resolved_root}")

    for file_path in resolved_root.rglob("*"):
        if file_path.is_symlink():
            raise ValueError(f"Refusing to ingest symlink outside the approved root: {file_path}")
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS and _is_within_root(file_path, resolved_root):
            for chunk in load_document_chunks(file_path):
                yield chunk
