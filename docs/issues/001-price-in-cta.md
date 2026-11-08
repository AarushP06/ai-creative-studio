# Issue #1 — A price on the button reaches the website

> In class, Copilot Chat on github.com drafts this issue from the failed Actions run.
> Use this file to CHECK Copilot's draft — or copy it directly if Copilot Chat is not available.

**Bug:** A service card with a price in the button text (`cta_text`) passes validation and is shown.

**Steps to reproduce**
1. `python run.py` and open http://127.0.0.1:8000
2. Studio Lab → Response source: **Simulate: price in cta** → Run this request
3. Or run `python -m pytest` → `test_price_in_cta_text_is_rejected` fails

**Expected:** the card is rejected with `cta_text: contains a price`.
**Actual:** the card is accepted and appears on the website.

**Acceptance criteria**
- [ ] A price in ANY free-text field (`title`, `summary`, `cta_text`) is rejected
- [ ] `python -m pytest` → all tests pass; no existing test edited or deleted
- [ ] A new test proves a price in `title` is rejected too
- [ ] At most 2 files changed (`app/rules.py`, `tests/test_rules.py`)
- [ ] Work done on branch `fix/issue-1-price-in-cta`, merged into `main` through a pull request
