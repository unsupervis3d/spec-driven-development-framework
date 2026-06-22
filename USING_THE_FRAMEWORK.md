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
2. **Copy `templates/CLAUDE.md`** from the framework repo into the project repo root. Rename to `CLAUDE.md`. Fill in the placeholders (framework version, framework path, project state).
3. **Write `PROJECT_OVERVIEW.md`** in the project repo root. This is the highest-leverage artifact in the whole framework. Do not skip steps to get to coding. It typically takes one or more focused sessions, not a few minutes.
4. **Create `RETRO.md`** in the project repo root, empty. Append observations as you go — do not wait for end-of-phase.
5. **Create `specs/` and `reviews/` directories.** Phase specs go in `specs/`; reviewer reports go in `reviews/phase_<N>/`.
6. **Commit everything.** Tag `framework-bootstrap` so you can find it later.

From here you choose your path.

---

## Facilitator path (recommended)

**To start or resume work on a phase:**

1. Open a Claude Code session in the project repo.
2. Paste the contents of `templates/facilitator_bootstrap.md` as the first message.
3. The Facilitator reads project state, determines what's next, and tells you. If there's already a `.facilitator/state.json` from a prior session, it picks up where you left off.

**To re-orient after a gap:**

Ask the Facilitator "where are we" or "what's next." It responds with current phase, state, gate (if any), and the immediate next action — usually in under 10 lines.

**During a phase:**

The Facilitator spawns each agent role as a subagent in fresh context, captures the structured output, and surfaces a human gate. You read the gate inputs (quoted verbatim from the subagent), approve or redirect. The Facilitator advances.

**Across phases:**

Each phase gets its own Facilitator session. At phase end, the Facilitator produces a carry-forward briefing (`.facilitator/carry_forward_phase_<N+1>.md`). The next phase's Facilitator reads it at startup.

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
3. Save the filled-in prompt to the project repo at `prompts/phase_<N>/<NN>_<role>_<context>.md` for the audit trail.
4. Open a fresh Claude Code session (do not reuse a prior session). Paste the filled prompt.
5. The agent does its work and emits a structured YAML output at the end.
6. You read the output, decide on the human gate, manually advance to the next role.

**Order, per phase:**

1. **Spec Author** — produces the phase spec.
2. (Human gate: review spec.)
3. **PM** — produces tickets.
4. (Human gate: review tickets.)
5. **For each ticket, in dependency order:**
   - **Test Author** → (gate) → **SWE** → (gate: read PR) → **Tester** → (gate) → **PR Reviewer** in fresh context → (gate) → human-driven merge.
6. **Phase Reviewer** in fresh context.
7. (Human gate: review phase report.)
8. Consolidate retro notes. Decide framework updates. Start next phase.

---

## When to update the framework

After each phase retro, look at the notes. If something was painful in a way that's *general*, fix it in the framework repo. Tag a new framework version. Update each project's `CLAUDE.md` to reference the new version when you're ready to migrate.

If something was painful but project-specific, fix it in the project, not the framework.

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
