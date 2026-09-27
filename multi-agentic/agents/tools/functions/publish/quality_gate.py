from __future__ import annotations

from typing import Any


def validate_publish_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the minimum fields needed before publishing to Confluence."""
    errors = []
    if not str(payload.get("title", "")).strip():
        errors.append("Missing title.")
    if not str(payload.get("space_key", "")).strip():
        errors.append("Missing Confluence space key.")
    body = payload.get("body")
    if not body:
        errors.append("Missing body.")
    elif payload.get("body_format") == "atlas_doc_format" and not body.get("content"):
        errors.append("ADF body must contain at least one content node.")
    if payload.get("body_format") not in {"storage", "atlas_doc_format"}:
        errors.append("body_format must be 'storage' or 'atlas_doc_format'.")

    return {"ok": not errors, "errors": errors, "payload": payload}
