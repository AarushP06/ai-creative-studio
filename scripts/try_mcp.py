"""Call the brand-rules MCP server WITHOUT a coding agent.

Use this to prove the server works, or as the fallback if your agent cannot connect.
    python scripts/try_mcp.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters

SERVER = Path(__file__).resolve().parent.parent / "mcp_server" / "brand_rules_server.py"


async def main() -> None:
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with Client(params) as client:
        tools = await client.list_tools()
        print("Tools offered by the server:", [t.name for t in tools.tools])
        result = await client.call_tool("get_brand_rules", {})
        data = result.structured_content or json.loads(result.content[0].text)
        print("\nget_brand_rules() returned:")
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
