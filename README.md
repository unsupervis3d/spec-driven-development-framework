# Spec-Driven Build Framework

A methodology for building real software with Claude Code (or any LLM coding agent) without losing control of scope, quality, or architectural integrity.

This repo holds the framework itself: the methodology, the agent roster, the Facilitator (orchestrator) spec, the prompt templates, and the per-project bootstrap. It also ships as two Claude Code plugins: `spec-driven-build` (the new-project interview, the Facilitator, the seven worker roles and the lightweight commands) and `subagent-model-guard` (enforcement of the role-to-model split). The framework is a set of disciplines, artifacts, and prompts you apply to a project repo.

---

## Status

**Version:** 0.4.0
**Maturity:** Active development. The framework has run five real projects end to end, one of them through more than twenty phases, and 0.3.0 is the release that folds their lessons back in. New projects start on the Facilitator path from day one.

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
  - `DECISIONS.md` — the one-line-per-ruling decision log that specs cite by ID.
  - `run_sheet.md` — the human acceptance run for a phase: the steps a person follows against a real boot, and signs.
  - `CLAUDE.md` — per-project bootstrap, written by the new-project interview.
  - `START_HERE.md` — the resume prompt the Facilitator refreshes at every phase boundary.
  - `org/` — the managed settings, managed `CLAUDE.md` and guard policy an org deploys to make the framework its standard.
- **The `spec-driven-build` plugin** (the repo root is the plugin):
  - `skills/new-project/` — `/spec-driven-build:new-project`, the scoping interview that creates a project.
  - `skills/facilitator/` — `/spec-driven-build:facilitator`, which starts or resumes the Facilitator.
  - `skills/ticket/`, `skills/review/`, `skills/ticket-status/` — the lightweight commands.
  - `agents/` — the seven worker roles (`spec-driven-build:<role>`), each pinned to its tier's model.
  - `hooks/` — the session-start kickoff: offers the interview in new repos, points framework repos at the Facilitator.
- **`plugins/subagent-model-guard/`** — a Claude Code plugin that denies any subagent spawn or Workflow agent that would run on the wrong model for its role, and audits the model each one actually started on, so the build/judge split holds under auto-approve. This repo is the marketplace for both plugins (`.claude-plugin/marketplace.json`, marketplace `spec-driven-build-plugins`).
- **`ORG_ROLLOUT.md`** — how to make the framework your org's standard: install for everyone, kick off new projects with scoping, and keep the gates.
- **`lightweight/`** — pared-down adaptations for ticket-scale work in existing codebases, where humans already play most of the roles. Keeps the one gate you can't drop.
- **`CHANGELOG.md`** — what changed between versions and why.

---

## Who this is for

This started as one person's tool, and it's opinionated to the point of being personal — the design choices are calibrated to real failure modes with Claude Code, not smoothed out for a general audience. That's deliberate; take what's useful and adapt the rest.

The underlying problems, though, are widely shared. If you build software with LLM agents and watch scope drift, silent architectural revisions, or "helpful" additions you never asked for, the methodology should resonate. You're welcome to use it, fork it, and adapt it (see License).

---

## Quick start

Install once per machine (or have your org deploy it; see `ORG_ROLLOUT.md`):

```
/plugin marketplace add <owner>/<repo>
/plugin install spec-driven-build@spec-driven-build-plugins
/plugin install subagent-model-guard@spec-driven-build-plugins
```

`<owner>/<repo>` is this repository or your org's fork. Then, for a new project:

1. Create an empty repo and open Claude Code in it. The plugin notices the repo is new and offers the scoping interview.
2. Run `/spec-driven-build:new-project` (or accept the offer). It interviews you, then drafts `PROJECT_OVERVIEW.md` and the project skeleton. Approve the overview section by section. It's the highest-leverage artifact in the framework, so don't rush it.
3. Commit, then run `/spec-driven-build:facilitator`. The Facilitator takes over: it tells you what's next, spawns the worker roles, and stops at every human gate.

Resume later by opening a Claude Code session in the repo and running `/spec-driven-build:facilitator`, or asking it "where are we."

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
- **Every phase ends with a person and a sheet of steps.** Tests passing is how the agents know they're done. A human following numbered steps against a running system is how *you* know. That check has an artifact, an owner, and a signature, and no amount of auto-approval removes it.
- **The Facilitator verifies; it does not relay.** A subagent's "tests pass" or "pushed" is a claim until the Facilitator has re-run the command itself.

---

## Known limitations

- **Subagent isolation has held in practice,** but subagents stall after finishing more often than they fail. The Facilitator handles that by inspecting the tree, not re-spawning.
- **Single-implementer assumption.** A team of humans would need to negotiate role ownership in ways the framework doesn't currently address.
- **Heavyweight for small projects.** The four-artifact pattern and seven-role roster are appropriate for multi-phase projects. Don't apply this to one-weekend builds.
- **Tied to current LLM capabilities.** As models improve, some roles may collapse naturally. Revisit the roster yearly.

---

## License

MIT — see [`LICENSE`](LICENSE). Use it, fork it, adapt it. It's provided as-is, with no warranty and no promise of support; it's a methodology under active development, not a maintained product.
