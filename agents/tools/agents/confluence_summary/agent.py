from google.adk.agents.llm_agent import Agent
from pathlib import Path

_PROMPT = Path(__file__).parent / "prompt.md"


def confluence_summary_agent() -> Agent:
    """Creates an agent for summarizing retrieved evidence into Confluence-ready Markdown."""
    return Agent(
        model="gemini-3.5-flash",
        name="confluence_summary_agent",
        description="Turns retrieved evidence into a concise Confluence-ready summary.",
        instruction=_PROMPT.read_text(encoding="utf-8"),
        mode="single_turn",
    )

