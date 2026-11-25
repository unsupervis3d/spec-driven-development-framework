---
name: ticket
description: Run the lightweight spec-driven-build loop for one work unit: implement, cold-context review, human gate on testing steps, PR, CI monitor. Use for ticket-scale work in an existing codebase.
argument-hint: "<work-unit-id>"
disable-model-invocation: true
---

**Settings.** Values in angle brackets below (`<HOW_TO_FETCH_WORK>`, `<CONSTRAINTS_FILE>`, ...) come
from the "Lightweight settings" section of the project's `CLAUDE.md`. If that section or a key is
missing, ask the human for the value once, offer to add it to `CLAUDE.md`, and don't guess. The
section's format is in `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md`.

Run the lightweight spec-driven-build workflow for work unit **$ARGUMENTS**. The canonical subagent prompts
live at `${CLAUDE_PLUGIN_ROOT}/lightweight/prompts/` (or this repo's forked copies under
`.claude/prompts/`, if `CLAUDE.md` says to use them); read each one fresh at the moment you spawn that phase's subagent so the prompt
files stay the single source of truth.

## 1. Implementer phase
Spawn a subagent with the contents of `ticket_implementer.md` as its prompt, with `$ARGUMENTS` filled in.
The implementer fetches the work unit (`<HOW_TO_FETCH_WORK, e.g. gh issue view $ARGUMENTS>`), reads any
notes at `<NOTES_LOCATION>`, reads the constraints in `<CONSTRAINTS_FILE>`, does a size scan (stops
and recommends escalate-or-split if too big), writes failing tests, implements to green, writes the
draft change description with numbered human testing steps to `<DRAFT_PATH, e.g.
.claude/scratch/ticket_$1_pr_draft.md>`, appends private notes to `<NOTES_LOCATION>`, and returns
structured output.

## 2. Reviewer phase — COLD CONTEXT
Spawn a **fresh** subagent with the contents of `ticket_reviewer.md` as its prompt. It must NOT
receive the implementer's structured output, this session's history, any narrative of what was
done, or the notes. It reads only: the work unit (fresh fetch), `<CONSTRAINTS_FILE>`,
`<DRAFT_PATH>`, and `git diff <base>...HEAD`. It returns a structured verdict.

## 3. Human gate
Quote the reviewer's verdict and the draft's testing steps verbatim in chat. If rejected, fix and
re-run from step 2. If approved, present the testing steps for the human to walk.

## 4. Wait
The human walks the testing steps against a running instance and replies with the result. Do not
proceed on "looks fine"; ask for the result of the walk.

## 5. On human approval
Create the PR via `gh pr create` with the draft as the description. Link it to the work unit via
`<TICKET_LINK_COMMAND, e.g. .claude/scripts/ticket_link.sh $ARGUMENTS <pr-number>>`. Delete `<DRAFT_PATH>`.
Write `<STATE_FILE, e.g. .claude/in_flight.json>` to record the new PR.

## 6. CI monitor phase
Spawn a subagent with the contents of `ticket_ci_monitor.md` as its prompt, with the PR number
filled in. It polls CI, handles flakes per its own rules, assigns `<CI_GREEN_ASSIGNEE>` on green,
and updates `<STATE_FILE>` as state changes.

Honor every constraint in `<CONSTRAINTS_FILE>` throughout. Follow the branch and PR conventions in
`CLAUDE.md`. Never commit directly to the default branch.

Spawn every subagent with an explicit `model`: the implementer and CI monitor on the build tier
(`sonnet`), the reviewer on the judge tier (`opus`). The subagent model guard denies spawns that
don't.
