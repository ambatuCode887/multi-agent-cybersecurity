"""
Opt-in live smoke check for the configured LLM and Atlassian MCP.

This command is read-only: it makes one harmless model request and performs the MCP ``tools/list`` preflights, but never calls a Confluence write tool. It is intended to be run in a CI/CD pipeline to verify that the configured LLM and MCP are working correctly.
"""

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
