# Changelog

All notable changes to the spec-driven-build framework are documented here. The "why" matters more than the "what" — entries explain reasoning, not just list files changed.

---

## [0.4.0] — 2026-11-24

The framework becomes a plugin. Until now everything but the guard was templates and documents: each project copied the role files, commands and bootstrap prompt, filled in placeholders, and kept its own copy. Those copies never received an update and drifted from the framework. Now one install gives every project the same, current framework, and an org can make it the default for everyone.

### Added

- **`spec-driven-build` plugin.** The repository root is the plugin:
  - **`/spec-driven-build:new-project`** (`skills/new-project/`). The scoping interview, asked in rounds: what the project is and is not, its users, the core loop, how a human will verify each phase, the stack and hard constraints (pushed until they can be checked by a script), the phases, success criteria and delivery. It then creates `CLAUDE.md`, a draft `PROJECT_OVERVIEW.md`, `DECISIONS.md`, `RETRO.md`, `specs/` and `reviews/`, and the human approves the overview section by section before anything is built. Brownfield repos get a discovery pass instead of a from-memory description.
  - **`/spec-driven-build:facilitator`** (`skills/facilitator/`). Starts or resumes the Facilitator. It replaces pasting `templates/facilitator_bootstrap.md`, and it spawns roles as `spec-driven-build:<role>` with the model passed explicitly.
  - **Seven role agents** (`agents/`), each pinned to its tier's model and reading its template from the plugin's `prompts/`. Project specifics come from the project's `CLAUDE.md`, not from per-project copies of the role files.
  - **`/spec-driven-build:ticket`, `/spec-driven-build:review`, `/spec-driven-build:ticket-status`.** The lightweight commands, with per-repo settings in a "Lightweight settings" section of `CLAUDE.md`.
  - **Session-start kickoff** (`hooks/session_start.py`). Offers the interview in an empty or near-empty repo, and points a framework repo at its Facilitator with the current phase and state. It says nothing in other repos. `SPEC_DRIVEN_BUILD_KICKOFF=off` disables it.
- **`ORG_ROLLOUT.md`.** How to make the framework an org standard, in five layers: a fork you control, managed settings that install both plugins for everyone, a managed `CLAUDE.md` that states the standard, the kickoff, and enforcement through gates, run sheets and the guard. It says plainly what this cannot force.
- **`templates/org/`.** The managed settings block, the managed `CLAUDE.md`, and the locked guard policy.

### Changed

- **Marketplace renamed** from `spec-driven-build` to `spec-driven-build-plugins`, so the framework plugin installs as `spec-driven-build@spec-driven-build-plugins`.
- **The guard finds plugin agent definitions** through Claude Code's install records, including local-directory marketplaces, so a plugin role agent's `model:` pin counts.
- **`templates/CLAUDE.md`** records commands, constraint scripts and lightweight settings, which the role agents read in place of placeholders.
- **Removed `templates/agents/`, `templates/commands/` and `templates/facilitator_bootstrap.md`.** They are superseded by `agents/`, `skills/` and `skills/facilitator/`. Without the plugin, paste `skills/facilitator/SKILL.md` with `${CLAUDE_PLUGIN_ROOT}` replaced by your clone's path.
- **The Facilitator skill no longer hardcodes the framework's location** (it used `~/projects/spec-driven-development-framework/`). It reads everything from the plugin.

### Design rationale

Packaging the guard alone left the most important property unenforced: every project drifting on its own copy. A plugin makes the framework a single versioned artifact. An org pins it in a fork and moves projects forward by bumping a version, not by asking each team to re-copy files.

The kickoff hook is deliberately quiet. It speaks only where the framework clearly applies: an empty repo, or a repo that already uses the framework. A standard that interrupts every bug fix in every legacy repo gets switched off.

Making the scoping interview a skill, with an approval gate at the end, puts the highest-leverage step at the start of every project, where it costs least. Nobody has to remember the questions, and the questions that matter most can't be skipped: how a human will verify each phase, and hard constraints that can be checked.

### Migration from 0.3.1

1. Re-add the marketplace under its new name and install both plugins:
   - `claude plugin marketplace remove spec-driven-build`
   - `claude plugin marketplace add <owner>/<repo>`
   - `claude plugin install spec-driven-build@spec-driven-build-plugins`
   - `claude plugin install subagent-model-guard@spec-driven-build-plugins`
