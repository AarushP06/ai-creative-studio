"""The MCP server used by coding agents. Tested in-process (no agent, no network)."""
import asyncio
import json

from mcp import Client

from mcp_server.brand_rules_server import RULES_PATH, server


def run(coro):
    return asyncio.run(coro)


async def _list_and_call():
    async with Client(server) as client:
        tools = await client.list_tools()
        result = await client.call_tool("get_brand_rules", {})
        return tools, result


def test_server_offers_exactly_one_read_only_tool():
    tools, _ = run(_list_and_call())
    assert [t.name for t in tools.tools] == ["get_brand_rules"]


def test_get_brand_rules_returns_the_rules_file():
    _, result = run(_list_and_call())
    data = result.structured_content or json.loads(result.content[0].text)
    assert data == json.loads(RULES_PATH.read_text(encoding="utf-8"))
    assert "palette" in data and "card_limits" in data
