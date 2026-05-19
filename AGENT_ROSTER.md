# Agent Roster

The roster defines the agents in the build pipeline. Each agent has one job. Each agent operates in a fresh context with explicit inputs and outputs. No agent both produces work and decides whether that work is correct.

The roster is a forcing function: if you can't answer the four questions (job, inputs, outputs, failure mode) cleanly for an agent, that agent shouldn't exist. Roles that fail this test should collapse into another agent or be deleted.

This is a starting point. After running the pipeline through a few real features, revisit the roster. Some agents will turn out to have substantial role overlap; collapse them. Some single agents will turn out to be doing two different jobs poorly; split them.

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
  - "Done definition" tying to behavioral contracts passing and human gate.

**Failure mode:**
- Spec is ambiguous or contradictory.
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

**Failure mode:**
- Tasks are too large (a single task implementing the entire feature) or too small (granularity below useful checkpoints).
- Tasks have unstated dependencies (Task 3 requires Task 5 to be done first, but the order says otherwise).
- Tasks reference unstated requirements (assumes architectural decisions not in the spec or project overview).
- Tasks introduce scope not in the spec.
- "Done when" criteria are vague ("it works" rather than "BC-3 test passes and no regression in existing tests").

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

**Constraint that follows from this agent:** The SWE agent may not modify test assertions or test logic in files this agent produces. Trivial fixes (import paths, typo corrections) are permitted but must be flagged in the PR description. A pre-merge CI check diffs the test files; substantive changes to assertions cause the PR to be rejected.

**No human gate after this agent:** The tests are the source of truth. They should be reviewable by the human, but the pipeline doesn't pause here by default — the human can intervene if the tests look wrong, but the normal flow goes directly from Test Author to SWE.

---

## 4. SWE

**Job:** Implement the tasks from the PM's plan such that the Test Author's tests pass, without modifying those tests.

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

**Failure mode:**
- Modifies Test Author's tests to make them pass (CI catches this; agent should not attempt).
- Implementation passes tests but is brittle in ways the tests don't catch (handled by Tester downstream).
- Implementation violates hard constraints from project overview (handled by PR Reviewer).
- Implementation introduces dependencies or files not justified by any task in the plan.
- Tests pass with the *minimum possible code* — e.g., handler calls API but doesn't handle response, because the test only checked the call. (This is the "loading state never reset" failure mode and is partially caught by Tester.)
- Surfaces ambiguities in the spec by assuming an answer rather than flagging it.

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
- If gaps or failures are found, the report becomes a fix-file-style document for the SWE to address.

**Failure mode:**
- Reports "no issues" when issues exist (false negative).
- Reports issues that aren't real (false positive — wasting SWE time).
- Limits scope to "running the pre-written tests" (which the CI already does — this agent is supposed to go further).
- Doesn't actually run the application — only reads code.

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

**Failure mode:**
- Reads the diff but doesn't actually run the prior phase tests (cargo-culting "regression pass").
- Doesn't run the hard-constraint greps (the most mechanical and most important check).
- Approves changes that break tests in earlier phases.
- Doesn't catch obvious diff hygiene issues (dead code added, debug logging left in, large files committed accidentally).
- Misses cost regressions (e.g., a new LLM call added with no max_tokens, breaking the cost contract).

**Human gate after this agent:** Yes. This is Squid's "gate 2" — human merges the PR. The agent's review is advisory; the human makes the final call.

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

**Failure mode:**
- Treats the phase as the sum of features without checking the seams (misses integration breakage between features).
- Doesn't run cost-contract verification queries against real data.
- Skips the regression pass (this is the most important phase-level check).
- Approves a phase where individual features pass but the phase-level integration is broken.

**Human gate after this agent:** Yes — and this is the 15-minute "be a user" check from the framework. The Phase Reviewer's verdict is advisory; the human actually uses the product as a user would before declaring the phase complete.

---

## Pipeline summary

