# CLAUDE.md

> Copy this file into the root of any project that uses the spec-driven-build framework. Replace the placeholders (`<...>`) and delete this top blockquote.

## Framework

This project is built using the **spec-driven-build framework**, version **<X.Y.Z>**.

The framework repository lives at: `<absolute path to framework repo on this machine>`

- **Delivery mode:** `<github_pr | local_branch>`. <github_pr only: the `gh` identity for this project is `<identity>`; confirm with `gh auth status` before any push or PR.>
- **Role install path:** `<pasted prompts via the Facilitator | .claude/agents/ (copied from <framework-path>/templates/agents/)>`.
- **Worker models:** build tier (test_author, swe) `sonnet`; judge tier (spec_author, pm, tester, pr_reviewer, phase_reviewer) `opus`. Enforced, not advisory: the `subagent-model-guard` plugin (`<framework-path>/plugins/subagent-model-guard/`) denies any spawn whose model breaks this. Install it with `/plugin marketplace add <framework repo>` then `/plugin install subagent-model-guard@spec-driven-build`. Every spawn names its model, and so does every Workflow `agent()` call. Nothing inherits the session model.

The recommended way to do work on this project is via the **Facilitator** — an orchestrator session that holds the framework knowledge so you don't have to. To begin (or resume) work:

1. Open a Claude Code session in this repo.
2. Paste the contents of `<framework-path>/templates/facilitator_bootstrap.md` as the first message.
3. The Facilitator reads project state and tells you what's next.

You can ask the Facilitator "where are we" or "what's next" at any time to re-orient after a gap.

### Manual workflow (fallback)

If the Facilitator is unavailable or you need to do something it doesn't support, the manual workflow is documented in `<framework-path>/USING_THE_FRAMEWORK.md`. Read the framework docs in this order:

1. `<framework-path>/SPEC_DRIVEN_BUILD_FRAMEWORK.md` — the methodology
2. `<framework-path>/AGENT_ROSTER.md` — the seven agent roles
3. `<framework-path>/FACILITATOR.md` — the orchestrator's spec (relevant context even when running manually)
4. This project's `PROJECT_OVERVIEW.md` — the project-level decisions

The framework's discipline is non-optional in this project. Hard constraints in `PROJECT_OVERVIEW.md` are auto-fail criteria. Reviewer roles run in fresh context. Spec is the artifact; code is the output.

## Project state

- Current phase: `<phase number and name, or "not yet started">`
- Facilitator state: see `.facilitator/state.json` (if present); resume prompt in `.facilitator/START_HERE.md`
- Open tickets / in-flight work: see GitHub issues filtered by `phase-<N>` label, or `specs/phase_<N>/tickets/`
- Decisions: `DECISIONS.md` (cite `D-<n>`; never restate)
- Human acceptance run for the current phase: `reviews/phase_<N>/run_sheet.md` (unsigned until the human walks it)
- Retro notes: `RETRO.md` (Facilitator appends auto-notes; you append your own)

## Project-specific notes

<Anything specific to this project that doesn't belong in PROJECT_OVERVIEW.md but that every Claude Code session should know.>
