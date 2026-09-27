from __future__ import annotations

from typing import Any

from agents.config import env
from agents.tools.functions.publish.adf import markdown_to_adf, markdown_to_storage
from agents.tools.functions.publish.quality_gate import validate_publish_payload


def prepare_confluence_page(
    title: str,
    markdown: str,
    space_key: str | None = None,
    parent_id: str | None = None,
    body_format: str = "storage",
) -> dict[str, Any]:
    """Prepare and validate a Confluence page payload."""
    resolved_space = space_key or env("CONFLUENCE_SPACE_KEY", "")
    resolved_parent = parent_id or env("CONFLUENCE_PARENT_ID", "")
    if body_format not in {"storage", "atlas_doc_format"}:
        return {
            "ok": False,
            "errors": ["body_format must be 'storage' or 'atlas_doc_format'."],
            "payload": {"title": title, "space_key": resolved_space, "parent_id": resolved_parent or None},
        }
    body: str | dict[str, Any]
    if body_format == "atlas_doc_format":
        body = markdown_to_adf(markdown)
    else:
        body = markdown_to_storage(markdown)

    payload = {
        "title": title,
        "space_key": resolved_space,
        "parent_id": resolved_parent or None,
        "body_format": body_format,
        "body": body,
    }
    return validate_publish_payload(payload)
