"""Smoke-check local chunking and Confluence publish-payload preparation."""

from __future__ import annotations

from agents.config import load_environment
from agents.tools.functions.ingest.documents import chunk_text
from agents.tools.functions.publish.prepare import prepare_confluence_page


def main() -> None:
    load_environment()
    chunks = chunk_text("Credential stuffing is an attack using leaked passwords." * 20)
    assert chunks, "chunk_text should produce chunks"

    prepared = prepare_confluence_page(
        title="Smoke Test",
        markdown="# Smoke Test\n\n- Ingestion chunks generated\n- Publish payload prepared",
        space_key="TEST",
    )
    assert prepared["ok"], prepared
    print("Smoke checks passed.")


if __name__ == "__main__":
    main()
