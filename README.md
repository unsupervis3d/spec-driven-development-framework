# Spec-Driven Build Framework

A methodology for building real software with Claude Code (or any LLM coding agent) without losing control of scope, quality, or architectural integrity.

This repo holds the framework itself: the methodology document, the agent roster, and the prompt templates that go with them. It is not a tool. There is nothing to install. The framework is a set of disciplines and artifacts you apply to a project repo.

---

## Status

**Version:** 0.1.0
**Maturity:** Pre-pilot. The framework has been designed but not yet used end-to-end on a real project. Treat everything here as provisional until at least one pilot has shipped and the retrospective has been folded back in.

Expect breaking changes between 0.x versions. The framework will be tagged at each meaningful revision so that in-flight projects can pin to a known version and not get whiplashed by changes mid-build.

---

## What's in here

- **`SPEC_DRIVEN_BUILD_FRAMEWORK.md`** — the methodology. Read this first. Covers the four-artifact pattern, hard constraints, behavioral contracts, cost contracts, adversarial review, phase splitting, and when *not* to use the framework.
- **`AGENT_ROSTER.md`** — the seven roles that run a project from spec to shipped phase: Spec Author, PM, Test Author, SWE, Tester, PR Reviewer, Phase Reviewer. Each role's purpose, scope, and known open questions.
- **`prompts/`** — prompt templates for each agent role. Drop these into a fresh Claude Code session to invoke a given role. *(To be populated during the pilot — these are the artifacts most likely to need real-world iteration before they're worth committing.)*
- **`templates/`** — starter templates for the four project artifacts (`PROJECT_OVERVIEW.md`, phase specs, feature specs, retro notes). *(Also to be populated during the pilot.)*
- **`CHANGELOG.md`** — what changed between framework versions and why. The "why" matters more than the "what." Future-you needs to remember the reasoning.

---

## Who this is for

One person: me. The framework is opinionated to the point of being personal. If you found this repo from outside and it's useful to you, great — but the design choices are calibrated to one person's failure modes with Claude Code, not to a general audience.

That said, the underlying problems are widely shared. If you build software with LLM agents and find yourself watching scope drift, silent architectural revisions, or "helpful" additions you never asked for, the methodology may resonate.

---

## How to use this with a project

1. Clone or copy this repo somewhere stable.
2. In your project repo, reference the framework version you're building against (a line in your `PROJECT_OVERVIEW.md` is enough — e.g. `Framework: spec-driven-build v0.1.0`).
3. Write your `PROJECT_OVERVIEW.md` using the methodology in `SPEC_DRIVEN_BUILD_FRAMEWORK.md`. This is the highest-leverage artifact in the whole framework — getting it wrong contaminates every downstream phase.
4. Plan your phases. Each phase gets its own spec.
5. Run each phase through the agent roster. Spec Author writes feature specs; PM produces tickets; Test Author writes acceptance tests; SWE implements; Tester verifies; PR Reviewer reviews per-feature; Phase Reviewer reviews the whole phase before the human gate.
6. After each phase, write a brief retro note in the project repo. After the project, pull the generalizable learnings back into this framework repo as a versioned update.

---

## Design principles

These are the ideas the framework refuses to give up on. Anything that violates one of these is a framework bug, not a feature.

- **The spec is the artifact. The code is the output.** If the spec is good and the code is wrong, the implementer failed. If the code is fine and the spec was vague, the human failed. Most failures are spec failures.
- **The verifier is not the implementer.** Reviewers run in fresh context, with no memory of what the implementer thought it was doing. Confidence about your own work is not evidence.
- **Hard constraints are non-negotiable and grep-enforceable.** If a constraint can't be checked by a script, it isn't a hard constraint — it's a hope.
- **Drift compounds; catch it early.** Every phase inherits the previous phase's accumulated "helpful additions." Adversarial review at the phase boundary is the only place to catch this before it becomes load-bearing.
- **The framework is a means, not an end.** The goal is shipping products you're proud of. If the framework is making the work worse, the framework is wrong.

---

## Known limitations

Documented honestly so future-me doesn't pretend they don't exist:

- **Untested end-to-end.** No pilot has completed yet. Some of the agent roles may turn out to be redundant or wrong; some of the artifacts may be over- or under-specified.
- **Single-implementer assumption.** Designed for one human orchestrating LLM agents. A team of humans using this would need to negotiate role ownership in ways the framework doesn't currently address.
- **Heavyweight for small projects.** The four-artifact pattern and seven-agent roster are appropriate for multi-phase projects. Don't apply this to one-weekend builds.
- **Tied to current LLM capabilities.** As models get better, some agent roles (especially the splits between Tester and PR Reviewer, or Spec Author and PM) may collapse naturally. Revisit the roster yearly.

---

## License

Personal use. No license granted for external use until the framework is past 1.0 and the design is stable enough that I'm willing to support it.
