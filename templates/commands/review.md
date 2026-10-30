---
description: Cold-context review of an existing PR (lightweight pattern)
argument-hint: <pr-number>
---

Perform a cold-context review of PR **$1**.

Spawn a **fresh** subagent with the contents of `<framework-path>/lightweight/prompts/review_only.md`
(or this repo's forked copy under `.claude/prompts/`) as its prompt, read at spawn time, with `$1`
filled in.

The reviewer reads only: `gh pr view $1`, `gh pr diff $1`, the linked work unit (derived from the PR
title, description, or branch, then fetched fresh via `<HOW_TO_FETCH_WORK>`), and
`<CONSTRAINTS_FILE>`. Nothing else: no session history, no implementer reasoning, no notes at
`<NOTES_LOCATION>`, and not the PR's comment thread.

Relay the subagent's structured verdict to chat verbatim. Works for your own PR (a self-review pass
after manual implementation, or mid-iteration after feedback) and for a teammate's.
