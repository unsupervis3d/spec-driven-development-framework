# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is the **spec-driven-build framework** itself — a methodology, an agent roster, and a set of templates. **It is not a tool and there is nothing to install, build, lint, or run.** The artifacts here are markdown documents that *other* project repos consume.

Concretely: a separate project repo bootstraps from `templates/CLAUDE.md`, references this framework by version in its `PROJECT_OVERVIEW.md`, and runs its build pipeline using the agent roles defined here. Work in *this* repo is editing the methodology and templates — not implementing features in a product.

Treat any request that sounds like "add a feature," "wire this up," or "run the tests" with suspicion. There is no application here. The request likely belongs in a downstream project repo, not this one.

## The four primary documents

Read these in this order when picking up a task:

1. **`README.md`** — orientation, status, design principles. Source of truth for the framework's *intent*.
2. **`SPEC_DRIVEN_BUILD_FRAMEWORK.md`** — the methodology. The four-artifact pattern (`PROJECT_OVERVIEW.md`, `PHASE_N_SPEC.md`, `REVIEW_AGENT_PROMPT.md`, `PHASE_N_REVIEW_RUBRIC.md`), hard constraints, behavioral contracts, the fix-file pattern, phase splitting, adversarial review. The deep reference.
3. **`AGENT_ROSTER.md`** — the seven agent roles (Spec Author, PM, Test Author, SWE, Tester, PR Reviewer, Phase Reviewer), each with Job / Inputs / Outputs / Failure mode. Each role's prompt template lives here in spirit, even before `prompts/` is populated.
4. **`USING_THE_FRAMEWORK.md`** — the operational glue. How to bootstrap a project, run a phase, when to update the framework. Short by design.

Supporting files: `CHANGELOG.md` (versioning log — the "why" matters more than the "what"), `RETRO.md` (pilot project notes), and `templates/` (starter files copied into downstream project repos — currently just `templates/CLAUDE.md`).

## Editorial discipline

The framework is opinionated, personal to one user, and pre-pilot. When editing:

- **Preserve voice and stance.** The documents are blunt, prescriptive, and honest about limitations. Do not soften them into generic best-practices prose. "The framework is a means, not an end" is a line of intent, not filler.
- **Honor the design principles listed in `README.md`.** Anything that violates them is a framework bug. Specifically: spec is the artifact / code is the output; verifier is not the implementer; hard constraints are grep-enforceable; drift compounds; the framework serves shipping, not itself.
- **The framework is provisional.** Resist adding new agents, new artifacts, or new ceremony before a pilot has surfaced the need. Section "What this roster deliberately does not include" in `AGENT_ROSTER.md` and "Design intent for the pilot" in `CHANGELOG.md` both spell this out. Restraint is a feature.
- **Each agent's job has one sentence with no `and`.** If you find yourself writing two activities joined by `and`, the role should either be split or the second activity dropped.
- **Hard constraints must be grep-enforceable.** When adding example constraints, give a constraint a grep could catch — "no `subprocess.run`" beats "code should be safe."
- **`templates/` files use `<placeholder>` syntax.** Real values get filled in by the consuming project, not here. Don't accidentally hardcode a project name into a template.

## Versioning and changelog

Framework versions are tagged so downstream projects can pin against a stable revision. The current version is in `README.md` (`Version: 0.1.0` at time of writing).

Every meaningful revision:

1. Updates the appropriate documents.
2. Bumps the version in `README.md`.
3. Adds a `CHANGELOG.md` entry that explains the **why**, not just the what. Future-you needs the reasoning.
4. Is tagged in git at the new version.

Do not change framework content without a changelog entry. The changelog is the audit trail; silent revisions defeat the point of versioning.

## What "done" looks like in this repo

A task on this repo is done when the documents are internally consistent — `README.md`, `SPEC_DRIVEN_BUILD_FRAMEWORK.md`, `AGENT_ROSTER.md`, and `USING_THE_FRAMEWORK.md` agree with each other, and `CHANGELOG.md` reflects the change. There are no tests to run and no build to pass; consistency across documents is the verification.

When you finish an edit, cross-check: did the change in document A invalidate a claim in document B? The four core docs reinforce each other and will drift apart silently if edits aren't propagated.

## Don't

- Don't create a `src/`, `package.json`, or any code scaffolding. There is no application.
- Don't apply the framework's own pipeline (Spec Author → PM → ...) to changes in this repo. The framework is for execution-mode product builds, not for editing the framework itself. (Read the "Discovery vs. Execution" section of `SPEC_DRIVEN_BUILD_FRAMEWORK.md` — meta-applying the framework to itself is exactly the kind of procedure-as-procrastination it warns against.)
- Don't add `prompts/` content speculatively. Per `CHANGELOG.md`'s design intent: prompts are the artifacts most likely to need real-world iteration; populate them from pilot experience, not imagination.
- Don't generate per-project content (project overviews, phase specs, retros) in *this* repo. Those live in the project repo that consumes the framework.
