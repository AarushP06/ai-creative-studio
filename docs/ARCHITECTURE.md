# Architecture

## Two execution environments

```
BUILD TIME  (developer's computer, before the visitor arrives)
  Student → Coding agent (Codex / Claude Code)
              ├─ reads AGENTS.md            (project instructions)
              ├─ selects a Skill            (.agents/skills/…/SKILL.md)
              ├─ may delegate to a custom agent (ui_designer, test_reviewer)
              └─ calls MCP tool get_brand_rules  (mcp_server/brand_rules_server.py)
           → edits code → runs tests → human reviews diff → commit → GitHub PR

  On github.com:  GitHub Actions runs the tests on every push (red ✗ / green ✓)
                  Copilot Chat explains a failed run, drafts the issue, summarises the PR
                  The human creates the issue and clicks Merge — AI never decides alone

RUN TIME  (python run.py — while a visitor uses the site)
  Browser ──POST /api/service-card──► FastAPI (app/main.py)
                                        │  session limit / cooldown (app/limits.py)
                                        ▼
                                   Gemini API  (app/generators.py)   ── fails? ──► mock card
                                        │ raw text
                                        ▼
                         parse JSON → Pydantic (app/models.py) → business rules (app/rules.py)
                                        │ accepted                  │ rejected
                                        ▼                           ▼
                                  card on the page        Studio Lab shows why + mock card
```

RUN TIME, Architecture C  (Plan your visit — the website's own agent)
  Browser ──POST /api/ask──► app/agent/service.py
                               │  loads app/agent/instructions.md (our code reads it)
                               ▼
                         Gemini + tool descriptions (function calling)
                               │ "call check_availability(day='thursday')"
                               ▼
                         permissions.py  ── not allowed / over the limit? ──► error to the model
                               │ allowed
                               ▼
                         tools.py → data/availability.json → result back to Gemini
                               │ answer text
                               ▼
                         answer check (no prices, no guarantees) → browser + trace

The running website never reads AGENTS.md, Skills or MCP. Its agent has its own
instructions, its own tools and its own permissions — all configured in code.

| | A · Coding agent (build time) | C · Runtime agent (run time) |
|---|---|---|
| Instructions | AGENTS.md (read automatically) | app/agent/instructions.md (loaded by agent.py) |
| Tools | terminal, editor, tests, MCP `get_brand_rules` | `check_availability` (Python function) |
| Permissions | approval mode, custom-agent tool locks | `permissions.py` (ALLOWED_TOOLS, call limits) |
| Used by | the developer | the website visitor |

Level 1 keeps C small: one read-only tool, a hard call limit, one question at a time.
Level 2: several tools, write actions with human approval, memory, MCP at run time, evaluation.

## Three lines of defence

| Layer | Checks | Enforced by |
|---|---|---|
| Structured output | JSON shape, enum values | Gemini (ignores `maxLength`!) |
| Contract | types, lengths, allowed values, no extra fields | Pydantic `ServiceCard` |
| Business rules | no prices, no guarantees, … | `app/rules.py` |

What none of them prove: that a claim is *true*. "Open since 1998" passes every check even
if the brief never said it. That needs a different technique (grounding checks, human review).

## Why the mock path exists
No key, HTTP 429, timeout, bad key, server error, empty or rejected output → the visitor
still gets a validated card. A student's grade never depends on Google being available.