```
Human writes 1-paragraph intent
    ↓
[1] Spec Author → feature spec
    ↓ (no gate — spec sanity-checked indirectly via plan review)
[2] PM → task plan
[3] Test Author → failing tests  (runs in parallel with PM)
    ↓
Gate 1: Plan approval + usefulness check (~5-7 min)
    Reviewer reads the plan, closes it, writes three concrete
    sentences describing what a user does with this feature.
    If the sentences come easily and feel substantive, proceed.
    If they feel forced, the feature itself needs reconsideration.
    ↓
[4] SWE → implementation that makes tests pass
    ↓
[5] Tester → adversarial verification
    ↓ (internal loop with SWE if issues)
[6] PR Reviewer → diff review + regression pass
    ↓
Gate 2: PR merge (~5-15 min)
    ↓
... loop through all features in the phase ...
    ↓
[7] Phase Reviewer → cross-feature integration + phase rubric
    ↓
Gate 3: "Be a user" (~15 min per phase)
    ↓
Move to next phase
```

Two gates per feature plus one per phase. The human's job is gate-keeping, not implementation. Estimated human time per feature: 15-25 minutes of focused attention. Estimated human time per phase: an additional 15 minutes.

Across a 100-feature project, this is roughly 30-45 hours of human review work over the project lifetime — the rhythm of an engaged engineering manager, not a fatigued reviewer.

---

## Open questions for the first run

These are uncertainties that the roster can't resolve from the armchair. Track them; revisit after the first phase of real use.

1. **Does Tester earn its keep, or do Test Author and PR Reviewer cover its work?** Track Tester's findings across the first 10 features. If <20% of Tester's findings are unique (not also surfaced by Test Author's tests or PR Reviewer's review), collapse Tester into PR Reviewer.

2. **Does Phase Reviewer earn its keep, or is it redundant after good per-feature reviews?** Track whether Phase Reviewer catches anything PR Reviewer didn't. If Phase Reviewer's findings are consistently the same caliber as PR Reviewer's (just at larger scope), the role can collapse — PR Reviewer at the last PR of a phase runs an expanded rubric.

3. **Is Spec Author the right place to start, or should the human still write feature specs by hand?** Spec Author is the highest-leverage agent if it works (turns a paragraph into a complete spec) but the riskiest (a bad spec drift compounds through the whole pipeline). For the first phase, the human may want to write specs directly and skip this agent, then introduce it once the spec format is well-calibrated.

4. **What's the right tool for tracking feature state across the pipeline?** The roster assumes a tracker (ClickUp or similar) exists. The pipeline produces 6-7 task transitions per feature; without a tracker, the state lives in markdown files and chat history, which doesn't scale past a handful of features in flight.

5. **What's the rule when an agent fails?** If the Test Author writes tests that look obviously wrong, do we (a) re-run it, (b) escalate to the human, or (c) let it through and rely on Tester to catch it? The roster doesn't specify. Probably: agents should fail loudly (refuse to produce output if they can't do the job confidently), but this needs to be tested.

---

## What this roster deliberately does not include

For reference, agents considered and rejected:

- **Architecture Reviewer.** Rejected because architecture decisions live in `PROJECT_OVERVIEW.md` and are enforced via hard constraints — adding a per-feature architecture review is over-engineering.
- **Performance Reviewer.** Rejected for v1; performance issues are caught at the human gate. Add this agent only if performance becomes a recurring failure.
- **Documentation Author.** Rejected because docs should be produced as part of features, not as a separate pass — separating docs from code produces stale docs.
- **Cost Analyst.** Folded into Cost Contracts as a framework concept, with verification handled by PR Reviewer and Phase Reviewer. Doesn't need its own agent.
- **Security Reviewer.** Rejected for v1; security concerns are encoded as hard constraints in project overview. Add if security becomes a recurring concern.

If any of these come up repeatedly in practice, add them. Otherwise, resist the urge.
