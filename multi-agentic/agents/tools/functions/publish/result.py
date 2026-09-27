from __future__ import annotations

import base64
from typing import Any

import httpx

from agents.config import env, missing
from agents.tools.functions.publish.prepare import prepare_confluence_page


def _auth_header(email: str, token: str) -> str:
    raw = f"{email}:{token}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def publish_confluence_page(
    title: str,
    markdown: str,
    space_key: str | None = None,
    parent_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Publish Markdown to Confluence.

    Defaults to `dry_run=True` so an agent can preview safely. Set dry_run to
    false only after the prepared payload looks correct.
    """
    prepared = prepare_confluence_page(
        title=title,
        markdown=markdown,
        space_key=space_key,
        parent_id=parent_id,
        body_format="storage",
    )
    if not prepared["ok"]:
        return prepared

    if dry_run:
        return {"ok": True, "dry_run": True, "payload": prepared["payload"]}

    missing_vars = missing(["CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"])
    if missing_vars:
        return {"ok": False, "errors": [f"Missing env vars: {', '.join(missing_vars)}"]}

    base_url = (env("CONFLUENCE_BASE_URL") or "").rstrip("/")
    email = env("CONFLUENCE_EMAIL") or ""
    token = env("CONFLUENCE_API_TOKEN") or ""
    payload = prepared["payload"]

    request_body: dict[str, Any] = {
        "type": "page",
        "title": payload["title"],
        "space": {"key": payload["space_key"]},
        "body": {
            "storage": {
                "value": payload["body"],
                "representation": "storage",
            }
        },
    }
    if payload.get("parent_id"):
        request_body["ancestors"] = [{"id": payload["parent_id"]}]

    try:
        response = httpx.post(
            f"{base_url}/rest/api/content",
            headers={
                "Authorization": _auth_header(email, token),
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=request_body,
            timeout=30,
        )
    except httpx.HTTPError as error:
        return {"ok": False, "errors": [f"Confluence request failed: {error}"]}
    if response.status_code >= 400:
        return {
            "ok": False,
            "status_code": response.status_code,
            "error": response.text,
        }
    data = response.json()
    return {
        "ok": True,
        "id": data.get("id"),
        "title": data.get("title"),
        "url": f"{base_url}{data.get('_links', {}).get('webui', '')}",
    }
