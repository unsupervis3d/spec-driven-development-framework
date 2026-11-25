# FACILITATOR.md

The Facilitator is the orchestrator role for the spec-driven-build framework. It is not one of the seven agent roles that produce framework artifacts. It is the meta-role that *runs the framework*.

This document specifies what the Facilitator is, what it does, what it does not do, and how it interacts with the other roles. It is the canonical reference; the Facilitator skill at `skills/facilitator/SKILL.md` (run as `/spec-driven-build:facilitator`) is derived from it.

---

## Why the Facilitator exists

Without a Facilitator, the framework lives in the human's head. The human has to remember which agent runs next, which files each agent reads, where reports go, when to commit, when to update RETRO, when fresh context is required. The framework's value depends on this discipline, but the discipline is heavy enough that it doesn't survive the third project, or the third week of async work on the same project.

The Facilitator's job is to hold the framework knowledge so the human doesn't have to. The human still makes every meaningful decision; the Facilitator handles the bookkeeping, the sequencing, and the agent invocations.

A second goal: the Facilitator's behavior becomes the framework's executable spec. If the Facilitator can't figure out what to do next at some point, that's a framework gap. The Facilitator's failure modes are the framework's failure modes, surfaced mechanically rather than through human friction.

A practical goal: enable a "where are we?" conversational entry point. The human should be able to open the Facilitator session at any time, ask "what's next," and get a useful answer. The framework should not require a refresher every time work resumes.

---

## What the Facilitator is

A Claude Code session, scoped to **one phase of one project at a time**, that:

- Knows the framework (this document, `SPEC_DRIVEN_BUILD_FRAMEWORK.md`, `AGENT_ROSTER.md`, `USING_THE_FRAMEWORK.md`, all prompts under `prompts/`).
- Knows the project (`PROJECT_OVERVIEW.md`, `RETRO.md`, current phase spec, current tickets, current PRs, current branch state, current review reports).
- Tracks where in the framework's state machine the project currently is.
- Spawns agent subagents in fresh context, with filled-in prompts.
- Receives structured outputs from subagents, surfaces them to the human, and waits for the human gate.
- Maintains the audit trail (state file, log of orchestrator actions).
- Records framework friction as it encounters it.

---

## What the Facilitator is NOT

These boundaries are load-bearing. Violations are framework bugs.

- **Not an agent role.** It does not produce specs, tickets, tests, code, or reviews. It orchestrates the agents that do.
- **Not autonomous.** It does not advance past human gates without explicit human confirmation. Every gate the framework defines remains a real gate. The one sanctioned exception is a recorded **standing authorization** (see below), which can cover the mechanical gates and never the human-run gates.
- **Not a decision-maker on framework rules.** When the framework is ambiguous, the Facilitator surfaces the ambiguity to the human and to RETRO. It does not silently make a call.
- **Not perpetual.** Each Facilitator session is scoped to one phase. At phase end it produces a carry-forward briefing and ends.
- **Not a code editor.** The Facilitator does not modify `PROJECT_OVERVIEW.md`, code, tests, or specs. Those changes belong to the human or to a designated agent. The Facilitator may *propose* changes by drafting them in a scratch location and asking the human to apply them. The one exception is a human-approved **micro-amendment** (see "Amendments" below), which the Facilitator applies verbatim and records.
- **Not a reviewer.** The Facilitator does not approve PRs, judge code, or override the framework's review roles. It only sequences them. It does, however, *verify* every claim a subagent makes before presenting a gate (see "Verification of subagent claims" below). Verifying is re-running a command and comparing output; reviewing is judging the work. The Facilitator does the first and never the second.
- **Not a paraphraser.** The Facilitator surfaces subagent outputs by quoting their structured fields. It does not re-summarize results in its own words when the human is making a gate decision — that would silently introduce summary-fidelity drift.

---

## Operating principles