2. In existing projects, start the Facilitator with `/spec-driven-build:facilitator` in place of the pasted bootstrap.
3. Copied role files in `.claude/agents/` become local overrides. Delete them to use the plugin's agents, or keep them and say so in `CLAUDE.md`.
4. Move each project's fills (test commands, constraint scripts, lightweight placeholders) into `CLAUDE.md` per `templates/CLAUDE.md`.

---

## [0.3.1] — 2026-11-24

Enforcement of the role-to-model split. Until now the split was a recommendation, and usage data showed it being ignored.

### Added

- **`subagent-model-guard` plugin** (`plugins/subagent-model-guard/`). This repository is also its marketplace (`.claude-plugin/marketplace.json`, marketplace name `spec-driven-build`), so installing is `/plugin marketplace add <owner>/<repo>` then `/plugin install subagent-model-guard@spec-driven-build`. What it does:
  - **Spawn check.** A `PreToolUse` check on `Agent`, `Task` and `Workflow` classifies every subagent spawn by role and denies it if its effective model is outside the role's tier. Roles are recognised from the agent name (including plugin agents such as `*:code-reviewer` or `*-analyzer`), the description, the prompt's opening, or an instruction to follow a role template or emit its output block.
  - **Tiers.** The build tier (`swe`, `test-author`, implementer, CI monitor) runs on `sonnet`. The judge tier (`spec-author`, `pm`, planner, `tester`, `pr-reviewer`, `phase-reviewer`, any reviewer) runs on `opus` or `fable`.
  - **Everything else.** Unroled spawns must name a model explicitly. Role work in a fork is denied. Every `agent()` call in a Workflow script must pass `opts.model`.
  - **Audit.** A `PostToolUse` audit compares each subagent's `resolvedModel` with its tier and reports a mismatch to the session as unverified work.
  - **Policy.** Layered: bundled defaults, then the user's `<config dir>/subagent_model_policy.json`, then an org's copy in the managed-settings directory, which wins so users can't loosen it.
  - **Behaviour.** Fails open on internal errors. Logs every decision (never prompts) to `<config dir>/logs/`.
  - **Org rollout.** Managed `extraKnownMarketplaces` plus `enabledPlugins`. Users can't disable a managed-enabled plugin, and its hooks run even under `allowManagedHooksOnly`.
  - **Tests.** `scripts/test_subagent_model_guard.py`, standard library only.

### Changed

- Role files in `templates/agents/` pin `model:` in frontmatter (`sonnet` for build roles, `opus` for judge roles). Previously models lived only in `CLAUDE.md` and `state.json`.
- Tester and PM move to the judge tier (`worker_models.tester` and `.pm`: `opus`). The tester is the first verifier of the SWE's work and should not share a tier with the writer it checks.
- `FACILITATOR.md` "Subagent operating rules", `templates/CLAUDE.md`, `templates/facilitator_bootstrap.md` and `USING_THE_FRAMEWORK.md` require an explicit model on every spawn and every Workflow `agent()` call, and point at the `subagent-model-guard` plugin.
- `verify_framework.py` runs on Python 3.9.

### Design rationale

Usage data from the downstream projects showed the role-to-model table ignored in every way it could be:
- role files with no `model:` line;
- role prompts pasted into `general-purpose` agents with no model;
- implementers spawned on the reviewer model;
- reviewers spawned on the implementer model.

In each case the subagent ran on whatever the orchestrator ran on, which is usually the most expensive model. Fixing it in prose had already failed, so the rule is now a hook, which runs in every permission mode.

Denying a spawn is cheaper than correcting it after it runs: the caller re-issues the call at once with the named model, and nothing runs on the wrong tier in the meantime.

It ships as a plugin, not a skill or an install script. A skill is guidance Claude can ignore, which is the failure being fixed. An install script asks people to run code that edits their settings, and leaves no clean update path. A plugin registers its own hooks, updates through `/plugin`, and is the unit an org can force-enable from managed settings. Only that managed rollout is tamper-proof. A user-installed plugin can be disabled by its user, and the README says so.

### Migration from 0.3.0

