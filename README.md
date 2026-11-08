# AI Creative Studio

**Applied AI Certificate · Level 1 · Session 3 — Build with AI. Put AI inside the app.**

A business website for a fictional business that *you* invent. A visitor clicks
**Generate a service card** → our server asks Gemini → Python validates the answer →
only safe cards reach the page.

See the one-page diagram in `docs/ARCHITECTURE.md`.

---

## 1. Setup (once)

You need **Python 3.11+**, Git, VS Code with the **Codex** and **GitHub Copilot Chat** extensions, a GitHub account and a Gemini API key.

```bash
# 1. Fork this repository on GitHub, then clone YOUR fork
git clone https://github.com/<you>/ai-creative-studio.git
cd ai-creative-studio

# 2. Virtual environment
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS / Linux

# 3. Packages + settings
pip install -r requirements.txt
copy .env.example .env            # Windows   (macOS/Linux: cp .env.example .env)

# 4. Check
python scripts/check_setup.py
```

No API key yet? That's fine — the site runs in **Mock mode**.

## 2. Run and test

```bash
python run.py               # open http://127.0.0.1:8000   (Ctrl+C to stop)
python -m pytest            # offline tests — never call Gemini
```

At the start you should see **exactly 2 failing tests**, both caused by one bug
(`docs/issues/001-price-in-cta.md`). That's today's defect.

## 3. Today's build — one app, three uses of AI

| Section | Use of AI | You do | Branch | Checkpoint |
|---|---|---|---|---|
| Setup | — | Run the site, edit `business/brief.md`, commit → Actions turns red ✗ | `main` | `checkpoint-1` |
| **A** | **AI for development** | **Copilot** explains the red run and drafts Issue #1 → branch → **Codex** + `safe-change` fixes it → PR → merge. Then connect MCP → the ui_designer agent applies the palette from `get_brand_rules` → PR → merge | `fix/issue-1-price-in-cta`, `style/brand-palette` | `checkpoint-2` |
| **B** | **The app calls an LLM** | Add your key → live card. Untrusted brief → see what gets through → `add-validation-rule` → PR → merge | `feat/no-discounts` | `checkpoint-3` |
| **C** | **An agent inside the app** | *Plan your visit*: watch the agent decide to call `check_availability`, change the data and `instructions.md`, see `permissions.py` block a tool → PR → merge | `feat/visit-assistant-rule` | `final` |

## 3b. The Git workflow — every change, every time

Real teams never let anyone (human or AI) change `main` directly. Each change lives on
its own branch and reaches `main` only through a reviewed pull request (PR).

```
Issue → branch → agent plan → you approve → failing test → fix → review diff
      → commit → push → pull request → GitHub runs the tests → merge → back to main
```

```bash
# 1. Start from an up-to-date main
git switch main
git pull

# 2. One branch per issue — BEFORE the agent edits anything
git switch -c fix/issue-1-price-in-cta

# 3. ... agent + Skill work, tests pass, you read the diff ...

# 4. Commit and push the branch
git add app/rules.py tests/test_rules.py
git commit -m "fix: reject prices in every text field (closes #1)"
git push -u origin fix/issue-1-price-in-cta

# 5. Open the PR on GitHub (or: gh pr create --fill --base main)
#    → wait for the green ✓ from the "tests" check → Merge

# 6. Back to main for the next task
git switch main
git pull
```

Three things that trip people up:

| Watch out | Why |
|---|---|
| **PR base = YOUR fork's `main`** | GitHub suggests the course repository by default for forks. Change *base repository* to `<you>/ai-creative-studio`. |
| **`closes #1` closes the issue only after the merge** | An open, unmerged PR leaves the issue open. That is correct behaviour. |
| **Agent on `main`?** Stop. | The Skills check the branch first. If `git branch --show-current` prints `main`, create a branch before any edit. |

Branch names: `fix/…` for bugs, `feat/…` for new behaviour, `style/…` for visual changes.

## 4. Stuck for more than 3 minutes? Jump.

```bash
git stash                              # keep your work aside (optional)
git switch -c rescue checkpoint-2      # a new branch starting at that checkpoint
```

Each checkpoint is the state of `main` **after** that step's pull request was merged.
Continue the next step from `rescue` (create the next branch from it as usual). Your next PR
will also contain the checkpoint's changes; write "rescued at checkpoint-2" in the PR.

Tags: `starter` → `checkpoint-1` → `checkpoint-2` → `checkpoint-3` → `final`

## 5. Gemini API key (Section B)

1. Google AI Studio → **Get API key** (free tier; you must be 18+).
2. Paste it into `.env` after `GEMINI_API_KEY=` — never into code, never into chat with an agent.
3. `git check-ignore .env` must print `.env`.
4. Restart `python run.py`. The chip at the top right turns **● Live**.

Free tier: use only fictional business data. Never paste personal information.

## 6. Connect the MCP server (Section A)

```bash
python scripts/register_mcp.py      # prints the exact command for Codex / Claude Code
python scripts/register_mcp.py --vscode   # GitHub Copilot: writes .vscode/mcp.json
python scripts/try_mcp.py           # works even if your agent cannot connect
```

Then ask your agent: *"Call the get_brand_rules tool and tell me the accent colour."*
No `get_brand_rules` call in the trace = the agent answered from memory. Try again.

## 6b. The visit assistant (Section C)

```
app/agent/
  instructions.md   what the agent should do      → loaded by agent.py (NOT AGENTS.md)
  agent.py          the loop: model → tool? → permissions → tool → model → answer check
  tools.py          check_availability(day) reads data/availability.json (read-only)
  permissions.py    ALLOWED_TOOLS + call limits   → enforced by code
```

Instructions *ask*. Permissions *enforce*. No key? The mock agent makes scripted decisions,
but the tool, the permissions and the answer check still run for real.

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| Chip says **Mock mode** with a key | Restart the server after editing `.env`; check `AI_MODE=auto` |
| Toast: *HTTP 429* / *did not answer in time* | Normal on free tier — the mock card still passes the checkpoint |
| Toast: *rejected the API key* | Re-copy the key into `.env`; no quotes, no spaces |
| `Address already in use` | Another server is running. Stop it, or `PORT=8001 python run.py` |
| `No module named …` | Activate `.venv`, then `pip install -r requirements.txt` |
| `No module named 'mcp.server.fastmcp'` | You followed an old tutorial — this repo uses MCP SDK 2.x (`MCPServer`) |
| Agent ignores the Skill | Name it: *"Use the safe-change skill."* |
| Agent allowance used up | `git switch -c rescue checkpoint-2` and continue |
| Visit assistant ignores my change to `instructions.md` | Restart is not needed, but the **mock** agent is scripted and ignores instructions. Check the trace line *Loaded instructions.md* shows your new rule |

## Project map

```
app/            run-time code (FastAPI, Gemini call, validation)
app/agent/      run-time agent: instructions.md, agent.py, tools.py, permissions.py
static/         the website (HTML, CSS, JS, illustrations)
business/       your brief + an untrusted test brief
brand/          brand-rules.json — single source of truth
data/           mock cards, invalid responses, availability.json
mcp_server/     build-time MCP server for coding agents
tests/          offline tests
.agents/skills/ Skills (Codex)   ·   .claude/skills/ same Skills (Claude Code)
.codex/agents/  custom agents (Codex)   ·   .claude/agents/ custom agents (Claude Code)
.github/agents/ custom agents (GitHub Copilot)   ·   .github/workflows/ GitHub Actions tests
AGENTS.md       instructions for coding agents
docs/           architecture, issue #1, personal evidence template
```
