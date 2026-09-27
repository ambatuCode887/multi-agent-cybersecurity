from __future__ import annotations

import html
import re


_INLINE_PATTERN = re.compile(
    r"(\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|__([^_]+)__|`([^`]+)`|\*([^*]+)\*|_([^_]+)_)"
)


def _inline_storage(text: str) -> str:
    parts: list[str] = []
    position = 0
    for match in _INLINE_PATTERN.finditer(text):
        parts.append(html.escape(text[position:match.start()]))
        if match.group(2) is not None:
            label = html.escape(match.group(2))
            url = html.escape(match.group(3), quote=True)
            parts.append(f'<a href="{url}">{label}</a>')
        elif match.group(4) or match.group(5):
            parts.append(f"<strong>{html.escape(match.group(4) or match.group(5))}</strong>")
        elif match.group(6):
            parts.append(f"<code>{html.escape(match.group(6))}</code>")
        else:
            parts.append(f"<em>{html.escape(match.group(7) or match.group(8))}</em>")
        position = match.end()
    parts.append(html.escape(text[position:]))
    return "".join(parts)


def _inline_adf(text: str) -> list[dict]:
    nodes: list[dict] = []
    position = 0
    for match in _INLINE_PATTERN.finditer(text):
        if match.start() > position:
            nodes.append({"type": "text", "text": text[position:match.start()]})
        if match.group(2) is not None:
            nodes.append(
                {
                    "type": "text",
                    "text": match.group(2),
                    "marks": [{"type": "link", "attrs": {"href": match.group(3)}}],
                }
            )
        elif match.group(4) or match.group(5):
            nodes.append(
                {
                    "type": "text",
                    "text": match.group(4) or match.group(5),
                    "marks": [{"type": "strong"}],
                }
            )
        elif match.group(6):
            nodes.append(
                {"type": "text", "text": match.group(6), "marks": [{"type": "code"}]}
            )
        else:
            nodes.append(
                {
                    "type": "text",
                    "text": match.group(7) or match.group(8),
                    "marks": [{"type": "em"}],
                }
            )
        position = match.end()
    if position < len(text):
        nodes.append({"type": "text", "text": text[position:]})
    return nodes or [{"type": "text", "text": ""}]


def markdown_to_storage(markdown: str) -> str:
    """Convert simple Markdown into Confluence storage-format XHTML."""
    blocks: list[str] = []
    in_list = False
    in_code = False
    code_lines: list[str] = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            blocks.append("</ul>")
            in_list = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            if in_code:
                blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = []
                in_code = False
            else:
                close_list()
                in_code = True
            continue
        if in_code:
            code_lines.append(raw_line)
            continue
        if not line:
            close_list()
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            close_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{_inline_storage(heading.group(2))}</h{level}>")
        elif line.startswith(("- ", "* ")):
            if not in_list:
                blocks.append("<ul>")
                in_list = True
            blocks.append(f"<li><p>{_inline_storage(line[2:])}</p></li>")
        else:
            close_list()
            blocks.append(f"<p>{_inline_storage(line)}</p>")

    if in_code:
        blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    close_list()
    return "\n".join(blocks)


def markdown_to_adf(markdown: str) -> dict:
    """Create a minimal Atlassian Document Format document."""
    content = []
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        index += 1
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("```"):
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            content.append({"type": "codeBlock", "content": [{"type": "text", "text": "\n".join(code_lines)}]})
        elif re.match(r"^#{1,6}\s+", stripped):
            match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            assert match is not None
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": len(match.group(1))},
                    "content": _inline_adf(match.group(2)),
                }
            )
        elif stripped.startswith(("- ", "* ")):
            items = []
            while index <= len(lines):
                item_line = stripped if not items else lines[index - 1].strip()
                if not item_line.startswith(("- ", "* ")):
                    break
                items.append({"type": "listItem", "content": [{"type": "paragraph", "content": _inline_adf(item_line[2:])}]})
                if index >= len(lines) or not lines[index].strip().startswith(("- ", "* ")):
                    break
                index += 1
            content.append({"type": "bulletList", "content": items})
        else:
            content.append(
                {
                    "type": "paragraph",
                    "content": _inline_adf(stripped),
                }
            )
    return {"type": "doc", "version": 1, "content": content}
