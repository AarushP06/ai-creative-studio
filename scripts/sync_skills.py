"""Copy Skills from .agents/skills (Codex) to .claude/skills (Claude Code).

Edit Skills ONLY in .agents/skills, then run:  python scripts/sync_skills.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / ".agents" / "skills", ROOT / ".claude" / "skills"

if __name__ == "__main__":
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    print("Synced:", ", ".join(sorted(p.name for p in DST.iterdir())))
