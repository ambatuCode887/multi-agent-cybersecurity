from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from agents.config import csv_env, env, load_environment
from agents.tools.agents.confluence_publisher.agent import confluence_publisher_agent
from agents.tools.agents.confluence_summary.agent import confluence_summary_agent
from agents.tools.agents.retrieval.agent import retrieval_agent
from agents.tools.functions.ingest.documents import ingest_file_to_qdrant
from agents.tools.functions.publish.prepare import prepare_confluence_page
from agents.tools.functions.publish.result import publish_confluence_page
from agents.tools.functions.retrieve.credential_stuffing import retrieve_knowledge
from pathlib import Path

load_environment()

def _optional_mcp_tools():
    """Attach Confluence MCP tools when env config is present."""
    mcp_url = env("CONFLUENCE_MCP_URL")
    mcp_command = env("CONFLUENCE_MCP_COMMAND")
    if not mcp_url and not mcp_command:
        return []

    from mcp import StdioServerParameters

    from google.adk.tools.mcp_tool.mcp_session_manager import (
        StdioConnectionParams,
        StreamableHTTPConnectionParams,
    )
    from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

    if mcp_url:
        return [
            McpToolset(
                connection_params=StreamableHTTPConnectionParams(url=mcp_url),
                tool_name_prefix="mcp_confluence",
            )
        ]

    return [
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=mcp_command,
                    args=csv_env("CONFLUENCE_MCP_ARGS"),
                )
            ),
            tool_name_prefix="mcp_confluence",
        )
    ]


root_agent = Agent(
    model="gemini-3.5-flash",
    name="root_agent",
    description="Multi-agent RAG assistant with Qdrant retrieval and Confluence publishing.",
    instruction=(
        "You coordinate a multi-agent RAG workflow. Use ingestion tools to add "
        "documents to Qdrant, retrieval tools to ground answers, summary agents "
        "to prepare Confluence-ready Markdown, and publisher tools only after "
        "running a dry run unless the user explicitly asks to publish."
    ),
    tools=[
        ingest_file_to_qdrant,
        retrieve_knowledge,
        prepare_confluence_page,
        publish_confluence_page,
        *_optional_mcp_tools(),
    ],
    sub_agents=[
        retrieval_agent(),
        confluence_summary_agent(),
        confluence_publisher_agent(),
    ],
)
