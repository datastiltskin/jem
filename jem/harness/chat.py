"""Chat harness — Anthropic API with JEM tools."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Optional

from mcp.server import call_tool

JEM_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_PROMPT_PATH = JEM_ROOT / "harness" / "system_prompt.txt"

LEGAL_ADVICE_PHRASES = (
    "legal advice",
    "should i sue",
    "should i appeal",
    "will i win",
    "what should i do",
)


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text()


def is_legal_advice_query(message: str) -> bool:
    lowered = message.lower()
    return any(p in lowered for p in LEGAL_ADVICE_PHRASES)


def decline_message() -> str:
    return (
        "JEM provides structural map data only, not legal advice or case outcome prediction. "
        "For advice on your specific situation, please consult a qualified advocate."
    )


TOOL_DEFINITIONS = [
    {
        "name": "get_entity",
        "description": "Get entity by id with data_quality flags",
        "input_schema": {
            "type": "object",
            "properties": {"entity_id": {"type": "string"}},
            "required": ["entity_id"],
        },
    },
    {
        "name": "search_entities",
        "description": "Search entities",
        "input_schema": {
            "type": "object",
            "properties": {"q": {"type": "string"}},
        },
    },
    {
        "name": "get_relationships",
        "description": "Get relationships for an entity",
        "input_schema": {
            "type": "object",
            "properties": {"entity_id": {"type": "string"}},
        },
    },
    {
        "name": "get_structural_gaps",
        "description": "Get structural gaps",
        "input_schema": {
            "type": "object",
            "properties": {"entity_id": {"type": "string"}},
        },
    },
]


def execute_tool(name: str, arguments: dict) -> str:
    result = call_tool(name, arguments)
    return json.dumps(result, ensure_ascii=False)


def chat(
    message: str,
    *,
    history: Optional[list[dict]] = None,
    client: Any = None,
    create_message: Optional[Callable] = None,
) -> dict:
    """Process a chat message. Returns {reply, tools_used, declined}."""
    if is_legal_advice_query(message):
        return {"reply": decline_message(), "tools_used": [], "declined": True}

    system = load_system_prompt()
    messages = list(history or [])
    messages.append({"role": "user", "content": message})

    tools_used: list[str] = []

    if create_message is not None:
        raw = create_message(system=system, user=message, tools=TOOL_DEFINITIONS)
        if isinstance(raw, dict) and raw.get("tool_calls"):
            parts = []
            for tc in raw["tool_calls"]:
                tools_used.append(tc["name"])
                tool_result = execute_tool(tc["name"], tc.get("arguments", {}))
                parts.append(f"[{tc['name']}]: {tool_result}")
            reply = raw.get("text", "") + "\n" + "\n".join(parts)
        else:
            reply = raw if isinstance(raw, str) else raw.get("text", str(raw))
        return {"reply": reply.strip(), "tools_used": tools_used, "declined": False}

    import anthropic

    api = client or anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    anthropic_tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in TOOL_DEFINITIONS
    ]

    response = api.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=messages,
        tools=anthropic_tools,
    )

    reply_parts = []
    for block in response.content:
        if block.type == "text":
            reply_parts.append(block.text)
        elif block.type == "tool_use":
            tools_used.append(block.name)
            tool_result = execute_tool(block.name, block.input)
            reply_parts.append(f"[{block.name}]: {tool_result}")

    return {
        "reply": "\n".join(reply_parts).strip(),
        "tools_used": tools_used,
        "declined": False,
    }
