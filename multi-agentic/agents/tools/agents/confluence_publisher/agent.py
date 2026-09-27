from google.adk.agents.llm_agent import Agent

from pathlib import Path
import os

from agents.tools.functions.publish.prepare import prepare_confluence_page
from agents.tools.functions.publish.result import publish_confluence_page

_PROMPT = Path(__file__).parent / "prompt.md"

_REQUIRED_ENV = ("CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN", "CONFLUENCE_SPACE_KEY", "CONFLUENCE_BASE_URL")

def _validate_configuration() -> None:
    """fail close if required env vars are not set"""
    missing = [var for var in _REQUIRED_ENV if not (env := os.environ.get(var))]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def confluence_publisher_agent() -> Agent:
    """Creates an agent for preparing and publishing Confluence pages."""
    _validate_configuration()
    return Agent(
        model="gemini-3.5-flash",
        name="confluence_publisher_agent",
        description="Prepares and publishes Confluence pages.",
        instruction=_PROMPT.read_text(encoding="utf-8"),
        tools=[prepare_confluence_page, publish_confluence_page],
        mode="single_turn",
    )