# CLAUDE.md

> `/spec-driven-build:new-project` creates this file from the template. To do it by hand, copy this
> file into the project root, replace the placeholders (`<...>`), and delete this blockquote.

## Framework

This project is built with the **spec-driven-build framework**, version **<X.Y.Z>**, installed as the
`spec-driven-build` Claude Code plugin. Without the plugin, the framework repository is at:
`<path to a clone of the framework repo, or "plugin only">`.

- **Delivery mode:** `<github_pr | local_branch>`. <github_pr only: the `gh` identity for this project is `<identity>`; confirm with `gh auth status` before any push or PR.>
- **Roles:** the plugin's agents (`spec-driven-build:<role>`). <Or: local overrides in `.claude/agents/` for `<roles>`, because `<reason>`.>
- **Worker models:** build tier (test_author, swe) `sonnet`; judge tier (spec_author, pm, tester, pr_reviewer, phase_reviewer) `opus`. The `subagent-model-guard` plugin enforces this and denies any spawn whose model breaks it. Every spawn names its model, and so does every Workflow `agent()` call. Nothing inherits the session model.
- **Commands:** test `<exact command per app>`; lint `<command>`; type check `<command>`. <Note any that collide when run together.>
- **Constraint scripts:** `<the executable hard-constraint checks from PROJECT_OVERVIEW.md, or "see rubric">`.

Work on this project runs through the **Facilitator**, an orchestrator that holds the framework
knowledge so you don't have to. To begin or resume:

1. Open a Claude Code session in this repo.
2. Run `/spec-driven-build:facilitator`.
3. The Facilitator reads project state and tells you what's next.

Ask it "where are we" or "what's next" at any time to re-orient after a gap.

### Manual workflow (fallback)

If the Facilitator is unavailable or can't do what you need, the manual workflow is in the
framework's `USING_THE_FRAMEWORK.md`. Read the framework docs in this order: `SPEC_DRIVEN_BUILD_FRAMEWORK.md`
(the method), `AGENT_ROSTER.md` (the seven roles), `FACILITATOR.md` (the orchestrator's spec), then
this project's `PROJECT_OVERVIEW.md`.

The framework's discipline is non-optional in this project. Hard constraints in `PROJECT_OVERVIEW.md` are auto-fail criteria. Reviewer roles run in fresh context. Spec is the artifact; code is the output.

## Lightweight settings

<Optional. Used by `/spec-driven-build:ticket`, `/spec-driven-build:review` and
`/spec-driven-build:ticket-status` for ticket-scale work. Delete this section if unused.>

- **HOW_TO_FETCH_WORK:** `<e.g. gh issue view <id> --repo <owner/repo>>`
- **CONSTRAINTS_FILE:** `<e.g. PROJECT_OVERVIEW.md, or docs/constraints.md>`
- **NOTES_LOCATION:** `<where private implementer notes go, e.g. .claude/notes/<id>.md>`
- **DRAFT_PATH:** `<e.g. .claude/scratch/ticket_<id>_pr_draft.md>`
- **TICKET_LINK_COMMAND:** `<how to link a PR to its work unit, or "none">`
- **STATE_FILE:** `<e.g. .claude/in_flight.json>`
- **CI_GREEN_ASSIGNEE:** `<who to assign when CI is green, or "none">`
- **STALE_THRESHOLD:** `<e.g. 2 days>`

## Project state

- Current phase: `<phase number and name, or "not yet started">`
- Facilitator state: see `.facilitator/state.json` (if present); resume prompt in `.facilitator/START_HERE.md`
- Open tickets / in-flight work: see GitHub issues filtered by `phase-<N>` label, or `specs/phase_<N>/tickets/`
- Decisions: `DECISIONS.md` (cite `D-<n>`; never restate)
- Human acceptance run for the current phase: `reviews/phase_<N>/run_sheet.md` (unsigned until the human walks it)
- Retro notes: `RETRO.md` (Facilitator appends auto-notes; you append your own)

## Project-specific notes

<Anything specific to this project that doesn't belong in PROJECT_OVERVIEW.md but that every Claude Code session should know.>
