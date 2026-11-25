---
name: review
description: Cold-context review of an existing PR (lightweight spec-driven-build pattern). Works for your own PR or a teammate's.
argument-hint: "<pr-number>"
disable-model-invocation: true
---

**Settings.** Values in angle brackets below (`<HOW_TO_FETCH_WORK>`, `<CONSTRAINTS_FILE>`, ...) come
from the "Lightweight settings" section of the project's `CLAUDE.md`. If that section or a key is
missing, ask the human for the value once, offer to add it to `CLAUDE.md`, and don't guess. The
section's format is in `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md`.

Perform a cold-context review of PR **$ARGUMENTS**.

Spawn a **fresh** subagent with the contents of `${CLAUDE_PLUGIN_ROOT}/lightweight/prompts/review_only.md`
(or this repo's forked copy under `.claude/prompts/`, if `CLAUDE.md` says to use it) as its prompt, read at spawn time, with `$ARGUMENTS`
filled in.

The reviewer reads only: `gh pr view $ARGUMENTS`, `gh pr diff $ARGUMENTS`, the linked work unit (derived from the PR
title, description, or branch, then fetched fresh via `<HOW_TO_FETCH_WORK>`), and
`<CONSTRAINTS_FILE>`. Nothing else: no session history, no implementer reasoning, no notes at
`<NOTES_LOCATION>`, and not the PR's comment thread.

Relay the subagent's structured verdict to chat verbatim. Works for your own PR (a self-review pass
after manual implementation, or mid-iteration after feedback) and for a teammate's.

Spawn every subagent with an explicit `model`: the implementer and CI monitor on the build tier
(`sonnet`), the reviewer on the judge tier (`opus`). The subagent model guard denies spawns that
don't.
