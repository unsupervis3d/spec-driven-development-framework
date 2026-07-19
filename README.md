# Spec-Driven Build Framework

A methodology for building real software with Claude Code (or any LLM coding agent) without losing control of scope, quality, or architectural integrity.

This repo holds the framework itself: the methodology, the agent roster, the Facilitator (orchestrator) spec, the prompt templates, and the per-project bootstrap. It is not a tool. There is nothing to install. The framework is a set of disciplines, artifacts, and prompts you apply to a project repo.

---

## Status

**Version:** 0.2.0
**Maturity:** Active development. The framework has been exercised against a real private pilot project (mid-phase). New projects starting on 0.2.0 use the Facilitator path from day one.

Expect breaking changes between 0.x versions. The framework is tagged at each meaningful revision so projects can pin to a known version.

---

## What's in here

- **`SPEC_DRIVEN_BUILD_FRAMEWORK.md`** — the methodology. Read this first.
- **`HUMAN_GATES.md`** — the human review gates and why they're the load-bearing idea of the whole framework. Read this second.
- **`AGENT_ROSTER.md`** — the seven worker roles that produce artifacts: Spec Author, PM, Test Author, SWE, Tester, PR Reviewer, Phase Reviewer.
- **`FACILITATOR.md`** — the orchestrator (meta-role) that holds framework knowledge, tracks state, spawns the worker roles as subagents, and surfaces human gates. The recommended way to use the framework.
- **`USING_THE_FRAMEWORK.md`** — operational glue: bootstrapping a new project, the Facilitator path, the manual path, when to update the framework.
- **`prompts/`** — invocation prompt templates for each worker role. Each template includes a structured-output section the Facilitator parses.
- **`templates/`**:
  - `PROJECT_OVERVIEW.md` — fillable template for the per-project overview (the highest-leverage artifact).
  - `RETRO.md` — fillable template for per-project retro notes.
  - `CLAUDE.md` — per-project bootstrap.
  - `facilitator_bootstrap.md` — the prompt the human pastes to start a Facilitator session.
- **`lightweight/`** — pared-down adaptations for ticket-scale work in existing codebases, where humans already play most of the roles. Keeps the one gate you can't drop.
- **`CHANGELOG.md`** — what changed between versions and why.

---

## Who this is for

This started as one person's tool, and it's opinionated to the point of being personal — the design choices are calibrated to real failure modes with Claude Code, not smoothed out for a general audience. That's deliberate; take what's useful and adapt the rest.

The underlying problems, though, are widely shared. If you build software with LLM agents and watch scope drift, silent architectural revisions, or "helpful" additions you never asked for, the methodology should resonate. You're welcome to use it, fork it, and adapt it (see License).

---

## Quick start

For a new project on framework v0.2.0:

1. Create the project repo. Empty.
2. Copy `templates/CLAUDE.md` to the project root, fill placeholders.
3. Copy `templates/PROJECT_OVERVIEW.md` to the project root and fill it in. This is the highest-leverage artifact in the whole framework — don't rush it.
4. Open a Claude Code session in the project repo. Paste `templates/facilitator_bootstrap.md`.
5. The Facilitator takes over: tells you what's next, spawns agent subagents, surfaces human gates.

Resume later by opening a Claude Code session and asking the Facilitator "where are we."

The manual workflow (without Facilitator) is documented in `USING_THE_FRAMEWORK.md` as a fallback.

---

## Design principles

These are the ideas the framework refuses to give up on. Anything that violates one of these is a framework bug, not a feature.

- **The spec is the artifact. The code is the output.** If the spec is good and the code is wrong, the implementer failed. If the code is fine and the spec was vague, the human failed. Most failures are spec failures.
- **The verifier is not the implementer.** Reviewers run in fresh context. Confidence about your own work is not evidence.
- **Hard constraints are non-negotiable and grep-enforceable.** If a constraint can't be checked by a script, it isn't a hard constraint — it's a hope.
- **Drift compounds; catch it early.** Adversarial review at the phase boundary is the only place to catch accumulated "helpful additions" before they become load-bearing.
- **The framework is a means, not an end.** The goal is shipping products you're proud of. If the framework is making the work worse, the framework is wrong.
- **Human gates remain real even with the Facilitator.** The Facilitator removes bookkeeping, not judgment. If a gate feels skippable, slow down.

---

## Known limitations

- **Lightly tested end-to-end.** The original pilot reached mid-phase under 0.1.x. The Facilitator and structured outputs are new in 0.2.0 and have not yet been exercised on a full phase.
- **Subagent reliability is an assumption.** v0.2.0 assumes Claude Code's subagent feature provides fresh context. If isolation is poor, fresh-context-required roles fall back to human-driven sessions.
- **Single-implementer assumption.** A team of humans would need to negotiate role ownership in ways the framework doesn't currently address.
- **Heavyweight for small projects.** The four-artifact pattern and seven-role roster are appropriate for multi-phase projects. Don't apply this to one-weekend builds.
- **Tied to current LLM capabilities.** As models improve, some roles may collapse naturally. Revisit the roster yearly.

---

## License

MIT — see [`LICENSE`](LICENSE). Use it, fork it, adapt it. It's provided as-is, with no warranty and no promise of support; it's a methodology under active development, not a maintained product.
