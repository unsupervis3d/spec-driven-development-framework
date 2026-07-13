# Changelog

All notable changes to the spec-driven-build framework are documented here. The "why" matters more than the "what" — entries explain reasoning, not just list files changed.

---

## [Unreleased]

### Added
- **Phase-slicing + end-to-end "done" principle** (`SPEC_DRIVEN_BUILD_FRAMEWORK.md`: the Phase-plan bullet and the Done Definition prose). Phases must be sliced as end-to-end vertical feature slices, not horizontal layers; and a phase is not "done" until a human has exercised its new capability end-to-end through its user-facing surface — the UI in a local/Codespace run, or a scripted CLI/API session when there is deliberately no UI — against a real boot of the stack, not merely until the unit/contract suites are green. The Done Definition now mandates at least one human-run, whole-stack acceptance criterion as a first-class blocking gate.

### Design rationale
Across three real phases the same defect class recurred and only ever surfaced at the human evidence run, never in the agent suites: missing CORS, unwired cross-origin API base URLs, cookie `SameSite`, compose/env boot-coherence, and streaming/SSE wiring. Agent tests inject env directly and mock the network, so "all behavioral-contract tests pass" repeatedly did not mean "the feature works when a person uses it," and the gaps became after-the-fact remediation loops fired *after* a phase review had already passed. Making the end-to-end, user-exercisable slice the *purpose* of a phase — rather than a nice-to-have a phase can declare "separable" and drop — forces the scope to include the surface that makes the feature real and promotes the human end-to-end gate from an optional evidence item to a blocking part of Done.

---

## [0.2.0] — 2026-05-19

The Facilitator release. Introduces orchestrator role plus structured agent outputs.

### Added
- `FACILITATOR.md` — specification of the orchestrator role. The Facilitator is a meta-role (not a worker) that holds framework knowledge, tracks state, spawns worker roles as subagents in fresh context, captures structured outputs, surfaces human gates, and maintains the audit trail. It is scoped to one phase of one project.
- `templates/facilitator_bootstrap.md` — the prompt the human pastes to start a Facilitator session.
- "Where are we / what's next" conversational entry point baked into the Facilitator bootstrap, enabling fast re-orientation after a gap.

### Changed
- All seven worker-role prompt templates (`prompts/spec_author.md` through `prompts/phase_reviewer.md`) now include a **structured output section** — a YAML block emitted at the end of each role's response. The Facilitator parses these fields and quotes them verbatim when surfacing human gates. This was added specifically to defend against summary-fidelity drift: the Facilitator can't accidentally compress a Tester report into "the tests look fine" if the Tester role's verdict is a parseable field.
- `templates/CLAUDE.md` (project-level) now describes the Facilitator path as recommended and the manual workflow as fallback.
- `USING_THE_FRAMEWORK.md` rewritten to document both paths.
- `AGENT_ROSTER.md` opens with a note explaining how the Facilitator wraps the existing roster (the seven worker roles are unchanged).

### Design rationale
The Facilitator emerged from real friction during the first pilot project: the framework worked, but operating it required holding ten conventions in your head, and async work between sessions required a refresher each time. The Facilitator makes the framework portable in a real way — drop a `CLAUDE.md` into a new project, start a session, paste the bootstrap, and the framework knows what to do.

Two design decisions worth naming explicitly:
1. **Level 3 orchestration with structured outputs.** All seven worker roles spawn as subagents (not just the fresh-context-required ones). The Facilitator's main defense against drift is that it quotes parseable fields verbatim rather than paraphrasing freeform output.
2. **Per-phase scope.** A Facilitator session covers one phase. Carry-forward briefings move state across phase boundaries. This trades some context efficiency for context-window safety.

### Open questions for v0.2.x
- How well does Claude Code subagent isolation hold up in practice? If subagent context bleeds from parent, the fresh-context guarantee breaks and PR Reviewer / Phase Reviewer become useless. First few runs are load-bearing tests of this assumption.
- Are the structured output schemas right? Likely they're close but will need tuning. Expect schema migrations in 0.2.1+.
- Does the state file design survive real use? The current schema is a hypothesis.

### Migration notes for in-flight projects
Projects mid-phase under 0.1.x can continue with the manual workflow — none of the worker role outputs have *removed* fields, only added structured output. Adopting the Facilitator mid-project is supported but optional; recommended to adopt at a phase boundary so the Facilitator's startup state is clean.

---

## [0.1.1] — 2026-05-19

Mid-pilot iteration. Captured prompt templates derived from the pilot project's first agent invocations, plus the first framework refinement surfaced by the pilot.

### Added
- `prompts/spec_author.md`, `prompts/pm.md`, `prompts/test_author.md`, `prompts/swe.md`, `prompts/tester.md`, `prompts/pr_reviewer.md`, `prompts/phase_reviewer.md` — invocation prompt templates derived from the prompts that worked during Phase 1 of the pilot.

### Changed
- SWE role: now permitted to add comments to existing GitHub issues to capture observations relevant to those issues' future work. **Not** permitted to create new GitHub issues — new follow-up work surfaces via the PR description and requires human review.

### Pilot observations preserved for 0.2.0 consideration
- The PM role's siloed-tickets-from-phase-spec output was substantially better than past one-file-per-spec approaches. The Spec Author / PM separation appears to be doing real work.
- The Test Author role surfaces spec ambiguities as a side effect of writing failing tests. Worth promoting from "side effect" to "named responsibility" in `AGENT_ROSTER.md`.

---

## [0.1.0] — 2026-05-18

Initial framework release. Pre-pilot.

### Included
- `SPEC_DRIVEN_BUILD_FRAMEWORK.md` — methodology
- `AGENT_ROSTER.md` — the seven-role pipeline
- `README.md` — orientation and status
- `USING_THE_FRAMEWORK.md` — operational glue
- `templates/CLAUDE.md` — per-project bootstrap file

### Design intent for the pilot
Use the framework as written. Do not pre-build infrastructure before the pilot has surfaced what is actually needed.