1. Install the guard: `/plugin marketplace add <owner>/<repo>`, then `/plugin install subagent-model-guard@spec-driven-build` (or the managed rollout in `plugins/subagent-model-guard/README.md`).
2. Add `model:` lines to any `.claude/agents/` role files (see `templates/agents/`).
3. Set `worker_models.tester` and `worker_models.pm` to `opus` in `.facilitator/state.json`.

---

## [0.3.0] — 2026-10-27

The verification release. Five projects ran 0.2.0 (one through twenty-two phases); this release folds back what they learned. The theme: the pipeline could go green end to end while the human gate quietly lost its inputs. 0.3.0 makes the human-run check a first-class artifact at both the PR and the phase level, gives the Facilitator a verification duty instead of a trust relationship, and names the things every project invented on its own (fix rounds, rulings, standing authorization, amendments, local-branch delivery).

### Added
- **Human run sheet** (`templates/run_sheet.md`; `reviews/phase_<N>/run_sheet.md` per phase; `SPEC_DRIVEN_BUILD_FRAMEWORK.md` Done Definition; `HUMAN_GATES.md` Gate 3; `FACILITATOR.md` new state `PHASE_ACCEPTANCE_RUN`). The phase-level human acceptance criterion now has an artifact with an owner: the Spec Author writes the skeleton with the rubric, each ticket's SWE fills in its section as it merges, the human executes and signs it against a real boot from a clean clone, and the Phase Reviewer blocks the phase on an unsigned sheet. Sections need proof the check ran and a negative control.
- **Testing steps as structured fields.** `prompts/swe.md` emits `testing_steps`; `prompts/tester.md` walks them as written and emits `testing_steps_followable`; the Facilitator quotes both in full at every PR gate and refuses to present a gate without them.
- **Facilitator verification duty** (`FACILITATOR.md`, "Verification of subagent claims", operating principles 8–11). Every subagent claim is re-established by the Facilitator's own tool call before a gate: re-run the suite, re-run the greps, `ls` the file, read the PR head from the API and confirm it matches local and origin, re-read the PR description against the branch after every push. Mechanical checks may be substituted by the Facilitator when a role dies; adversarial roles never.
- **Fix rounds** (`FIX_ROUND` state; `reviews/phase_<N>/TICKET-<NNN>_TO_FIX_round<R>.md`). Findings go to the human for a ruling, then to the Test Author to become red tests in new files, then to the SWE, then to the same reviewer for a delta review with its own prior report attached. Three rounds on one ticket escalates to a scope or spec concern.
- **Ruling gate and standing authorization** (`HUMAN_GATES.md`, `FACILITATOR.md`). The human rules on each finding (`B-n`/`N-n`): fix now, defer, route to Spec Author; only the human rules or ratifies. Standing authorization is a recorded, scoped, logged way to auto-advance clean mechanical gates. It can never cover the step walk on the last ticket of a phase, the phase acceptance run, a ruling, or a spec/rubric approval.
- **Stage plan** in `state.json`: one boolean per state per ticket; a ticket cannot enter `MERGE` with an earlier box unticked. Plus closed vocabulary for `current_state`, an object-only `open_human_gate`, no narrative, and phase-end compaction to `.facilitator/archive/`.
- **`RUBRIC_AUTHORING` state** and Spec Author rubric mode. The review rubric is produced after spec approval and before any review, with a **fixture allowlist** (deliberate fake tokens and forbidden names in immutable tests that greps skip) and a **mutation list** (per AC, the change its test must catch). Every hard-constraint grep is proven against planted bad code before the rubric is approved.
- **Amendments** (`SPEC_DRIVEN_BUILD_FRAMEWORK.md` "Versioning and Mid-Build Changes"; `FACILITATOR.md` "Amendments"). Micro-amendments (`A-<n>`, inline, dated, human-approved, applied verbatim by the Facilitator) and full amendments under `specs/amendments/`. A **guard census** precedes any amendment that changes scope or a pinned value.
- **Delivery mode** `github_pr` | `local_branch`, asked at bootstrap and recorded in state. Subagents write files only in both modes; git mutations belong to the Facilitator or the human. Prompts carry both variants. `gh` identity pinned at bootstrap.
- **Review artifact paths** table in `FACILITATOR.md`, including `pr_description_ticket_<NNN>.md`, `TICKET-<NNN>_merge_notes.md`, `phase_review.md`. Plain text only; scratch not committed into ticket PRs.
- **Subagent operating rules** passed to every role: one file or command per call, no git mutations, never edit `.gitignore`, reviewers don't read `reviews/`/`RETRO.md`/`.facilitator/`, kill only your own PIDs, one verifier at a time per working tree, stall handling by inspection.
- **Test discipline** in `prompts/test_author.md`, `prompts/tester.md`, `prompts/pr_reviewer.md`: real oracles (expected value never computed by the code under test, no substring-absence asserts, plausible fixtures), mutation seeds and mutation passes in a scratch copy, guard the whole class, same-class audits, hollow-test and regression checks, PR-description truth check (`claims_checked_rather_than_trusted`), test-run budget per role (Test Author runs only its files; SWE runs the full suite exactly once).
- **Phase Reviewer additions**: verifies the signed run sheet, fifth-instance sweep across ticket scopes, design-doc drift check, mutation list proof.
- **Decision log** (`templates/DECISIONS.md`, `D-<n>`). Specs, tickets and commits cite IDs instead of pasting rulings into spec bodies.
- **Brownfield discovery** (Spec Author discovery mode; `discovery/INVENTORY.md`, `GAPS.md`, `OPEN_QUESTIONS.md`; "Existing components" in the overview; integration contracts written from code, not prose).
- **Sub-phases and post-phase work** (`1a`/`1b`, `<N>-ff1`, `<N>-hotfix1`) run the full state machine including a run sheet.
- **Resume prompt** `templates/START_HERE.md` → `.facilitator/START_HERE.md`, refreshed at every phase boundary, dated, and distrusted when older than the latest log entry.
- **Native subagent install path** `templates/agents/` (one role file per worker role with a `tools:` allowlist plus a shared README) as an equivalent to pasted prompts.
- **Lightweight slash commands** `templates/commands/{ticket,review,ticket-status}.md`.
- **Worker model per role** recorded in state and `CLAUDE.md`.

