# Agent Roster

The roster defines the agents in the build pipeline. Each agent has one job. Each agent operates in a fresh context with explicit inputs and outputs. No agent both produces work and decides whether that work is correct.

The roster is a forcing function: if you can't answer the four questions (job, inputs, outputs, failure mode) cleanly for an agent, that agent shouldn't exist. Roles that fail this test should collapse into another agent or be deleted.

This is a starting point. After running the pipeline through a few real features, revisit the roster. Some agents will turn out to have substantial role overlap; collapse them. Some single agents will turn out to be doing two different jobs poorly; split them.

## A note on the Facilitator

The seven roles below are the framework's *worker* roles — they produce the artifacts (specs, tickets, tests, code, reports) the framework runs on. As of framework v0.2.0, there is an eighth meta-role, the **Facilitator**, defined in `FACILITATOR.md`. Framework 0.3.0 gives the Facilitator four more duties learned from real projects: it **verifies every subagent claim** with its own tool call before presenting a gate, it keeps a **stage plan** so a skipped stage is visible as an unticked box, it runs **fix rounds** (findings become red tests via the Test Author before the SWE touches anything), and it holds the phase open until the human has executed the **run sheet** (PHASE_ACCEPTANCE_RUN).

The Facilitator is not a member of this roster. It does not produce any of the framework's artifacts. Its job is to *orchestrate* the seven worker roles: track project state, prepare invocation prompts, spawn each role as a subagent in fresh context, capture structured outputs, surface human gates, and maintain the audit trail.

In practice this means:

