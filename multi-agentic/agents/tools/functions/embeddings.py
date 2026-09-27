from __future__ import annotations

import hashlib
import math
from typing import Sequence

from agents.config import env, env_int


def _hash_embedding(text: str, dimension: int) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < dimension:
        digest = hashlib.sha256(f"{counter}:{text}".encode("utf-8")).digest()
        for byte in digest:
            values.append((byte / 127.5) - 1.0)
            if len(values) == dimension:
                break
        counter += 1

    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Embed texts for Qdrant.

    Set `EMBEDDING_PROVIDER=fake` for offline smoke tests. The default uses
    Google GenAI embeddings and requires `GOOGLE_API_KEY`.
    """
    dimension = env_int("EMBEDDING_DIM", 768)
    provider = (env("EMBEDDING_PROVIDER", "google") or "google").lower()
    if provider == "fake":
        return [_hash_embedding(text, dimension) for text in texts]

    from google import genai

    client = genai.Client(api_key=env("GOOGLE_API_KEY"))
    model = env("EMBEDDING_MODEL", "gemini-embedding-001")
    try:
        response = client.models.embed_content(
            model=model,
            contents=list(texts),
            config={"output_dimensionality": dimension},
        )
    except Exception as error:
        raise RuntimeError(
            f"Embedding request failed for model '{model}'. "
            "Set EMBEDDING_MODEL to an available Google embedding model "
            "or use EMBEDDING_PROVIDER=fake for offline tests."
        ) from error
    embeddings = getattr(response, "embeddings", None)
    if embeddings is None:
        raise RuntimeError("Google embedding response did not include embeddings.")
    return [list(item.values) for item in embeddings]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
