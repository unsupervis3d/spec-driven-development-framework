# Using the Framework

A short guide to applying the spec-driven-build framework to a project. There are two ways to use it: the **Facilitator path** (recommended) and the **manual path** (fallback). This document covers both.

The deep methodology is in `SPEC_DRIVEN_BUILD_FRAMEWORK.md`; the agent details are in `AGENT_ROSTER.md`; the orchestrator's spec is in `FACILITATOR.md`. This is the operational glue.

---

## Where the framework lives

The framework repo lives at a stable path on your machine. Pick one and commit to it. Suggested: `~/projects/spec-driven-development-framework/`.

Every project's `CLAUDE.md` and Facilitator bootstrap reference that absolute path. If the framework moves, every project's pointers need to be updated — so don't move it.

If you work across multiple machines, use the same path on each, or symlink so the canonical path resolves everywhere.

---

## Bootstrapping a new project

1. **Create the project repo.** `git init`, a one-line README, optionally a GitHub remote.
2. **Copy `templates/CLAUDE.md`** from the framework repo into the project repo root. Rename to `CLAUDE.md`. Fill in the placeholders (framework version, framework path, project state, delivery mode, role install path, worker models).
3. **Answer the bootstrap questions** (they are listed in `templates/facilitator_bootstrap.md`; the Facilitator asks them on a new project): delivery mode (`github_pr` or `local_branch`), the `gh` identity if `github_pr`, the role install path, the worker model tiers (and install the `subagent-model-guard` plugin so they are enforced; `plugins/subagent-model-guard/README.md` covers the per-user install and an org-wide rollout users can't disable), the exact test/lint/type commands per app, and whether a design doc exists under `docs/plans/`.
4. **Choose a role install path.** Either the Facilitator fills `prompts/<role>.md` per spawn (nothing to install), or copy `templates/agents/` to the project's `.claude/agents/` and fill its placeholders so each role is spawnable by name with a harness-enforced tool allowlist. The two are equivalent; `CLAUDE.md` records which one the project uses.
5. **Write `PROJECT_OVERVIEW.md`** in the project repo root, starting from `templates/PROJECT_OVERVIEW.md`. This is the highest-leverage artifact in the whole framework. Do not skip steps to get to coding. It typically takes one or more focused sessions, not a few minutes. On a brownfield project, run the Spec Author in discovery mode first so the "Existing components" section comes from `discovery/INVENTORY.md`, not memory. Fill "How a human verifies a phase"; every phase's run sheet starts from it.
6. **Create `RETRO.md`** from `templates/RETRO.md` and **`DECISIONS.md`** from `templates/DECISIONS.md` in the project repo root. Append to both as you go; specs and tickets cite `D-<n>` IDs instead of restating decisions.
7. **Create `specs/` and `reviews/` directories.** Phase specs, rubrics and `specs/amendments/` go in `specs/`; reviewer reports, fix lists and the phase's `run_sheet.md` go in `reviews/phase_<N>/` (the full path table is in `FACILITATOR.md`, "Review artifact paths").
8. **Commit everything.** Tag `framework-bootstrap` so you can find it later.

From here you choose your path.

---

## Facilitator path (recommended)

**To start or resume work on a phase:**

1. Open a Claude Code session in the project repo.
2. Paste the contents of `templates/facilitator_bootstrap.md` as the first message.
3. The Facilitator reads project state, determines what's next, and tells you. If there's already a `.facilitator/state.json` from a prior session, it picks up where you left off. If a previous session left `.facilitator/START_HERE.md`, you can paste that instead; it carries the locked decisions and open gate so the Facilitator does not have to rediscover them.

**To re-orient after a gap:**

Ask the Facilitator "where are we" or "what's next." It responds with current phase, state, gate (if any), and the immediate next action — usually in under 10 lines.

**During a phase:**

The Facilitator spawns each agent role as a subagent in fresh context, captures the structured output, and surfaces a human gate. You read the gate inputs (quoted verbatim from the subagent), approve or redirect. The Facilitator advances.

**Across phases:**

Each phase gets its own Facilitator session. A phase ends with you, not the agents: you execute and sign `reviews/phase_<N>/run_sheet.md` against a real boot of the stack before the Phase Reviewer runs, and no standing authorization covers that gate. At phase end, the Facilitator produces a carry-forward briefing (`.facilitator/carry_forward_phase_<N+1>.md`) and refreshes `.facilitator/START_HERE.md`. The next phase's Facilitator reads them at startup.

**See `FACILITATOR.md`** for the state machine and per-state responsibilities.

---

## Manual path (fallback)

Use the manual path when:

- The Facilitator is unavailable (Claude Code session limits, etc.).
- You're debugging a Facilitator failure and want to invoke a specific agent directly.
- You're doing a one-off action the Facilitator doesn't support.

**To invoke an agent role manually:**

1. Copy the relevant prompt template from `prompts/<role>.md` in the framework repo.
2. Fill in the placeholders for this specific invocation.
3. Save the filled-in prompt to the project repo at `.facilitator/scratch/<role>_<context>_prompt.md` for the audit trail (the same place the Facilitator uses).
4. Open a fresh Claude Code session (do not reuse a prior session). Paste the filled prompt.
5. The agent does its work and emits a structured YAML output at the end.
6. You read the output, decide on the human gate, manually advance to the next role.

**Order, per phase:**

1. **Spec Author** (spec mode) — produces the phase spec.
2. (Human gate: review spec.)
3. **Spec Author** (rubric mode) — produces `specs/PHASE_<N>_REVIEW_RUBRIC.md` and the skeleton of `reviews/phase_<N>/run_sheet.md`.
4. (Human gate: review rubric and run sheet skeleton; confirm every grep was proven against planted bad code.)
5. **PM** — produces tickets.
6. (Human gate: review tickets.)
7. **For each ticket, in dependency order:**
   - **Test Author** → (gate) → **SWE** → (gate: read the PR and its `testing_steps`) → **Tester** → (gate: confirm `testing_steps_followable`) → **PR Reviewer** in fresh context → (gate).
   - **If any verifier returned findings — a fix round:** you rule on each finding (`B-n` / `N-n`: fix now, defer, or route to Spec Author); **Test Author** encodes the "fix now" findings as new red tests → **SWE** → **Tester** → **PR Reviewer** on the delta, same reviewer instructions, prior report attached. Increment the round; three rounds on one ticket is a scope signal, not a reason for a fourth.
   - **Merge gate:** walk the PR's testing steps yourself against a running instance, then merge. The SWE's run sheet section for this ticket is now final.
8. **Execute and sign the run sheet** (`reviews/phase_<N>/run_sheet.md`) against a real boot of the whole stack from a clean clone. Every section needs a result, proof, and a negative control.
9. **Phase Reviewer** in fresh context. It checks the signature before anything else.
10. (Human gate: review phase report. Findings go through a phase-level fix round and a re-run of the failed run sheet sections.)
11. Consolidate retro notes. Decide framework updates. Start next phase.

---

## When to update the framework

After each phase retro, look at the notes. If something was painful in a way that's *general*, fix it in the framework repo. Tag a new framework version. Update each project's `CLAUDE.md` to reference the new version when you're ready to migrate.

If something was painful but project-specific, fix it in the project, not the framework.

Lessons flow upstream as **generic rules**: the defect class, the gate that missed it, the rule that would have caught it. Never the project's name, hostnames, account names, people, or employer. The framework repo is public; the projects that teach it usually are not.

Resist the urge to fix the framework mid-phase. The framework is a tool; changing it while using it makes the data noisier. Wait for the phase boundary.

---

## What to do when you're stuck

The framework will sometimes get in the way. When that happens:

1. **Note it in `RETRO.md`.** What you were trying to do, what the framework required, what would have been easier.
2. **Do the thing the framework says.** This time. Even if heavy.
3. **At the phase retro, decide.** Real framework problem, or a corner-cutting impulse? Be honest.

The framework is supposed to feel slightly painful — that pain is the friction that catches mistakes. But if it's *too* painful and the catch rate is low, the design is wrong. Don't suffer in silence; don't bypass without recording.

---

## Anti-patterns to watch for

- **Spec drift mid-phase.** Updating `PROJECT_OVERVIEW.md` or the phase spec while feature work is in flight, because something was harder than expected. Stop. Either finish the feature against the original spec (and note in retro), or pause and update deliberately. Don't smear.
- **Reviewer cross-contamination.** Letting a reviewer session see what the implementer "intended." Reviewers read artifacts cold.
- **Skipping the human gate.** "Just merge it, it's fine" at end of phase. Don't.
- **Framework worship.** Treating "did we follow the framework correctly" as the success criterion instead of "did we ship something good." The framework serves the work.
- **Facilitator over-trust.** The Facilitator is operational glue. It does not replace your judgment. If it presents a gate and you'd review it lightly, slow down — gates are designed to be substantive.
- **Standing authorization that swallows the phase gate.** "Keep going while it's green" is allowed for the mechanical gates and recorded in `state.json`. If it ends in a phase you never touched by hand, the authorization was mis-scoped: it can never cover the last ticket's step walk, the run sheet, a ruling, or a spec/rubric approval.
- **Decisions pasted into spec bodies.** A ruling answered in chat gets appended to the spec, then copied to the open-questions file, then quoted in a ticket. Two thousand lines later nobody can find the current rule. Decisions go in `DECISIONS.md` with an ID; everything else cites the ID.
