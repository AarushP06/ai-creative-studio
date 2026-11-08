"""Project structure that the coding agents rely on."""
from tests.conftest import ROOT

SKILLS = ["safe-change", "add-validation-rule"]


def test_agents_md_exists_and_states_the_two_runtimes():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "BUILD TIME" in text and "RUN TIME" in text


def test_claude_md_imports_agents_md():
    assert "@AGENTS.md" in (ROOT / "CLAUDE.md").read_text(encoding="utf-8")


def test_skills_have_name_and_description():
    for skill in SKILLS:
        text = (ROOT / ".agents" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert text.startswith("---") and f"name: {skill}" in text and "description:" in text


def test_claude_code_skill_copies_are_in_sync():
    """Codex reads .agents/skills; Claude Code reads .claude/skills. Keep them identical."""
    for skill in SKILLS:
        a = (ROOT / ".agents" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        b = (ROOT / ".claude" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert a == b, f"{skill}: .claude/skills copy differs — run: python scripts/sync_skills.py"


def test_copilot_agents_are_locked_by_tools():
    """Copilot custom agents: the reviewer cannot edit, the designer cannot run commands."""
    reviewer = (ROOT / ".github" / "agents" / "test-reviewer.agent.md").read_text(encoding="utf-8")
    designer = (ROOT / ".github" / "agents" / "ui-designer.agent.md").read_text(encoding="utf-8")
    reviewer_tools = reviewer.split("tools:")[1].splitlines()[0]
    designer_tools = designer.split("tools:")[1].splitlines()[0]
    assert "'edit'" not in reviewer_tools and "'execute'" in reviewer_tools
    assert "'execute'" not in designer_tools and "'brand-rules/*'" in designer_tools


def test_skills_refuse_to_work_on_main():
    """Real-world rule: no direct changes to main — every Skill checks the branch first."""
    for skill in SKILLS:
        text = (ROOT / ".agents" / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "git branch --show-current" in text and "main" in text