- When you (the human) work on a project, you primarily interact with the Facilitator. The Facilitator interacts with the worker roles.
- The worker roles remain unchanged from earlier framework versions. Their responsibilities, boundaries, and outputs are defined here, not in `FACILITATOR.md`.
- Each worker role's prompt template now includes a **structured output section** (YAML) that the Facilitator parses. The structured output is in addition to, not a replacement for, the prose deliverables.
- A worker role can still be invoked manually (paste the prompt into a fresh Claude Code session) for cases where the Facilitator is unavailable or unhelpful. The structured output section is harmless when read by humans.
- Roles ship as agents in the `spec-driven-build` plugin (`agents/<role>.md`, spawned as `spec-driven-build:<role>`, each pinned to its tier's model and reading its template from `prompts/`). Without the plugin, a role can still be run from its pasted prompt (`prompts/<role>.md`, filled in per invocation). Both carry the same structured output.
- Every role runs under the subagent operating rules in `FACILITATOR.md`: one file or command per tool call, no git mutations, reviewers don't read `reviews/` or `RETRO.md`, kill only your own PIDs, end with the structured block.

The Facilitator does not change *what* the worker roles do. It changes *who keeps track of which one runs when*. Read on for the seven worker roles.


---

## How to read each entry

Every entry has the same four sections:

- **Job:** one sentence describing what this agent does. If the sentence requires the word "and" to connect two distinct activities, the agent has two jobs and probably should be split.
- **Inputs:** the files, context, and prior-stage outputs this agent reads. Anything not listed here is unavailable.
- **Outputs:** the artifacts this agent produces. These are concrete files or structured responses, not vague "feedback."
- **Failure mode:** what counts as this agent doing its job badly. This is the criterion the next agent in the chain uses to detect upstream problems.

The roster is ordered by pipeline position, not importance.

---

## 1. Spec Author

**Job:** Translate a one-paragraph human feature description into a complete feature spec that downstream agents can act on.

The role runs in one of three modes, chosen by the Facilitator: **spec** (the default, below), **rubric** (after spec approval: produce `specs/PHASE_N_REVIEW_RUBRIC.md` and the skeleton of `reviews/phase_N/run_sheet.md`), and **discovery** (brownfield projects: inventory the existing codebase into `discovery/` before `PROJECT_OVERVIEW.md` exists).

**Inputs:**
- A short feature description from the human (1-3 paragraphs of intent).
- `PROJECT_OVERVIEW.md` — for hard constraints, project-level cost contracts, architecture.
- The current `PHASE_N_SPEC.md` — for phase-level constraints and ACs that the feature must respect.
- The current state of the codebase (to know what already exists).
- Any prior feature specs in the same phase (for consistency).

**Outputs:**
- `specs/phase-N/feature-NNN-<slug>.md` — a complete feature spec following the framework template, containing:
  - Feature goal (one paragraph).
  - Behavioral contracts (BC-1, BC-2, ...) specific to this feature.
  - Inherited hard constraints (referenced by ID from project overview).
  - Inherited or feature-specific cost contracts.
  - Acceptance criteria (mechanical, verifiable).
  - Out-of-scope list.
  - At least one **human-run acceptance criterion** per phase: a short numbered walk through the phase's user-facing surface (UI, or a scripted CLI/API session when there is deliberately no UI) against a real boot of the whole stack. These become the sections of the run sheet.
  - "Done definition" tying to behavioral contracts passing, the signed run sheet, and the human gate.
- In rubric mode: `specs/PHASE_N_REVIEW_RUBRIC.md` with executable hard-constraint greps (each proven against planted bad code), a **fixture allowlist** (the deliberate fake tokens and forbidden names in immutable tests that the greps must skip), and a **mutation list** (per AC, the one-line implementation change its test must catch); plus the run sheet skeleton from `templates/run_sheet.md`.
- In discovery mode: `discovery/INVENTORY.md`, `discovery/GAPS.md`, `discovery/OPEN_QUESTIONS.md`, and a draft `PROJECT_OVERVIEW.md` whose "Existing components" section is written from the inventory.

**Failure mode:**
- Spec is ambiguous or contradictory.
- Spec has no human-exercisable surface — nothing a person could click, run, or call at phase end. That is a scope error, not a documentation gap.
- Spec paraphrases a design doc or the overview instead of enumerating its requirements by ID; paraphrase is how a requirement gets dropped.
- A prohibition names its subject but not its scope ("do not use X" with no "where").
- Rubric written after the review it governs, or greps that have never caught anything.
- Behavioral contracts describe code structure ("the LoginForm component must call useAuthStore") instead of user-observable behavior ("submitting valid credentials results in a POST to /api/auth/login and navigation to /dashboard").
- Behavioral contracts are missing for substantive interactive elements (per the BC pattern's "needs a contract" criteria).
- Acceptance criteria are not mechanically verifiable.
- Out-of-scope list is empty or generic — the spec author didn't actively decide what to defer.
- Inherited constraints from project/phase aren't surfaced or referenced.

**Human gate before this agent's output proceeds:** No, in normal operation. Spec Author's output flows directly to PM and Test Author. The spec is sanity-checked indirectly at Gate 1 (plan approval) — if PM's plan reveals misunderstandings, that surfaces spec problems. Reinstate spec-level review temporarily if Spec Author starts producing low-quality specs; treat it as a tuning mechanism, not a permanent fixture.

---

## 2. PM

**Job:** Decompose an approved feature spec into a sequenced task list with clear definitions of done per task.

**Inputs:**
- The approved feature spec.
- `PROJECT_OVERVIEW.md` (for context only, not for groomming logic).
- The current state of the codebase.

**Outputs:**
- A task plan: ordered list of tasks, each with a one-sentence description and a "done when" criterion.
- An explicit handoff document for the Test Author: which behavioral contracts the Test Author should write tests for, in what order, with any preconditions noted.
- Per ticket: a **run sheet contribution** (which of the phase's human-run ACs this ticket's testing steps will feed) and a **deployed-state premise** (one sentence: what is true of the running system between this ticket's merge and the next). Structured output names the `first_human_exercisable_ticket`.

**Failure mode:**
- Tasks are too large (a single task implementing the entire feature) or too small (granularity below useful checkpoints).
- Tasks have unstated dependencies (Task 3 requires Task 5 to be done first, but the order says otherwise).
- Tasks reference unstated requirements (assumes architectural decisions not in the spec or project overview).
- Tasks introduce scope not in the spec.
- "Done when" criteria are vague ("it works" rather than "BC-3 test passes and no regression in existing tests").
- Sequencing leaves a dangling half-built pair — a task that wires up UI for a backend endpoint that a later task hasn't built yet, or vice versa. Each task's PR should leave the product in a state a human can actually exercise; if one end-to-end slice genuinely needs more than one task, keep the not-yet-wired half out of the human-facing surface (don't render it, don't link it) until the completing task lands, and say so in that task's "done when" or out-of-scope notes.
- The last ticket is the first time anything is human-exercisable. The end-to-end slice arrives early and widens.

**Human gate after this agent's output:** Yes. This is the merged "spec-and-plan gate" that combines verification of the task plan with a usefulness check on the spec. The reviewer reads the plan, then closes it and writes three concrete sentences describing what a user does with this feature when it's done. If those sentences come easily and feel substantive, the feature is well-motivated; proceed. If they feel forced or generic, the feature itself needs reconsideration before any code is written. ~5-7 minutes total.

---

## 3. Test Author

**Job:** Translate behavioral contracts from the feature spec into executable failing tests, written independently of how the SWE will implement the feature.

Test Author is the load-bearing agent of this entire framework. Bad tests here cascade through every downstream agent — SWE will produce code that passes meaningless tests, Tester will struggle to find what was missed, and the feature will ship broken in ways that look fine. Invest disproportionately in Test Author's prompt quality and the tests it produces.

**Inputs:**
- The approved feature spec (specifically, the behavioral contracts).
- The codebase as it exists *before* the SWE starts (so tests can correctly import existing types, services, etc.).
- The project's testing conventions: framework, mocking style, file organization, naming patterns, existing test examples.

**Outputs:**
- Test files for each behavioral contract.
- Each test must fail when run against the pre-SWE codebase. The agent's output includes the output of running the tests; any test that passes against unchanged code causes the agent's output to be rejected automatically.
- A "test manifest" mapping each BC to one or more test functions, so the Tester agent later can verify coverage.
- **Mutation seeds:** for at least one test per AC, the one-line implementation change that would make it fail. These seed the rubric's mutation list.
- Any additions to the rubric's fixture allowlist (file and reason) for deliberate fake tokens or forbidden names the tests must contain.
- In a fix round: the "fix now" findings from `reviews/phase_N/TICKET-NNN_TO_FIX_roundR.md` encoded as red tests in **new** test files, or a reasoned rejection of any finding whose proposed fix would change a behavioral contract.

**Oracle rules:**
- The expected value is never computed by the code under test.
- Never assert by the absence of a substring.
- Fakes validate the fields the cited API or schema actually requires; fixture data is semantically and calendar-plausible, because a golden file encodes whatever junk it was built from.
- A guard scoped to one element misses the same cause in siblings and ancestors; write the test at the level the defect lives.
- Run only your own test files. The full suite is the SWE's, once.

**Mandatory checklist for API-element BCs (the "five states"):**

For any behavioral contract describing an interaction that triggers a backend call, the tests must cover all five states:

1. **None / idle:** The element renders correctly when nothing has happened.
2. **Loading:** When the action is in flight, the UI indicates this. The user cannot trigger the action a second time during this state.
3. **Partial:** If the action returns data progressively (paginated, streamed, partial), partial responses are displayed correctly.
4. **Full success:** The action completes; UI reflects the result; state updates appropriately; any downstream effect (navigation, modal close) occurs.
5. **Error:** The action fails (network error, 4xx, 5xx, validation error). The user sees an actionable message. The element returns to a state where they can retry.

A test suite covering only state 4 is unacceptable. This is the failure mode that breaks shipped products in obvious ways.

**Failure mode:**
- Tests pass on the empty implementation (hollow tests).
- Tests are overly prescriptive about implementation details ("must call axios.get with this exact URL shape") rather than testing observable behavior.
- Tests miss any of the five states for an API-element BC.
- Tests use mocks set up to match any implementation (e.g., `expect(fetch).toHaveBeenCalled()` without asserting on arguments — the test passes whether the right URL was called or not).
- Tests don't actually run (broken imports, missing test setup).
- Tests don't follow the project's existing conventions (foreign style that's hard to maintain).
- Tests survive their own mutation seed (the test is hollow and the seed proved it).
- Expected values derived from the implementation, or assertions on what is *absent*.

**Constraint that follows from this agent:** The SWE agent may not modify test assertions or test logic in files this agent produces. Trivial fixes (import paths, typo corrections) are permitted but must be flagged in the PR description. A pre-merge CI check diffs the test files; substantive changes to assertions cause the PR to be rejected.

**No human gate after this agent:** The tests are the source of truth. They should be reviewable by the human, but the pipeline doesn't pause here by default — the human can intervene if the tests look wrong, but the normal flow goes directly from Test Author to SWE.

---

## 4. SWE

**Job:** Implement the tasks from the PM's plan such that the Test Author's tests pass, without modifying those tests. SWE may use gh issue comment to annotate existing tickets with observations relevant to that ticket's future work. SWE may not use gh issue create; new follow-up work surfaces via the PR description and requires human review before becoming a tracked item.

The SWE writes files only. It does not add, commit, branch, push, or open the PR; the Facilitator or the human does that at the gate, in whichever delivery mode (`github_pr` or `local_branch`) the project runs.

**Inputs:**
- The approved feature spec (for context).
- The PM's task plan.
- The Test Author's test files (read-only).
- The codebase.
- `PROJECT_OVERVIEW.md` — for hard constraints the SWE must not violate.

**Outputs:**
- Implementation code that makes the Test Author's tests pass.
- Additional unit tests for internal logic the Test Author didn't cover (allowed and encouraged).
- A summary of changes: files touched, dependencies added, any spec ambiguities encountered.
- Manual testing steps in the PR description **and** as the structured `testing_steps` field: numbered, concrete instructions a human can follow against a running instance — commands to run (copy-paste complete, environment variables inside), URLs to open, buttons to click, inputs to enter — with the expected result at each step, covering every acceptance criterion, written for someone who did not build the feature. This is what makes Gate 2 a real check instead of a code read; the Facilitator quotes the field verbatim at the gate.
- This ticket's section of `reviews/phase_N/run_sheet.md`: the subset of the testing steps a human re-runs at phase end.
- The PR description kept at `.facilitator/scratch/ticket_NNN_pr_description.md` so the Facilitator can diff it against the branch after every later push.
- One full-suite run, at the end, with its real output quoted. Before that, only this ticket's tests.
- A same-class audit: for each defect a finding names, every other instance of that class in the touched code, fixed or justified.

**Failure mode:**
- Modifies Test Author's tests to make them pass (CI catches this; agent should not attempt). This holds even when the spec owner has ruled mid-flight — the ruling goes through the Test Author. In a fix round the SWE may add a *new* test file only if the Test Author's red tests prove insufficient.
- Performs a git mutation (commit, branch, push, PR) from inside the role.
- Fixes one instance of a defect when the review named a class. Four instances take four rounds unless the SWE sweeps.
- Implementation passes tests but is brittle in ways the tests don't catch (handled by Tester downstream).
- Implementation violates hard constraints from project overview (handled by PR Reviewer).
- Implementation introduces dependencies or files not justified by any task in the plan.
- Tests pass with the *minimum possible code* — e.g., handler calls API but doesn't handle response, because the test only checked the call. (This is the "loading state never reset" failure mode and is partially caught by Tester.)
- Surfaces ambiguities in the spec by assuming an answer rather than flagging it.
- Ships a PR that looks complete but contains a dead end — a button wired to an endpoint that isn't built yet, a form that writes to a table that doesn't exist, a route or flag nothing turns on. If the ticket's own scope can't produce a full end-to-end slice, the unfinished half stays out of the human-facing surface entirely rather than shipping visible-but-non-functional.
- PR description has no testing steps, or steps too vague to actually follow ("verify it works" instead of concrete actions and expected results).

---

## 5. Tester

**Job:** Verify the SWE's implementation behaves correctly beyond what the pre-written tests check, focusing on coverage gaps, test integrity, and adversarial exploration.

**Inputs:**
- The feature spec.
- The Test Author's test files and manifest.
- The SWE's implementation.
- The running application (this agent operates an actual dev environment, not just reads code).

**Outputs:**
- A test report listing:
  - Coverage gaps: behaviors from the spec that no test covers.
  - Test integrity issues: tests that pass but don't meaningfully verify behavior (hollow tests that survived).
  - Failed adversarial cases: edge cases that broke the implementation (network errors, empty states, race conditions, malformed input).
  - Dead ends encountered while exercising the app: a control that renders but does nothing real (wired to an endpoint that doesn't exist, a flag nothing turns on). Tester is the first agent to actually run the app, so it's the cheapest place to catch these — before they reach PR Reviewer or the human at Gate 2.
- `testing_steps_followable`: whether the PR description's numbered steps, walked exactly as written against a running instance, produced the expected results. The Facilitator quotes this field verbatim at Gate 2. A step the Tester had to fix in its head is a failed step.
- A mutation pass: each mutation on the rubric's list applied in a scratch copy of the repo (never the working tree), with the result.
- `claims_checked_rather_than_trusted`: each SWE claim and how it was verified.
- If gaps or failures are found, the report feeds the fix round; findings get stable IDs for the human's rulings.

**Discipline:**
- Checks a claimed defect against the data before recording it; a discrepancy that won't reproduce twice is a note.
- Re-runs the full suite only if code changed since the SWE's quoted run; otherwise cites that run and its commit.
- Honours earlier Tester notes on the same ticket (prior rounds), appending `## Round R` to the same report.
- Stopping rule: after two fix rounds on the same guard or validation, remaining theoretical evasions become accepted notes unless an honest mistake by a real user could reach them.

**Failure mode:**
- Reports "no issues" when issues exist (false negative).
- Reports issues that aren't real (false positive — wasting SWE time).
- Limits scope to "running the pre-written tests" (which the CI already does — this agent is supposed to go further).
- Doesn't actually run the application — only reads code.
- Reports `testing_steps_followable: true` without having walked them as a stranger would.
- Runs the mutation pass in the working tree.

**Note on this role's evolution:** This agent's job overlaps with Test Author (writing missing tests) and PR Reviewer (verifying code quality). Watch for this. If after 5-10 features Tester's findings are mostly things Test Author should have caught or things PR Reviewer would have caught, collapse this role into one of those agents.

**Human gate after this agent:** No. Findings flow to SWE, who addresses them. Tester re-runs after SWE's fixes. Loop continues until Tester reports clean.

---

## 6. PR Reviewer

**Job:** Verify that the completed feature is safe to merge into the codebase, focusing on cross-cutting concerns and diff hygiene.

**Inputs:**
- The full PR diff against the base branch.
- `PROJECT_OVERVIEW.md` (especially hard constraints).
- The feature spec's acceptance criteria.
- The state of all prior phases' tests.

**Outputs:**
- Verdict (pass / partial / fail).
- A fix file if not pass.
- Confirmation that the regression pass succeeded (all prior phase tests still pass).
- Confirmation that hard-constraint greps return empty.
- Confirmation that cost contract estimates haven't worsened.
- Confirmation that the PR ships a complete, human-testable slice — no dead-end UI or calls to unbuilt endpoints — and that the manual testing steps in the PR description are concrete enough to follow without reading the diff (read the steps *before* the diff, as a stranger).
- Hard-constraint results from **both** the rubric's greps and the reviewer's own independently written greps for the same intent, compared; files on the rubric's fixture allowlist skipped.
- `claims_checked_rather_than_trusted`: every factual claim in the PR description, checked against the diff or by running the command. The PR body has no other cold reader.
- A same-class audit per defect found (count and locations, not the first instance).
- A hollow-test check: each AC and contract test shown to fail under the rubric's mutation.
- A regression check: nothing touched undoes an earlier ticket's constraint or contract compliance.
- On `request_changes` or `reject`: `reviews/phase_N/TICKET-NNN_TO_FIX_roundR+1.md` with stable IDs (`B-n` blocking, `N-n` non-blocking), evidence, and the smallest closing fix, for the human's rulings.
- On a fix round: a **delta review** with its own prior report attached, so interactions between fixes are seen; appended as `## Round R`.
- Design notes for later tickets, when the diff reveals something the next ticket should know.

**Failure mode:**
- Reads the diff but doesn't actually run the prior phase tests (cargo-culting "regression pass").
- Doesn't run the hard-constraint greps (the most mechanical and most important check).
- Approves changes that break tests in earlier phases.
- Doesn't catch obvious diff hygiene issues (dead code added, debug logging left in, large files committed accidentally).
- Misses cost regressions (e.g., a new LLM call added with no max_tokens, breaking the cost contract).
- Approves a PR that's technically correct but not actually exercisable yet (dead-end UI, a flag nothing turns on) or that ships with no usable testing steps for Gate 2.
- Trusts the PR description for facts the diff can contradict. In one real fix round, two of five findings were the PR body stating things the branch did not do.
- Reports one instance of a defect class and lets the next round find the next one.

**Human gate after this agent:** Yes. This is Gate 2 — human merges the PR. The agent's review is advisory; the human makes the final call. See `HUMAN_GATES.md`.

---

## 7. Phase Reviewer

**Job:** At the boundary between phases, verify that the cumulative work of all features in the just-completed phase satisfies the phase-level spec and rubric, and that nothing earlier has silently broken.

**Inputs:**
- All feature specs from the just-completed phase.
- `PHASE_N_SPEC.md` and `PHASE_N_REVIEW_RUBRIC.md`.
- `PROJECT_OVERVIEW.md`.
- The codebase in its current state.
- The full accumulated test suite from all phases.

**Outputs:**
- Phase-level verdict (pass / partial / fail).
- A `PHASE_N_TO_FIX.md` if not pass.
- Verification that all behavioral contracts across all features in the phase have passing tests.
- Verification that all phase-level acceptance criteria pass.
- Verification that cost contracts at phase scope are satisfied with real usage data.
- Confirmation that the cross-phase integration tests pass.
- Verification that `reviews/phase_N/run_sheet.md` is **signed** (date, environment, per-section result, proof each check ran, at least one negative control) and that its sections cover every human-run AC in the Done Definition. An unsigned or incomplete run sheet is a blocking finding on its own.
- A **fifth-instance sweep**: for each defect class any ticket's review found this phase (the Facilitator passes the class names only), the whole merged codebase grepped for instances that fell between ticket scopes.
- A design-doc drift check, if the project keeps one under `docs/plans/`.
- The rubric's mutation list, each one proven in a scratch copy.
- Report at `reviews/phase_N/phase_review.md`; on `request_changes`, `reviews/phase_N/PHASE_N_TO_FIX_roundR+1.md` with stable IDs and, per finding, which ticket or role it routes to.

**Failure mode:**
- Passes a phase whose run sheet is unsigned, or signed without proof the checks ran.
- Kills a process it did not start. This role boots the whole stack; it records the PIDs it starts and stops only those.
- Treats the phase as the sum of features without checking the seams (misses integration breakage between features).
- Doesn't run cost-contract verification queries against real data.
- Skips the regression pass (this is the most important phase-level check).
- Approves a phase where individual features pass but the phase-level integration is broken.

**Human gate around this agent:** Yes, on both sides. *Before* the Phase Reviewer runs, the human executes and signs the run sheet (PHASE_ACCEPTANCE_RUN, the "be a user" check from `HUMAN_GATES.md`, now scripted). *After*, the human reads the phase report. The Phase Reviewer's verdict is advisory; no standing authorization covers either side.

---

## Pipeline summary

```
Human writes 1-paragraph intent
    ↓
[1] Spec Author (spec mode) → phase/feature spec, incl. human-run ACs
    ↓ (human gate: review spec)
[1] Spec Author (rubric mode) → review rubric + run sheet skeleton   ← RUBRIC_AUTHORING
    ↓ (human gate: review rubric; greps proven against planted bad code)
[2] PM → task plan, run-sheet contributions, deployed-state premises
[3] Test Author → failing tests + mutation seeds  (runs in parallel with PM)
    ↓
Gate 1: Plan approval + usefulness check (~5-7 min)
    Reviewer reads the plan, closes it, writes three concrete
    sentences describing what a user does with this feature.
    If the sentences come easily and feel substantive, proceed.
    If they feel forced, the feature itself needs reconsideration.
    ↓
[4] SWE → implementation that makes tests pass, `testing_steps`, run sheet section
    ↓
[5] Tester → adversarial verification, walks the steps, `testing_steps_followable`
    ↓
[6] PR Reviewer → diff review + truth check + regression pass
    ↓
    ├─ findings? → Human ruling gate (fix now / defer / to Spec Author)
    │              → FIX_ROUND: Test Author encodes findings as red tests
    │                 → SWE → Tester → PR Reviewer (delta) → back here
    ↓
Gate 2: PR merge (~5-15 min)
    Human walks `testing_steps` against a running instance, then merges.
    ↓
... loop through all features in the phase ...
    ↓
Gate 3: PHASE_ACCEPTANCE_RUN — human executes and signs
    reviews/phase_N/run_sheet.md against a clean-clone boot (~15 min).
    Never covered by a standing authorization.
    ↓
[7] Phase Reviewer → signed run sheet verified + cross-feature
    integration + phase rubric + fifth-instance sweep
    ↓ (human gate: read phase report)
Move to next phase
```

Two gates per feature plus one per phase. The human's job is gate-keeping, not implementation. Estimated human time per feature: 15-25 minutes of focused attention. Estimated human time per phase: an additional 15 minutes.

Across a 100-feature project, this is roughly 30-45 hours of human review work over the project lifetime — the rhythm of an engaged engineering manager, not a fatigued reviewer.

---

## Open questions after five projects

The roster has now run on five real projects, one of them through more than twenty phases. The first-run questions (does Spec Author earn its place, what tracks state, what happens when an agent fails) are answered: Spec Author stays, the Facilitator's state file and stage plan track state, and a failed agent is handled by the Facilitator verifying the tree and asking the human. What remains open:

1. **Does the stage plan get ticked reflexively?** It exists because a skipped PR review went unnoticed. A checklist that is ticked without the state's exit condition being met is worse than none. Watch for a tick with no artifact behind it.

2. **Is three fix rounds the right ceiling before the Facilitator escalates?** One ticket took seven rounds across two PRs. Three is a guess at where "fix" becomes "respec".

3. **Does the run sheet stay honest when one human writes the spec, walks the sheet, and signs it?** The sheet is the only test the agents can't run, and a single-person project has no second signature.

4. **Should Tester and PR Reviewer collapse on small tickets?** Observed deviations, recorded here as data and not as a recommendation: one project dropped the Tester after its first sub-phase and had the Facilitator do the mechanical re-checks; another collapsed per-ticket PR review into a single phase review from its fifth phase on. Both projects shipped. Neither measured what the dropped role would have caught. The roster keeps both roles until someone does.

---

## What this roster deliberately does not include

For reference, agents considered and rejected:

- **Architecture Reviewer.** Rejected because architecture decisions live in `PROJECT_OVERVIEW.md` and are enforced via hard constraints — adding a per-feature architecture review is over-engineering.
- **Performance Reviewer.** Rejected for v1; performance issues are caught at the human gate. Add this agent only if performance becomes a recurring failure.
- **Documentation Author.** Rejected because docs should be produced as part of features, not as a separate pass — separating docs from code produces stale docs.
- **Cost Analyst.** Folded into Cost Contracts as a framework concept, with verification handled by PR Reviewer and Phase Reviewer. Doesn't need its own agent.
- **Security Reviewer.** Rejected for v1; security concerns are encoded as hard constraints in project overview. Add if security becomes a recurring concern.

If any of these come up repeatedly in practice, add them. Otherwise, resist the urge.
