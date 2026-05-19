## Framework

This project is built using the **spec-driven-build framework**, version **<X.Y.Z>**.

The framework repository lives at: `~/projects/spec-driven-development-framework/` known as `<framework-path>`

Before doing any work on this project, read:

1. `<framework-path>/SPEC_DRIVEN_BUILD_FRAMEWORK.md` — the methodology
2. `<framework-path>/AGENT_ROSTER.md` — the seven agent roles and their responsibilities
3. This project's `PROJECT_OVERVIEW.md` (in the repo root) — the project-level decisions

The framework's discipline is non-optional in this project. In particular:

- Hard constraints in `PROJECT_OVERVIEW.md` are auto-fail criteria, not suggestions.
- Reviewer roles must run in fresh context (new Claude Code session, no memory of the implementer's work).
- Spec is the artifact; code is the output. If the spec is vague, ask before assuming.

## Agent role

If this session was started to act as a specific agent role (Spec Author, PM, Test Author, SWE, Tester, PR Reviewer, Phase Reviewer), the role-specific prompt should have been provided as the first user message. If no role was specified, default to asking which role this session should play before doing any work.

## Project state

- Current phase: `<phase number and name>`
- Current phase spec: `<path to phase spec, e.g. specs/PHASE_1_FOUNDATION.md>`
- Open tickets / in-flight work: see `<location, e.g. specs/in_flight/>`
- Retro notes: `RETRO.md` (append observations during work; do not wait for phase end)

## Project-specific notes

<Anything specific to this project that doesn't belong in PROJECT_OVERVIEW.md but that every Claude Code session should know. Examples: local conventions, paths to important files, gotchas the framework doesn't cover.>
