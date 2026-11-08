"""Connect the brand-rules MCP server to YOUR coding agent.

    python scripts/register_mcp.py            # print the commands for Codex / Claude Code
    python scripts/register_mcp.py --vscode   # write .vscode/mcp.json for GitHub Copilot in VS Code

Both use the Python of your active virtual environment, so the server finds its packages.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "mcp_server" / "brand_rules_server.py"
python = Path(sys.executable)

if "--vscode" in sys.argv:
    target = ROOT / ".vscode" / "mcp.json"
    target.parent.mkdir(exist_ok=True)
    config = {"servers": {"brand-rules": {"type": "stdio", "command": str(python), "args": [str(SERVER)]}}}
    target.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target.relative_to(ROOT)} (ignored by Git: it contains paths of your computer).")
    print("In VS Code: open .vscode/mcp.json and click 'Start' above \"brand-rules\", then trust it.")
    sys.exit(0)

print("Codex (CLI or VS Code extension):")
print(f'  codex mcp add brand-rules -- "{python}" "{SERVER}"')
print("  codex mcp list\n")
print("GitHub Copilot in VS Code:")
print("  python scripts/register_mcp.py --vscode\n")
print("Claude Code (optional):")
print(f'  claude mcp add brand-rules -- "{python}" "{SERVER}"')
print("  claude mcp list\n")
print("No agent connection? Prove the server works on its own:")
print("  python scripts/try_mcp.py")
