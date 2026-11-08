---
name: safe-change
description: Fix a bug or make a small change from a GitHub issue using test-first, minimal edits and human approval. Use when asked to fix an issue, fix a failing test, or make a "safe change".
---

# Safe change: issue → test → minimal fix → review

Follow every step in order. Do not skip the STOP points.

## 0. Check the branch — STOP if on main
Run `git branch --show-current`.
- If it prints `main` (or `master`): do not edit anything. Ask the human to run
  `git switch -c fix/issue-<number>-<short-name>` and wait.
- Otherwise continue and mention the branch name in your plan.

## 1. Restate the issue
In 3 lines: what is wrong, expected behaviour, actual behaviour.

## 2. Investigate (read-only)
- Run `python -m pytest` and report which tests fail.
- Find the code responsible. Quote the exact lines you rely on (file + line numbers).
- Do not edit anything yet.

## 3. Plan — STOP for approval
Show:
- the root cause in one sentence;
- the files you will change (maximum 2) and what changes in each;
- the test that proves the fix (an existing failing test, or a new one you will add).

Wait until the human says "approved".

## 4. Test first
If no test fails because of this bug, add one that does. Run it and show it FAIL.

## 5. Minimal fix
- Change only what the plan said.
- Never edit, skip or weaken an existing test to make it pass.
- Never touch `.env`, keys, or unrelated files.

## 6. Verify
- Run `python -m pytest`. All tests must pass. Show the summary line.
- Show `git diff --stat` and the full diff.

## 7. Hand back
Give the human the next commands, filled in:
```
git add <changed files>
git commit -m "fix: <what> (closes #<issue>)"
git push -u origin <branch>
```
Then: open a pull request into the fork's `main`, wait for the green tests check, merge,
`git switch main` and `git pull`.
Do NOT commit, push or merge yourself. The human does.
