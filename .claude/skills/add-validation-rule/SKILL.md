---
name: add-validation-rule
description: Add a new business rule that rejects unsafe AI-generated service cards (for example discounts, phone numbers, competitor names), with a simulated bad response and tests. Use when asked to block, ban or reject new content in AI output.
---

# Add a validation rule

A rule blocks AI output that is valid JSON but not acceptable for the business.

## 0. Check the branch — STOP if on main
Run `git branch --show-current`. If it prints `main`, ask the human to run
`git switch -c feat/no-<thing>` and wait. Never edit on `main`.

## 1. Confirm the rule — STOP for approval
State: the rule in one sentence, 3 examples that must be rejected, 2 similar examples
that must still be allowed (to avoid false positives). Wait for approval.

## 2. Check the brand rules
Read `brand/brand-rules.json` (or call the MCP tool `get_brand_rules` if it is connected).
If the rule is a brand policy, add a one-line entry under `banned_content`.

## 3. Write the check in `app/rules.py`
- Add a compiled regex constant next to the others.
- Add `def check_no_<thing>(card: ServiceCard) -> list[str]:`
- Loop over `TEXT_FIELDS` — a rule must scan EVERY free-text field, not just one.
- Message format: `"<field>: contains <thing> — <why it is not allowed>"`.
- Register the function in the `RULES` list.

## 4. Add a simulated bad response
Create `data/simulated_responses/<thing>.json`: a card that is valid in every way
EXCEPT the new rule. It appears automatically in the Studio Lab dropdown.

## 5. Add tests in `tests/test_rules.py`
- Parametrised test: each must-reject example is rejected.
- Test: the must-allow examples produce no violations.
`tests/test_pipeline.py` automatically checks that the new simulated response is rejected.

## 6. Verify
Run `python -m pytest` — all pass. Show the diff.
Suggest: `git commit -m "feat: reject <thing> in AI output"`, then push the branch and open a PR.
Do not commit, push or merge yourself; the human does.
