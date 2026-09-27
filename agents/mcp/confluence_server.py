from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # pyright: ignore[reportMissingImports]

from agents.tools.functions.publish.result import publish_confluence_page


mcp = FastMCP("confluence-publisher")


@mcp.tool()
def publish_page(
    title: str,
    markdown: str,
    space_key: str | None = None,
    parent_id: str | None = None,
    dry_run: bool = True,
) -> dict:
    """Publish or dry-run a Confluence page from Markdown."""
    return publish_confluence_page(
        title=title,
        markdown=markdown,
        space_key=space_key,
        parent_id=parent_id,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    mcp.run()