### Changed
- `prompts/*.md`: no role commits, branches, pushes or opens PRs; every role ends with its structured block; SWE may add new test files only in fix rounds and never edits existing tests, even on a mid-flight ruling.
- `prompts/phase_reviewer.md` report path is `reviews/phase_<N>/phase_review.md` (was `phase_reviewer.md`).
- `FACILITATOR.md` "Open questions for v0.2.0" replaced with what use answered and the 0.3.x questions.
- `verify_framework.py` reads the version from this file instead of hardcoding it.
- Removed the stale 0.2.0 transitional-mode note from `FACILITATOR.md` and the last pilot-project name from the cost-contract example.

### Design rationale
The lessons came from five projects and they rhymed. The Facilitator skipped a PR review on one ticket and nothing flagged it until the human asked. A `git push` printed success and pushed nothing, so a whole fix round was verified against commits that were not on the remote. PR descriptions drifted from their branches four times in one day. Every project ran fix rounds, and every project invented its own file name for them. Three projects granted the Facilitator some form of "keep going when green", and in one of them the Facilitator began labelling rulings "ratified" on its own. State files turned into prose; audit logs stopped within a week. And in two projects the per-ticket human gate degraded to reading a diff because the testing steps were prose in a PR body the orchestrator never had to show.

None of these were caught by the agent pipeline, because the agent pipeline was green. They were caught by a human walking steps, which is the point of the framework and was the least-specified part of it. 0.3.0 fixes that asymmetry: the human-run check is now an artifact with an owner at both levels, the Facilitator must verify rather than relay, and the things people were doing anyway (fix rounds, rulings, standing authorization, amendments, local delivery) have names, limits and file paths so the next project doesn't reinvent them.

### Migration from 0.2.0
- Add `delivery_mode`, `stage_plan`, `fix_rounds`, `amendments`, `standing_authorization`, `run_sheet`, and `worker_models` to `.facilitator/state.json`; the Facilitator offers to do this at startup.
- Create `reviews/phase_<N>/run_sheet.md` for the current phase from the template before the next PR gate; backfill sections from merged tickets' testing steps.
- Rename `reviews/phase_<N>/phase_reviewer.md` to `phase_review.md` if present.
- Start `DECISIONS.md`; move pasted rulings out of spec bodies as you touch them.
- Subagents that used to commit now write files only; the Facilitator does the git step. Nothing else in the structured outputs was removed, only added.

