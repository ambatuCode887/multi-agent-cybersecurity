from __future__ import annotations

import hashlib
import csv
import io
import json
import re
import math
import uuid
from pathlib import Path
from typing import Any


from agents.tools.functions.embeddings import embed_texts
from agents.tools.functions.qdrant_store import ensure_collection, upsert_points


TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".csv",
    ".json",
    ".py",
    ".html",
    ".htm",
}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | {".pdf", ".docx"}


def _read_text_file(path: Path) -> str:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="ignore")

    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if path.suffix.lower() == ".docx":
        import docx

        document = docx.Document(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    raise ValueError(f"Unsupported document type: {path.suffix}")


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 180) -> list[str]:
    """Split text into overlapping chunks that are friendly for embeddings."""
    clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not clean:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunks.append(clean[start:end])
        if end == len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def _structure_units(text: str, suffix: str = "") -> list[str]:
    """Create paragraph- or record-sized units before semantic grouping."""
    if suffix == ".csv":
        rows = list(csv.reader(io.StringIO(text)))
        if not rows:
            return []
        header = rows[0]
        return [
            ", ".join(
                f"{column}: {value}"
                for column, value in zip(header, row, strict=True)
            )
            for row in rows[1:]
            if row and len(row) == len(header)
        ]

    if suffix == ".json":
        try:
            value = json.loads(text)
            records = value if isinstance(value, list) else [value]
            return [json.dumps(record, ensure_ascii=True) for record in records]
        except json.JSONDecodeError:
            pass

    clean_lines = [line.strip() for line in text.splitlines()]
    units: list[str] = []
    current: list[str] = []
    for line in clean_lines:
        if not line:
            if current:
                units.append(" ".join(current))
                current = []
            continue
        if current and re.match(r"^#{1,6}\s+", line):
            units.append(" ".join(current))
            current = []
        current.append(line)
    if current:
        units.append(" ".join(current))
    return units


def _cosine_similarity(first: list[float], second: list[float]) -> float:
    dot = sum(left * right for left, right in zip(first, second))
    norm_first = math.sqrt(sum(value * value for value in first))
    norm_second = math.sqrt(sum(value * value for value in second))
    if norm_first == 0 or norm_second == 0:
        return 0.0
    return dot / (norm_first * norm_second)


def hybrid_chunk_text(
    text: str,
    chunk_size: int = 1200,
    overlap: int = 180,
    suffix: str = "",
    semantic_threshold: float = 0.55,
) -> list[str]:
    """Split structured units at semantic boundaries within a size limit."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")

    units = _structure_units(text, suffix=suffix.lower())
    if not units:
        return []
    if len(units) == 1:
        return chunk_text(units[0], chunk_size=chunk_size, overlap=overlap)

    embeddings = embed_texts(units)
    minimum_size = max(1, chunk_size // 3)
    chunks: list[str] = []
    current = ""
    for index, unit in enumerate(units):
        candidate = f"{current}\n\n{unit}" if current else unit
        topic_changed = (
            index > 0
            and current
            and _cosine_similarity(embeddings[index - 1], embeddings[index]) < semantic_threshold
            and len(current) >= minimum_size
        )
        too_large = len(candidate) > chunk_size
        if current and (topic_changed or too_large):
            chunks.append(current)
            carry = current[-overlap:] if overlap else ""
            current = f"{carry}\n\n{unit}" if carry else unit
        else:
            current = candidate

        if len(current) >= chunk_size:
            chunks.append(current[:chunk_size])
            current = current[max(0, chunk_size - overlap):]

    if current:
        chunks.append(current)
    return chunks


def _point_id(source: str, index: int, text: str) -> str:
    raw = f"{source}:{index}:{text}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return str(uuid.UUID(digest[:32]))


def ingest_texts(
    texts: list[str],
    source: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Embed and upsert text chunks into Qdrant."""
    from qdrant_client.models import PointStruct

    ensure_collection()
    metadata = metadata or {}
    vectors = embed_texts(texts)
    points = [
        PointStruct(
            id=_point_id(source, index, text),
            vector=vector,
            payload={
                "text": text,
                "source": source,
                "chunk_index": index,
                **metadata,
            },
        )
        for index, (text, vector) in enumerate(zip(texts, vectors))
    ]
    return upsert_points(points)


def ingest_file_to_qdrant(
    path: str,
    source: str | None = None,
    chunk_size: int = 1200,
    overlap: int = 180,
    semantic: bool = True,
) -> dict[str, Any]:
    """Load a local file, chunk it, embed chunks, and store them in Qdrant."""
    document_path = Path(path).expanduser().resolve()
    text = _read_text_file(document_path)
    chunks = (
        hybrid_chunk_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap,
            suffix=document_path.suffix,
        )
        if semantic
        else chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    )
    if not chunks:
        return {"source": str(document_path), "upserted": 0, "message": "No text found."}
    return ingest_texts(
        texts=chunks,
        source=source or str(document_path),
        metadata={"file_name": document_path.name, "file_path": str(document_path)},
    )
