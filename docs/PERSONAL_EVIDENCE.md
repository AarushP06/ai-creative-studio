# Personal Evidence — Session 3

Name: ______________________   GitHub fork URL: ______________________________

Fill in each box with a screenshot or pasted output. Keep it short.

## 1. The defect (before the fix)
Failing test output OR screenshot of the price card accepted in Studio Lab.

## 2. The fix is proven
`python -m pytest` summary line after the fix:
```
```
Commit hash: ________  (`git log --oneline -1`)
Pull request link: ______________________  ☐ tests check green  ☐ merged

## 3. Invalid AI output is rejected
Screenshot of Studio Lab showing a **Rejected** verdict with the violation list.
Which response was it? ☐ live Gemini with the untrusted brief  ☐ a simulated response: __________

## 4. The MCP tool call
Screenshot of the agent trace showing `get_brand_rules` being called
(Codex or GitHub Copilot — say which).

## 4b. Copilot on GitHub (optional)
Copilot's explanation of the failed Actions run, or its PR summary — and one thing you checked yourself.

## 4c. The runtime agent's trace
Screenshot of the *Plan your visit* trace where the agent calls `check_availability`.
In one sentence: why did the model call the tool (or not)? What would it have answered without it?

## 5. Your voice (2 sentences)
What did the AI get wrong or nearly wrong today, and how did you catch it?