### Also in 0.3.0 (written 2026-07-18, previously listed as Unreleased)

#### Added
- **Phase-slicing + end-to-end "done" principle** (`SPEC_DRIVEN_BUILD_FRAMEWORK.md`: the Phase-plan bullet and the Done Definition prose). Phases must be sliced as end-to-end vertical feature slices, not horizontal layers; and a phase is not "done" until a human has exercised its new capability end-to-end through its user-facing surface — the UI in a local/Codespace run, or a scripted CLI/API session when there is deliberately no UI — against a real boot of the stack, not merely until the unit/contract suites are green. The Done Definition now mandates at least one human-run, whole-stack acceptance criterion as a first-class blocking gate.
- **PR/ticket-level completeness + testability requirement** (`AGENT_ROSTER.md`: PM, SWE, Tester, PR Reviewer sections; `prompts/pm.md`, `prompts/swe.md`, `prompts/tester.md`, `prompts/pr_reviewer.md`; `HUMAN_GATES.md` Gate 2; lightweight `ticket_implementer.md` / `ticket_reviewer.md` / `review_only.md`). Every PR must ship a complete, human-testable slice — no button wired to an endpoint that doesn't exist yet, no route or flag nothing turns on. PM must not sequence tickets so an intermediate PR ships a dangling half-built pair; if a slice can't fit one ticket, the unfinished half stays out of the human-facing surface until the completing ticket lands. SWE's PR description must include numbered, concrete testing steps a human can follow against a running instance. Tester — the first agent to actually run the app — now explicitly watches for dead ends during its end-to-end spot-check. PR Reviewer gets a seventh check (completeness/testability) plus a `completeness_check` structured-output field (mirrored in the lightweight reviewers' `completeness_concerns` field). `SPEC_DRIVEN_BUILD_FRAMEWORK.md`'s Done Definition now cross-references this as the same principle applied one level down.
- **Open-source readiness pass.** Added `LICENSE` (MIT). Extracted `HUMAN_GATES.md` as its own top-level document; inline references that used to name the original pilot project (e.g. a project-specific nickname for "gate 2") are now generic and cross-referenced from `AGENT_ROSTER.md`. Added fillable `templates/PROJECT_OVERVIEW.md` and `templates/RETRO.md` so the framework repo carries templates, not a specific project's filled-in artifacts. Added `lightweight/` (the ticket-scale adaptation pattern, generalized, plus its generic prompts) as a documented reference implementation. Removed the stray `yarn.lock` (no `package.json` in this repo). `README.md` and `USING_THE_FRAMEWORK.md` rewritten to address an external reader and point at the new templates.

#### Design rationale
Across three real phases the same defect class recurred and only ever surfaced at the human evidence run, never in the agent suites: missing CORS, unwired cross-origin API base URLs, cookie `SameSite`, compose/env boot-coherence, and streaming/SSE wiring. Agent tests inject env directly and mock the network, so "all behavioral-contract tests pass" repeatedly did not mean "the feature works when a person uses it," and the gaps became after-the-fact remediation loops fired *after* a phase review had already passed. Making the end-to-end, user-exercisable slice the *purpose* of a phase — rather than a nice-to-have a phase can declare "separable" and drop — forces the scope to include the surface that makes the feature real and promotes the human end-to-end gate from an optional evidence item to a blocking part of Done.

The phase-level Done Definition guarantees a *phase* isn't declared done until it's human-exercisable end to end, but nothing stopped an individual ticket's PR — days or weeks before phase end — from merging a dead end along the way, because its own tests were green and the diff looked clean in isolation. That gap matters because Gate 2 (PR merge) is the only human checkpoint most tickets get before merging into the branch every later ticket builds on. If Gate 2 can be satisfied by reading a clean diff instead of exercising the feature, it degrades into exactly the rubber-stamp `HUMAN_GATES.md` warns against. Requiring concrete testing steps in every PR description, and adding a matching completeness check to the PR Reviewer's cold-context pass, makes "is this actually done" mechanically checkable at the same granularity the human is actually asked to approve.

The open-source pass exists because the framework was written for one person's use and named a specific pilot project throughout; publishing it required turning those into generic templates and examples so an outside reader isn't looking at someone else's project details.

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
