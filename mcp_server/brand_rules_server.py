"""MCP server for CODING AGENTS (build time) — not used by the running website.

Exposes one read-only tool, get_brand_rules, that returns brand/brand-rules.json.
A coding agent (Codex, Claude Code) launches this file over stdio after you
register it. See README → "Connect the MCP server".

Run by hand (it will wait silently for an MCP client — Ctrl+C to stop):
    python mcp_server/brand_rules_server.py
Test without an agent:
    python scripts/try_mcp.py
"""
from __future__ import annotations

import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer  # MCP Python SDK 2.x (FastMCP was renamed MCPServer)

RULES_PATH = Path(__file__).resolve().parent.parent / "brand" / "brand-rules.json"

server = MCPServer("brand-rules")


@server.tool()
def get_brand_rules() -> dict:
    """Return the official brand rules for AI Creative Studio service cards:
    length limits, allowed images/tones/CTA actions, banned content, colour palette
    and writing voice. Read-only. Call this before changing styles or validation rules."""
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    server.run()  # stdio transport
