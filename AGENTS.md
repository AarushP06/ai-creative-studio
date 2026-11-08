# AGENTS.md — AI Creative Studio

Instructions for coding agents (Codex, Claude Code, Copilot) working in this repository.

## What this project is

A small business website with two AI features:
- **Generate a service card** (Architecture B): the server asks Gemini for one card as JSON,
  validates it, and shows it only if it passes.
- **Plan your visit** (Architecture C): a small runtime agent in `app/agent/` answers a
  visitor question and may call one read-only tool, `check_availability`.

## Two separate execution environments — never mix them

| | BUILD TIME (you, the coding agent) | RUN TIME (the website) |
|---|---|---|
| Who runs | Codex / Claude Code in the developer's editor | `python run.py` (FastAPI) |
| Uses | AGENTS.md, Skills, custom agents, MCP `get_brand_rules` | Gemini API + Pydantic + `app/rules.py`; the runtime agent in `app/agent/` |
| Instructions | this file (read automatically by coding agents) | `app/agent/instructions.md` (loaded by our Python code) |
| Changes | source code, tests, styles | what the visitor sees |

The running app does NOT read this file, Skills, or MCP. The website's own agent reads only
`app/agent/instructions.md`, and only because `app/agent/agent.py` loads it. Do not mix the two.

## Commands

```bash
python run.py                    # start the website → http://127.0.0.1:8000
python -m pytest                 # all tests — offline, no API key needed
python scripts/check_setup.py    # environment check
python scripts/try_mcp.py        # call the MCP server without an agent
```

## Map

- `app/models.py` — Pydantic contract for a card (types, lengths, allowed values)
- `app/rules.py` — business rules (no prices, no guarantees). Every rule must scan ALL `TEXT_FIELDS`
- `app/pipeline.py` — raw text → JSON → Pydantic → rules
- `app/generators.py` — Gemini call + mock fallback; `app/service.py` — orchestration
- `app/agent/` — runtime agent: `agent.py` (loop), `tools.py`, `permissions.py`, `instructions.md`
- `data/availability.json` — fictional free visit times read by `check_availability`
- `brand/brand-rules.json` — single source of truth for limits, allowed values, palette
- `static/` — HTML, CSS, JS of the website
- `data/simulated_responses/` — deliberately invalid model outputs (each must be rejected)
- `tests/` — offline tests; Gemini is always faked

## Rules

0. Never edit or commit on `main`. Run `git branch --show-current` first; if it prints `main`, stop and ask the human to create a branch (e.g. `git switch -c fix/issue-1-<short-name>`).
1. Never open, print, copy or commit `.env` or any API key. Keys stay server-side.
2. Never edit, skip or delete a test to make it pass. Fix the code instead.
3. Tests must never call the real Gemini API or the network.
4. Smallest change that solves the task. More than 2 files changed → stop and ask first.
5. Do not change limits or allowed values in code only — `brand/brand-rules.json` and `app/models.py` must agree.
6. Model output is untrusted: render it with `textContent`, never `innerHTML`.
7. Do not add frameworks, databases, Docker or new dependencies.
8. Before you finish: run `python -m pytest` and show the result and the diff.
9. Never push, open or merge pull requests yourself. The human commits, pushes, opens the PR and merges.
10. Never add a tool to `ALLOWED_TOOLS` in `app/agent/permissions.py`, or raise its limits, without the human's explicit approval. Level 1 runtime tools are read-only.