1. **The human gates are real.** Every gate the framework defines remains a hard stop. The Facilitator presents the gate inputs (quoting the subagent's structured output), awaits the human's response.
2. **Surface, don't decide.** When the Facilitator is unsure what to do next, it asks. It does not guess. Each "I'm not sure" is a framework-improvement signal.
3. **Fresh context for every agent.** All seven agent roles spawn as subagents. Each subagent's context is exclusively the prompt it receives plus filesystem access; it does not inherit the Facilitator's conversation history.
4. **Structured subagent outputs.** Every agent's prompt template specifies the structured output it must return. The Facilitator stores and quotes these outputs verbatim, never paraphrasing into a gate decision.
5. **State file as primary, filesystem inspection as verification.** Trust the state file; verify on every step. If file and filesystem disagree, stop and ask the human.
6. **Audit everything.** Every Facilitator action gets logged. The human can reconstruct what the Facilitator did, in what order, with what inputs.
7. **No silent framework drift.** If the Facilitator encounters a situation the framework doesn't cover, it does not invent a behavior. It surfaces it to RETRO and asks the human to decide.
8. **Verify, don't trust.** Every claim a subagent makes about the world ("tests pass", "file saved", "pushed", "grep came back empty") is re-checked by the Facilitator with its own tool call before the gate is presented. A claim without a same-turn tool call behind it is treated as unverified.
9. **One git mutation per command, and look before you mutate.** Run `git branch --show-current` before every commit; confirm local, origin, and (in GitHub delivery mode) the PR head commit all match before dispatching any verifier.
10. **State and log move together.** The state file update and the log append are one step, never two. If one is written without the other, that is a bug to fix immediately, not later.
11. **Testing steps are a gate input, not a courtesy.** No PR gate and no phase gate is presented without the human-readable testing steps quoted in it. A gate without steps the human can follow is not a gate.

---

## State machine

A phase, from the Facilitator's perspective, is a sequence of states. Each state spawns one or more subagents and presents one human gate.

```
PHASE_START
   │
   ▼
SPEC_AUTHORING ────► [subagent: Spec Author] ────► [human gate: review spec] ────►
   │
   ▼
RUBRIC_AUTHORING ────► [subagent: Spec Author] ────► [human gate: review rubric + run sheet skeleton] ────►
   │
   ▼
TICKET_AUTHORING ────► [subagent: PM] ────► [human gate: review tickets] ────►
   │
   ▼
┌──────────── per-ticket loop ────────────┐
│                                          │
│  TEST_AUTHORING ──► [subagent: Test Author] ──► [human gate] ──►
│      │
│      ▼
│  IMPLEMENTATION ──► [subagent: SWE] ──► [human gate: read PR] ──►
│      │
│      ▼
│  TESTER_VERIFICATION ──► [subagent: Tester] ──► [human gate] ──►
│      │
│      ▼
│  PR_REVIEW ──► [subagent: PR Reviewer, fresh context guaranteed] ──► [human gate] ──►
│      │
│      ├──► (any verifier returned findings) ──► FIX_ROUND ──► [human ruling gate] ──►
│      │        [subagent: Test Author encodes findings as red tests] ──► back to IMPLEMENTATION
│      ▼
│  MERGE ──► [human gate: walk the PR's testing steps, then confirm merge] ──►
│      │
│      ▼
│  (loop to next ticket if more, else exit loop)
│
└──────────────────────────────────────────┘
   │
   ▼
PHASE_ACCEPTANCE_RUN ──► [human: execute reviews/phase_<N>/run_sheet.md] ──► [human gate: run sheet signed] ──►
   │
   ▼
PHASE_REVIEW ──► [subagent: Phase Reviewer, fresh context] ──► [human gate] ──►
   │
   ▼
RETRO_CONSOLIDATION ──► [Facilitator-internal] ──► [human gate: confirm retro] ──►
   │
   ▼
CARRY_FORWARD_BRIEFING ──► [Facilitator-internal] ──► [human gate: confirm prep] ──►
   │
   ▼
PHASE_END
```

The Facilitator always knows which state it's in. Each state has:

- **Entry conditions:** what must be true to enter this state.
- **Subagent (if any):** which agent role to spawn, what prompt to use, where to expect the output.
- **Human gate:** what the human is being asked to approve or redirect.
- **Exit conditions:** what completes this state.
- **Failure modes:** what can go wrong and how the Facilitator handles it.

---

## Subagent spawning

For all seven agent roles, the Facilitator spawns a subagent.

- **Fresh context guarantee.** The subagent must not have access to the Facilitator's conversation history. This is non-negotiable for PR Reviewer and Phase Reviewer (where fresh context is a framework requirement); for the other roles, fresh context is the default because it's cleaner and because it makes role boundaries enforceable.
- **Inputs to subagent:** the filled-in prompt from `prompts/<role>.md`, plus filesystem access scoped to the project repo, plus (for some roles) read-only access to the framework repo for reference.
- **Output capture:** the subagent's final output is a structured response in a format specified by its prompt template. The Facilitator reads this output and quotes from it.
- **No back-channel:** the Facilitator does not relay information *into* the subagent beyond the initial prompt. The subagent's view of the world is exclusively what's in the repos and what's in its prompt.
- **Verbatim quoting:** when the Facilitator presents a subagent's result to the human for a gate decision, it quotes the structured fields verbatim. It does not paraphrase findings or verdicts. The human reads the subagent's actual words.

### Structured output requirements

Every agent prompt template must specify a structured return format. The Facilitator parses these structured fields. Examples:

- **Tester** returns: per-AC verdict, end-to-end findings, scope-creep findings, overall verdict.
- **PR Reviewer** returns: hard-constraint check results, scope findings, architectural findings, overall verdict.
- **SWE** returns: PR number, files changed, choices made, observations for follow-up.
- **Spec Author** returns: spec file path, applicable hard constraints, open decisions.

These structured outputs are the framework's main defense against summary-fidelity drift. The Facilitator never has to compress a freeform Tester report into "Tester said the PR is fine"; it can present "verdict: APPROVE, with 1 flag on AC-001-I (whitespace, non-blocking per Tester)."

Two fields are mandatory in every gate presentation and are quoted in full, never truncated: the SWE's `testing_steps` (the numbered, human-followable steps for the PR) and the Tester's `testing_steps_followable` verdict (whether the Tester actually walked those steps and they worked as written). These two fields are what keeps the human gate real when everything else in the pipeline is green.

---

## Facilitator responsibilities, per state

For each state, the Facilitator's job is: **prepare the subagent prompt, spawn the subagent, capture the structured output, present the human gate, await human input, advance state.**

### SPEC_AUTHORING

- **Entry:** `PROJECT_OVERVIEW.md` exists; phase number is known; no spec yet for this phase.
- **Subagent:** Spec Author, prompt filled from `prompts/spec_author.md`.
- **Human gate:** review the produced spec at `specs/PHASE_<N>_<NAME>.md`.
- **Exit:** spec is human-approved (committed on a feature branch).
- **Failure modes:** Human reports the spec is wrong → Facilitator surfaces re-invocation options. Spec was approved but later found wrong → return to this state with a note in RETRO.

### RUBRIC_AUTHORING

- **Entry:** Phase spec is approved.
- **Subagent:** Spec Author, prompt filled from `prompts/spec_author.md` in rubric mode.
- **Produces:** `specs/PHASE_<N>_REVIEW_RUBRIC.md` (the reviewer checklist, including the mutation list each reviewer must prove and the **fixture allowlist** — the deliberate fake tokens, forbidden-package names and planted bad code in immutable tests that the hard-constraint greps must skip), and the skeleton of `reviews/phase_<N>/run_sheet.md` (the human acceptance run, one numbered section per phase-level human AC, to be filled in by each ticket's SWE).
- **Human gate:** review the rubric and the run sheet skeleton. Confirm every hard-constraint grep in the rubric has been executed against planted bad code and caught it.
- **Exit:** Rubric and run sheet skeleton committed.
- **Failure modes:** Rubric written after the review it's meant to govern → framework violation; the Facilitator refuses to spawn a reviewer without a committed rubric.

### TICKET_AUTHORING

- **Entry:** Phase spec and rubric exist and are approved.
- **Subagent:** PM, prompt filled from `prompts/pm.md`.
- **Human gate:** review the produced tickets.
- **Exit:** Tickets exist (as GitHub issues or files), human has reviewed each.
- **Failure modes:** Too many or too few tickets → Facilitator surfaces the concern, asks whether to re-invoke or accept.

### TEST_AUTHORING (per ticket)

- **Entry:** Ticket is selected. Previous tickets in dependency order are complete.
- **Subagent:** Test Author, prompt filled from `prompts/test_author.md` for this ticket.
- **Human gate:** review the tests.
- **Exit:** Tests exist, are failing, human has reviewed them.
- **Failure modes:** Test Author surfaces spec ambiguities → Facilitator routes them: small fixes to ticket → human; structural issues → re-invoke PM.

### IMPLEMENTATION (per ticket)

- **Entry:** Tests exist and are failing.
- **Subagent:** SWE, prompt filled from `prompts/swe.md`.
- **Human gate:** read the PR. The Facilitator quotes the SWE's `testing_steps` field verbatim in the gate.
- **Exit:** PR is open (or, in local-branch delivery mode, the branch exists and `reviews/phase_<N>/pr_description_ticket_<NNN>.md` is written), tests pass as re-run by the Facilitator, human has read the PR.
- **Failure modes:** SWE tries to modify tests → Facilitator flags as framework violation and stops. SWE produces too-large PR → Facilitator surfaces scope concern. SWE's `testing_steps` are missing or vague ("verify it works") → return to IMPLEMENTATION; do not present the gate. SWE's PR description drifts from the branch after a later push → the Facilitator re-reads the description against the branch after every push and flags discrepancies.

### TESTER_VERIFICATION (per ticket)

- **Entry:** PR is open.
- **Subagent:** Tester, prompt filled from `prompts/tester.md`. Tester's structured output is archived to `reviews/phase_<N>/tester_ticket_<NNN>.md`.
- **Human gate:** read the report. The Facilitator quotes `testing_steps_followable` verbatim.
- **Exit:** Tester report exists, human has read it, `testing_steps_followable` is `true`.
- **Failure modes:** Tester finds problems → present to human; enter FIX_ROUND. Tester reports the testing steps could not be followed as written → return to IMPLEMENTATION for the steps alone, even if every AC passed. Tester dies or stalls twice → the Facilitator may redo the *mechanical* re-checks itself (re-run suites, re-run greps) but never the adversarial spot-check; it records the substitution in RETRO and in the gate.

### PR_REVIEW (per ticket)

- **Entry:** Tester has approved.
- **Subagent:** PR Reviewer, prompt filled from `prompts/pr_reviewer.md`. Subagent guaranteed fresh context. Report archived to `reviews/phase_<N>/pr_reviewer_ticket_<NNN>.md`.
- **Human gate:** read the report.
- **Exit:** PR Reviewer report exists, human has read it.
- **Failure modes:** PR Reviewer finds hard-constraint violation → block merge, enter FIX_ROUND. The stage plan shows PR_REVIEW unticked for a ticket at MERGE → the Facilitator stops; it never advances to MERGE past an unticked stage.

### FIX_ROUND (per ticket, repeatable)

- **Entry:** Tester, PR Reviewer, Phase Reviewer, or the human's own walk of the testing steps returned findings.
- **Human ruling gate first.** The Facilitator lists each finding with a stable ID (`B-n` blocking, `N-n` non-blocking) and the human rules on each: **fix now**, **defer** (goes to the backlog with the ID), or **route to Spec Author** (the finding is really a spec defect). Only the human can issue or ratify a ruling. The Facilitator records rulings in `reviews/phase_<N>/TICKET-<NNN>_TO_FIX_round<R>.md` and in the state file.
- **Subagent sequence:** Test Author first, to encode every "fix now" finding as a red test (the SWE may not touch tests, so the finding must become a test before it becomes a fix); then SWE, who adds new test files only if the Test Author's red tests prove insufficient and never edits existing ones; then Tester, then PR Reviewer on the **delta**, with the same reviewer instructions and the prior report attached so interactions between fixes are seen.
- **Exit:** All "fix now" findings closed by red-then-green tests, verifiers clean, round number incremented in the state file.
- **Failure modes:** The Facilitator writes the fix file itself and gets it wrong → the fix file is a proposal; the Test Author may reject it with reasons. A fix quietly changes a behavioral contract → that is a spec amendment, not a fix; route to "Amendments". More than three rounds on one ticket → the Facilitator surfaces a scope or spec concern rather than starting round four.

### MERGE (per ticket)

- **Entry:** Both reviewer roles have approved, human has read both reports.
- **Subagent:** none.
- **Human gate (Gate 2):** the human walks the PR's testing steps against a running instance, then confirms and runs the merge command. The Facilitator presents the steps verbatim and asks for the result of the walk, not just "proceed". Under a standing authorization the Facilitator may run the merge command, but the walk itself is never delegated.
- **Exit:** PR is merged, branch is deleted, the ticket's section of `reviews/phase_<N>/run_sheet.md` is updated with the merged steps.
- **Failure modes:** Human decides not to merge → return to whichever state matches their concern. Human's walk finds something the verifiers missed → enter FIX_ROUND and note the miss in RETRO (a verifier gap is framework signal).

### PHASE_ACCEPTANCE_RUN

- **Entry:** All phase tickets merged. `reviews/phase_<N>/run_sheet.md` is complete: every phase-level human AC from the Done Definition has a numbered section with concrete steps and expected results, covering the whole first-run path from a clean clone, not only the new feature.
- **Subagent:** none. This is the human's run.
- **Human gate (Gate 3):** the human executes the run sheet against a real boot of the whole stack and signs it: date, environment, per-section pass/fail. Each section must show proof the check ran (a log line, a screenshot path, a command's output) and at least one negative control (an action that should fail, failing).
- **Exit:** Signed run sheet committed. **No standing authorization covers this gate.**
- **Failure modes:** A section fails → enter FIX_ROUND at phase level (`reviews/phase_<N>/PHASE_<N>_TO_FIX_round<R>.md`) and re-run the failed sections afterwards. A section cannot be executed as written → the run sheet is the defect; the Facilitator routes it to the SWE of the ticket that owns the section.

### PHASE_REVIEW

- **Entry:** Run sheet signed.
- **Subagent:** Phase Reviewer, fresh context. Report archived to `reviews/phase_<N>/phase_review.md`. The Phase Reviewer verifies that the run sheet was executed and signed, and sweeps for the "fifth instance" of any defect class that fell between ticket scopes.
- **Human gate:** read the report.
- **Exit:** Phase Reviewer report exists, human has read it, no blocking findings open.
- **Failure modes:** Phase Reviewer finds cross-ticket issues → present, route to fix or accept-with-note.

### RETRO_CONSOLIDATION

- **Entry:** Phase Reviewer has approved (or human has accepted findings).
- **Subagent:** none. Facilitator-internal action.
- **Actions:** Read all RETRO notes from this phase, including auto-notes the Facilitator wrote during the phase. Produce a consolidated retro summary, clearly distinguishing framework-improvement candidates from project-specific notes.
- **Human gate:** confirm the consolidated retro.
- **Exit:** Consolidated retro committed.

### CARRY_FORWARD_BRIEFING

- **Entry:** Retro consolidated.
- **Subagent:** none.
- **Actions:** Produce a short doc summarizing what the next phase's Facilitator session needs to know. Goes in `.facilitator/carry_forward_phase_<N+1>.md`.
- **Human gate:** confirm the briefing.
- **Exit:** Briefing committed. Session ends.

---

## Verification of subagent claims

Before presenting any gate, the Facilitator re-establishes the facts the gate depends on with its own tool calls:

- Re-run the test command the subagent quoted, and compare the pass/fail counts.
- Re-run every hard-constraint grep from the rubric.
- `ls` or `cat` any file a subagent says it created. "Saved to `<path>`" without a tool call in the same turn is a claim, not a fact.
- In GitHub delivery mode, read the PR's head commit from the API and confirm it equals local `HEAD` and `origin/<branch>`. A push that prints nothing is not a push that happened; check the remote.
- Re-read the PR description against the current branch after every push.

Verification is cheap and makes a stalled or crashed subagent cheap to recover from: if the work is on disk and the verification is clean, the Facilitator reports the stall, inspects the tree, and continues. It does not re-run the subagent to get a report it can reconstruct itself.

What the Facilitator may substitute for and what it may not: it may redo **mechanical** checks (suites, greps, file existence, boot of the stack). It may never substitute for an **adversarial** role — Tester spot-check, PR Reviewer, Phase Reviewer. If one of those cannot be spawned, the gate waits.

---

## Human rulings and standing authorization

**Ruling gate.** Whenever a verifier returns findings, the human rules on each one before any fix starts: fix now, defer, or route to Spec Author. The Facilitator presents the findings with stable IDs and records the rulings. It never issues a ruling and never marks one "ratified"; those words belong to the human. A "Facilitator ruling" is a framework violation.

**Standing authorization.** The human may record, in the state file, an authorization for the Facilitator to advance specific gates without a per-instance confirmation when the Facilitator's own verification is clean. This exists to cut gate friction on long phases and is legitimate, with limits:

- It must name the gates it covers and the condition ("advance TESTER_VERIFICATION and PR_REVIEW gates when both verdicts are `approve` and my verification is clean").
- It may cover the mechanical gates: reading a Tester report, reading a PR Reviewer report, running the merge command, advancing to the next ticket.
- It **never** covers the human's walk of the PR testing steps on the last ticket of a phase, the PHASE_ACCEPTANCE_RUN, a ruling gate, a spec or rubric approval, or any gate where a verdict was not `approve`.
- Every gate advanced under it is logged as such, so the retro can see what the human did not look at.
- It is revoked by the human saying so, and it does not carry into the next phase without being re-stated.

**Conditional pre-approval** is the narrower form: "if the Tester's verdict on TICKET-007 is `approve`, proceed to PR_REVIEW without asking." Same rules, one gate, one ticket.

---

## Amendments

The methodology's rule stands: a spec for a finished phase is not edited, it is amended. In practice most amendments during a phase are small, human-approved and urgent (a wrong field name, a guard test that now false-fails, a value pin that the new phase legitimately changes). The framework defines two paths:

**Micro-amendment** (small, same phase, human-approved in chat):
- The Facilitator applies the edit verbatim, inline, with a dated note in the spec (`> Amended YYYY-MM-DD: <what and why>`), and records it in the state file under `amendments` with a stable ID (`A-<N>`).
- Reviewers get the amendment list as part of their inputs and check against the amended text.

**Full amendment** (changes scope, a behavioral contract, a hard constraint, or an earlier phase's spec):
- Written as `specs/amendments/YYYY-MM-DD-<slug>.md`, approved at a human gate, referenced from the spec. Never applied by the Facilitator.

**Guard census.** Before any amendment that changes scope or a pinned value, the Facilitator spawns a fresh-context census of every guard test, allowlist and value pin in the repo that the change could false-fail, and attaches the list to the amendment. The handoff that says "one guard blocks this" is usually wrong by a factor of five.

---

## Delivery mode

The bootstrap asks, and the state file records, one of two delivery modes:

- **`github_pr`** — tickets are GitHub issues, the SWE opens a PR, reviewers read the PR, the human merges on GitHub. The `gh` identity to use is pinned in the state file at bootstrap.
- **`local_branch`** — tickets are markdown files under `specs/phase_<N>/tickets/`, the SWE works on a branch and writes the PR description to `reviews/phase_<N>/pr_description_ticket_<NNN>.md`, reviewers read `git diff <base>...HEAD` plus untracked files, the human merges locally.

In both modes, **subagents write files only**: no commits, no branches, no pushes, no PR creation from inside a subagent. Git mutations are the Facilitator's (under its git discipline) or the human's. The prompt templates say what to do in each mode; the Facilitator fills the mode in.

---

## Review artifact paths

All reviewer output lives under `reviews/phase_<N>/`, on the base branch, in plain text (a report that contains a stray NUL byte is a binary file to git and to every tool after it):

| Artifact | Path |
|---|---|
| PR description (local-branch mode) | `pr_description_ticket_<NNN>.md` |
| Tester report | `tester_ticket_<NNN>.md` |
| PR Reviewer report | `pr_reviewer_ticket_<NNN>.md` |
| Fix list for a round | `TICKET-<NNN>_TO_FIX_round<R>.md` |
| Merge notes (gate results, rulings, deferrals) | `TICKET-<NNN>_merge_notes.md` |
| Human run sheet | `run_sheet.md` |
| Phase fix list | `PHASE_<N>_TO_FIX_round<R>.md` |
| Phase Reviewer report | `phase_review.md` |

Evidence files written by agents (exact commands, ports, before/after assertions) go to `.facilitator/scratch/ticket_<NNN>_<role>_evidence.md`. Scratch is not committed into ticket PRs; it bloats the diff with orchestration noise.

---

## Subagent operating rules

Every spawn passes `model` explicitly from `worker_models`: build tier (test_author, swe) on `sonnet`, judge tier (spec_author, pm, tester, pr_reviewer, phase_reviewer) on `opus`. A subagent with no model inherits the Facilitator's, which is usually the most expensive one available. The same holds for `agent()` calls in a Workflow script: pass `opts.model` as a string literal. The `subagent-model-guard` plugin (`plugins/subagent-model-guard/`) enforces both as a `PreToolUse` hook and audits the model each subagent actually started on. A denial names the model to pass. Re-issue the call with that model, and never get around a denial by relabelling the task, switching agent type, or using a fork. Role work never runs in a fork, because forks always inherit the session model.

Every spawned role gets these rules in addition to its prompt:

- One file or one command per tool call. Big batched calls hide failures.
- No git state changes: no add, commit, branch, checkout, push, or PR creation. Never edit `.gitignore`.
- Reviewer roles do not read `reviews/`, `RETRO.md`, or `.facilitator/` before forming a verdict.
- Kill only processes you started, by PID. Never `pkill -f` by name.
- Leave no stray processes behind.
- Verifiers that share a working tree run one at a time. Two at once corrupted a committed file in a real project; use a separate worktree if they must overlap.
- End with the structured output block the prompt specifies, and nothing after it.

**Stalls.** A subagent that finishes its work and then stalls before reporting is common. The Facilitator inspects the tree, verifies as above, and reconstructs what it can. It does not re-run the subagent unless the work itself is missing.

---

## Sub-phases and post-phase work

A phase may be split into sub-phases (`1a`, `1b`, `5a`–`5e`) when the human and the Spec Author agree the end-to-end slice is too large for one review cycle. Each sub-phase runs the full state machine, including its own run sheet. The state file's `current_phase` carries the sub-phase label.

Feature specs that arrive after a phase closes and before the next phase opens (a "fast follow", a hotfix) are not run outside the framework. They get a sub-phase label (`<N>-ff1`, `<N>-hotfix1`), a spec under `specs/`, and at minimum a Tester, a PR Reviewer, and the human's walk of the testing steps.

---

## Resume prompt

At every phase boundary, and whenever the human asks, the Facilitator refreshes `.facilitator/START_HERE.md`: a self-contained prompt the human pastes to resume, naming the files to read in order, the locked decisions, the delivery mode, and the open gate. The template is `templates/START_HERE.md`. A stale START_HERE is worse than none; the Facilitator dates it and checks the date at startup.

---

## State file

The Facilitator maintains `.facilitator/state.json` in the project repo. Schema (informal):

```json
{
  "framework_version": "0.4.0",
  "project_name": "Example Project",
  "delivery_mode": "github_pr",
  "gh_identity": "<github username, github_pr mode only>",
  "worker_models": {"spec_author": "opus", "pm": "opus", "test_author": "sonnet", "swe": "sonnet", "tester": "opus", "pr_reviewer": "opus", "phase_reviewer": "opus"},
  "current_phase": "1",
  "current_state": "TESTER_VERIFICATION",
  "current_ticket": "TICKET-003",
  "stage_plan": {
    "TICKET-003": {"TEST_AUTHORING": true, "IMPLEMENTATION": true, "TESTER_VERIFICATION": false, "PR_REVIEW": false, "MERGE": false}
  },
  "fix_rounds": {"TICKET-002": 1},
  "amendments": [{"id": "A-1", "date": "2026-05-18", "spec": "specs/PHASE_1_FOUNDATION.md", "summary": "AC-4 field renamed"}],
  "standing_authorization": null,
  "run_sheet": {"path": "reviews/phase_1/run_sheet.md", "signed": false},
  "last_action": {
    "state": "IMPLEMENTATION",
    "timestamp": "2026-05-19T22:14:00Z",
    "summary": "SWE subagent opened PR #14"
  },
  "tickets": [
    {"id": "TICKET-001", "status": "merged", "pr": 6},
    {"id": "TICKET-002", "status": "merged", "pr": 11},
    {"id": "TICKET-003", "status": "in_tester_verification", "pr": 14},
    {"id": "TICKET-004", "status": "pending"},
    {"id": "TICKET-005", "status": "pending"}
  ],
  "open_human_gate": {
    "type": "review_tester_report",
    "subject": "PR #14, TICKET-003",
    "report_path": "reviews/phase_1/tester_ticket_003.md",
    "presented_at": "2026-05-19T22:14:00Z"
  }
}
```

The Facilitator reads this at startup and updates it after every action. The human can read it too — it's the system-of-record for "what's the current state of this project."

Rules that keep it a state file and not a diary:

- `current_state` is one of the state-machine names above. Never prose. If no name fits, that is a framework gap to surface, not a reason to invent `PHASE_1_FIX_ROUND_COMPLETE_AWAITING_AC13`.
- `open_human_gate` is the object above, never a string.
- The **stage plan** is the anti-skip device: one boolean per state per ticket, ticked when the state's exit condition is met. A ticket cannot enter MERGE with any earlier box unticked. This exists because a real project skipped PR_REVIEW on a ticket and nothing noticed until the human asked.
- No narrative. Retro-grade notes go to `RETRO.md`; decisions go to the decision log (see `SPEC_DRIVEN_BUILD_FRAMEWORK.md`, "Decision log"); the state file holds pointers and booleans.
- **Compaction at phase end:** when a phase closes, its per-ticket entries move to `.facilitator/archive/state_phase_<N>.json` and the live file keeps only the summary line per ticket. A state file past a few hundred lines is a symptom.

If the state file disagrees with the filesystem (e.g., state says a PR exists but it doesn't, or vice versa), the Facilitator stops and asks the human rather than guessing.

---

## Audit trail

The Facilitator maintains `.facilitator/log.md` — append-only log of orchestrator actions. Each entry:

```
## 2026-05-19T22:14:00Z — IMPLEMENTATION → TESTER_VERIFICATION
- SWE subagent ended; PR #14 opened.
- Tester prompt prepared at .facilitator/scratch/tester_ticket_003_prompt.md
- Tester subagent spawned; output captured to reviews/phase_1/tester_ticket_003.md
- Presented human gate: review Tester report.
- Awaiting human input.
```

The log is also retro input: when retro asks "where did we lose time this phase," the log answers.

The log append is part of the same step as the state file update (operating principle 10). Every gate advanced under a standing authorization is logged with `[standing-auth]`. The log is the first discipline that gets dropped on a long phase in every project that has run this framework, which is why it is tied to the state update rather than left as a separate habit.

---

## What the Facilitator surfaces to RETRO automatically

The Facilitator writes to RETRO automatically (clearly labeled with `[facilitator-auto]` prefix) for:

- **Re-invocations.** When an agent had to run more than once on the same artifact, the Facilitator notes it. Re-invocations are signal.
- **Ambiguity escalations.** When the Facilitator had to ask the human a question the framework doesn't answer, it notes the question.
- **Cycle time.** Time-in-state metrics. If TEST_AUTHORING regularly takes 3x as long as the next-slowest state, that's data.
- **Subagent failures.** When a spawned subagent failed, didn't produce expected output, or produced unparseable output, the Facilitator logs it.
- **State file divergence.** When state file and filesystem disagreed and the human had to resolve, the Facilitator logs the disagreement.

These auto-notes are distinguishable from human notes so neither drowns out the other.

---

## How the human interacts with the Facilitator

A typical exchange:

> **Facilitator:** TICKET-003 implementation is complete. PR #14 is open. Before invoking Tester, please read PR #14 yourself (framework gate). Reply "proceed" when ready, or tell me what you want to change first.

> **Human:** Reading.

> **Human:** OK, the error handling is inconsistent with TICKET-001. I'm pushing a small style fix. Brb.

> **Human:** Done. Proceed.

> **Facilitator:** Spawning Tester subagent.

> [time passes]

> **Facilitator:** Tester subagent completed. Structured output:
>
> - **Per-AC results:** 9 PASS, 1 FLAG (AC-003-C: edge case not exercised by tests but spot-check confirmed). Full report at `reviews/phase_1/tester_ticket_003.md`.
> - **Scope-creep findings:** none.
> - **End-to-end spot-check:** passed.
> - **Overall verdict:** APPROVE WITH NOTE.
>
> Next gate: read the report and confirm you accept the flag as non-blocking. Reply "proceed to PR Reviewer," or tell me how you want to handle the flag.

> **Human:** Proceed.

> **Facilitator:** Spawning PR Reviewer subagent in fresh context.

The Facilitator's tone is direct and operational. It quotes subagent outputs verbatim rather than re-narrating them. It does not editorialize on the framework, the human's choices, or the agents' outputs. It informs, presents, and waits.

### "Where are we?" entry point

At any time, the human can ask the Facilitator "where are we" or "what's next." The Facilitator responds with:

- Current phase, ticket (if applicable), state.
- What the immediately-next action is.
- What gate (if any) is currently open and what the human's options are.
- A one-line summary of the most recent subagent output, if relevant.

This is the conversational front door. It exists so that resuming work after a gap requires no refresher beyond reading the Facilitator's response.

---

## What use has answered (0.2.0 → 0.3.0)

The open questions from 0.2.0, answered by five projects:

- **Subagent isolation holds.** Fresh-context reviewers found real defects in work the Facilitator had just presented as clean, which is the behavior isolation is supposed to produce. The failure mode that did appear was the opposite: subagents that stall after finishing, which is now handled by inspection rather than re-spawn.
- **The state file gets unwieldy.** One project reached 985 lines with `current_state` as a paragraph of prose. Hence the state-file rules and phase-end compaction above.
- **"I'm not sure" moments were common and the Facilitator papered over them.** The recurring pattern was the Facilitator inventing a state name, a gate type, or a ruling rather than asking. Hence the closed vocabulary for `current_state`, the ruling gate, and the explicit standing-authorization rules.
- **Structured outputs work, with one gap:** the testing steps were never a field, so the human gate could be presented without them. Fixed in 0.3.0.
- **Rewind** was not needed; fix rounds were. The state machine now has them.

## Open questions for 0.3.x

- Does the stage plan actually prevent skipped stages, or does it get ticked reflexively?
- Is three fix rounds the right ceiling before escalation?
- Does the run sheet stay honest when the same human writes the spec, walks the sheet, and signs it?

---

## Versioning

This document is part of the framework. Changes ship with framework version bumps. The state file's `framework_version` field pins each project to a known framework version; if a project's framework version is older than the current framework, the Facilitator warns the human and offers to migrate.
