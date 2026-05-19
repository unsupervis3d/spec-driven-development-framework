# Using the Framework

A short guide to applying the spec-driven-build framework to a project. Read this once; then you should be able to bootstrap any new project in 5-10 minutes.

This document is intentionally short. The deep methodology is in `SPEC_DRIVEN_BUILD_FRAMEWORK.md`; the agent details are in `AGENT_ROSTER.md`. This is just the operational glue.

---

## Where the framework lives

The framework repo lives at a stable path on your machine. Pick one and commit to it. Suggested: `~/code/spec-driven-build/`.

Every project's `CLAUDE.md` references that absolute path. If the framework moves, every project's `CLAUDE.md` needs to be updated — so don't move it.

If you work across multiple machines, use the same path on each machine, or use a symlink so that one canonical path always works.

---

## Bootstrapping a new project

For every new project that will use the framework:

1. **Create the project repo.** Empty, just `git init` and a README.
2. **Copy `templates/CLAUDE.md` from the framework repo** into the project repo root. Rename to `CLAUDE.md`. Fill in the placeholders (framework version, framework path, project state).
3. **Write `PROJECT_OVERVIEW.md` in the project repo root.** This is the highest-leverage artifact in the whole framework. Do not skip steps to get to coding. Use the template in `templates/PROJECT_OVERVIEW.md` (TBD — currently no template; reference an existing project's overview as a model).
4. **Create `RETRO.md` in the project repo root, empty.** Append observations as you go through phases. Do not wait for end-of-phase to think about what's working and what isn't.
5. **Create `specs/` directory.** Phase specs and feature specs live here.
6. **Commit everything.** Tag this commit something like `framework-bootstrap` so you can find it later.

That's the bootstrap. From here on, the framework drives the work.

---

## Starting a Claude Code session

When you open a Claude Code session in the project:

1. **Claude Code reads `CLAUDE.md` automatically.** It learns about the framework and gets pointed at the right docs.
2. **You tell it which agent role this session is playing.** Spec Author, PM, Test Author, SWE, Tester, PR Reviewer, or Phase Reviewer.
3. **The role's prompt is your first message.** Until the framework has stable prompt templates, write the role prompt inline based on `AGENT_ROSTER.md`'s description of the role.
4. **The session does its work and produces the role's deliverable.** Then ends.

A new session for each role. Reviewers must run in fresh context — that is the whole point of the role separation. Do not reuse a session that just implemented a feature to also review it.

---

## Running a phase

The order, for each phase:

1. **Spec Author session.** Reads `PROJECT_OVERVIEW.md` and the phase-level objective; produces a phase spec at `specs/PHASE_N_<NAME>.md`. The human reviews and approves the spec before any feature work begins.
2. **For each feature in the phase, in dependency order:**
   - **PM session.** Reads the phase spec; produces a feature ticket with acceptance criteria.
   - **Test Author session.** Reads the ticket; produces failing tests against the acceptance criteria.
   - **SWE session.** Reads the ticket and the failing tests; implements until tests pass; opens a PR.
   - **Tester session.** Independently verifies the PR meets the acceptance criteria, in fresh context.
   - **PR Reviewer session.** Reads the PR and the hard constraints in `PROJECT_OVERVIEW.md`; runs grep checks; approves or rejects.
   - **Human gate.** You merge the PR.
3. **Phase Reviewer session, at end of phase.** Fresh context; reads all merged code for the phase against the phase spec and hard constraints. Surfaces anything that drifted across features.
4. **Human gate at end of phase.** Final approval. Update `RETRO.md` with phase-level observations. Decide whether the framework needs updates before the next phase.

---

## When to update the framework

After each phase retro, look at the notes. If something was painful in a way that's *general* — not specific to this project — fix it in the framework repo. Tag a new framework version. Update the project's `CLAUDE.md` to reference the new version.

If something was painful but project-specific, fix it in the project, not in the framework.

Resist the urge to fix the framework mid-phase. The framework is a tool; changing the tool while using it makes the data noisier. Wait for the phase boundary.

---

## What to do when you're stuck

The framework will sometimes get in the way. When that happens:

1. **Note it in `RETRO.md`.** Specifically: what were you trying to do, what was the framework requiring, what would have been easier.
2. **Do the thing the framework says.** This time. Even if it feels heavy.
3. **At the phase retro, decide.** Is this a real framework problem or did you just want to cut a corner? Be honest. The framework is supposed to feel slightly painful — that pain is the friction that catches mistakes. But if it's *too* painful and the catch rate is low, the design is wrong.

The framework is a means, not an end. If after a few phases the friction is consistently not earning its keep, change the framework. Don't suffer in silence and don't bypass without recording.

---

## Anti-patterns to watch for

- **Spec drift mid-phase.** Updating `PROJECT_OVERVIEW.md` or the phase spec while feature work is in flight, because something turned out harder than expected. Stop. Either finish the feature against the original spec (and note the problem in retro), or pause the feature and update the spec deliberately. Don't smear the change across both.
- **Reviewer cross-contamination.** Letting a reviewer session see what the implementer "intended." The reviewer's job is to read the code as a stranger would. Hand them only the artifacts the role calls for.
- **Skipping the human gate.** The temptation to "just merge it, it's fine" at the end of a phase. The human gate exists because the LLM agents don't have the context to make the final call. Skipping it is how a project ships something the human would have rejected if they'd looked.
- **Framework worship.** Treating "did we follow the framework correctly" as the success criterion instead of "did we ship something good." The framework serves the work, not the other way around.
