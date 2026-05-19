# Spec-Driven Build Framework

A methodology for building software projects with Claude Code (or any LLM-driven implementer) without losing control of scope, quality, or architectural integrity.

> **Why this exists.** LLMs implement what you ask, but they also implement what they imagine you might want. Over a multi-week build, that drift compounds: every phase inherits the previous phase's "helpful additions." This framework forces explicit specifications and adversarial review so drift gets caught early and the build stays on the rails you laid down.

---

## Discovery vs. Execution: Know Which Mode You're In

This framework is for **execution**: you know what you're building, and you need to delegate the implementation faithfully.

It is **not** for **discovery**: you're still figuring out what to build, what problem you're solving, what the right shape is.

The distinction matters because the framework's machinery — detailed specs, adversarial review, behavioral contracts — is wasted (and worse, *misleading*) if applied to a product whose definition isn't stable yet. Writing meticulous specs for the wrong product is an expensive form of premature commitment. The specs feel productive. The artifacts pile up. And then six weeks later you discover the product itself was wrong, and the specs were specs for the wrong thing.

**Signs you're still in discovery mode** (don't use this framework yet):
- You can't write the product definition in 2-3 paragraphs without hedging.
- You haven't talked to potential users about the problem and gotten consistent reactions.
- You're not sure what the core value proposition is, or you're choosing between two different ones.
- You can't list 3-5 specific user actions the product enables.
- You're tempted to write "we'll figure out the business model later" or "we'll see what users want."

**Signs you're in execution mode** (this framework helps):
- You have a clear product definition you've defended in conversation more than once.
- You know who the user is, specifically.
- You can list the major features and prioritize them.
- The remaining unknowns are technical, not conceptual.
- You can write the hard constraints in `PROJECT_OVERVIEW.md` without making them up on the spot.

**If you're in discovery**: do that first, with lighter-weight tools. Build prototypes. Talk to users. Throw things away. Use Claude Code for rapid exploration, not faithful execution. When the product is real enough that you find yourself making the same architectural decisions twice in a row, you've moved into execution mode.

**A specific failure mode to avoid**: using this framework as a way to *feel* like you're making progress when you're actually still discovering. Spec-writing is a great procrastination for the harder work of figuring out what users want. Don't let the procedure substitute for the thought.

---

## When to Use This (Execution Mode)

**Use this when:**
- The project is large enough to require multiple phases (3+).
- You care about specific architectural decisions and don't want them silently revised.
- You're delegating implementation to Claude Code (or similar) but want to stay in the driver's seat.
- The cost of fixing wrong infrastructure later is high (e.g., agent runtimes, data models, payment systems).

**Don't use this when:**
- You're prototyping or exploring. The overhead is too high.
- The project is one weekend of work.
- You want creative input from the implementer on architecture (this framework deliberately constrains that).
- You don't yet know what you're building. Do a discovery session first.

---

## The Four Artifacts

Every project produces exactly four kinds of documents.

### 1. `PROJECT_OVERVIEW.md` (one document, reusable across all phases)

**Purpose:** Strategic context. The "why" and the immutable architectural decisions.

**Contains:**
- Product definition: what is this thing, what it is NOT.
- Architecture: the stack, the major components, the data flow at 30,000 feet.
- **Hard constraints:** decisions that are non-negotiable. These are the things the reviewer will use as auto-fail criteria. Examples from real projects: "no backend code execution," "no LLM provider abstraction," "no gamification UI," "all secrets via env vars never literals."
- Phase plan: ordered list of phases with a one-paragraph description of each.
- Open questions: things deliberately deferred.

**Length:** 5-15 pages. Big enough to ground the project; small enough to read in full at the start of every Claude Code session.

**This document is reusable.** It does not change across phases (well — see Versioning below). Both the implementer and the reviewer read it.

### 2. `PHASE_N_SPEC.md` (one per phase)

**Purpose:** The exact, unambiguous description of what Phase N must produce. Mechanically checkable.

**Structure (every phase spec has these sections):**

```
# Phase N Spec — <name>

**Phase goal:** <one paragraph>

**Prerequisites:** <previous phase complete>

**Reading order:** <which docs to read first>

**You may NOT:** <bullets of out-of-scope items that are tempting to add>

## 1. New Dependencies
<exact package names with version pins>

## 2. Settings / Configuration
<every env var, every settings change>

## 3. <Domain section: Models, Endpoints, Components, etc.>
<exact specifications — field names, types, behaviors>

## ... <as many domain sections as needed>

## N-3. Behavioral Contracts (required for any phase touching user-facing UI)
<BC-1, BC-2, ... — each contract specifies trigger, side effects, and observable result>

## N-2. Tests (required, not optional)
<unit tests + a passing contract test for every BC>

## N-1. Acceptance Criteria
<table of AC-1 through AC-X with how-to-verify column>
<must include: "AC-X: All behavioral contract tests pass">


## N. Out of Scope (do NOT implement)
<bullets of things that would be reasonable to add but aren't this phase's job>

## N+1. Done Definition
<acceptance criteria pass + reviewer pass + human gate>
```

**Acceptance criteria are the load-bearing element.** Each AC is:
- Numbered (AC-1, AC-2, ...).
- Mechanically verifiable (a grep, a test, a curl, a manual click).
- Tied to one specific spec section.

If you can't write an AC that's mechanically checkable, the spec section is too vague — rewrite it.

**Length:** 10-50 pages depending on phase complexity. Foundational phases (data model, agent infrastructure) get more pages. Polish phases get fewer.

### 3. `REVIEW_AGENT_PROMPT.md` (one document, reusable)

**Purpose:** The system prompt for the adversarial reviewer Claude Code instance.

**Contains:**
- The reviewer's role and authority.
- Default stance: **skeptical**. The reviewer assumes drift unless proven otherwise.
- How to read a rubric.
- Output format (structured JSON with verdict, issues, evidence).
- Hard-constraint enforcement: automatic fail if any hard constraint from `PROJECT_OVERVIEW.md` is violated, regardless of what else passes.
- Calibration: when to say `pass` vs `partial` vs `fail`.

**This is the secret weapon.** Without an adversarial reviewer, Claude Code grading its own work is mostly self-congratulation. With one — in a fresh context, with no knowledge of the implementation process — you get real review.

Use a *different* Claude Code session (or even a different model) for the review. Fresh context is the point.

### 4. `PHASE_N_REVIEW_RUBRIC.md` (one per phase)

**Purpose:** The phase-specific checklist the reviewer uses.

**Structure:**

```
# Phase N — Review Rubric

**Inputs to gather:** <file paths, test outputs, grep commands>

## Acceptance Criteria
<map 1:1 to the spec's ACs; how to verify each>

## Drift Watchlist
<specific things that would be tempting drift for this phase>

## Constraint Violations
<phase-specific reminders of hard constraints>

## Calibration Reminder
<phase-specific guidance for the reviewer's judgment>
<final-sweep checklist>
```

**Length:** 3-10 pages. Always shorter than the spec.

---

## The Workflow

For each phase:

### Step 1: Implementer session

Open Claude Code in a **fresh worktree** for this phase.

Initial context:
- `PROJECT_OVERVIEW.md`
- `PHASE_N_SPEC.md`
- (Optional) previous phase's deliverables if they're directly referenced

Prompt:
> Implement Phase N per the spec. Surface any ambiguity rather than guessing. Do not introduce out-of-scope work. When done, run the tests and confirm all acceptance criteria pass.

Let it work. Commit when done.

### Step 2: Reviewer session

Open Claude Code in a **separate, fresh context** — different window, no shared memory. Ideally a different model (e.g., implementer uses Sonnet, reviewer uses Opus).

Initial context:
- `REVIEW_AGENT_PROMPT.md`
- `PHASE_N_REVIEW_RUBRIC.md`
- The diff (git diff against the previous phase's merge)
- Test output, lint output, any other automated signal

Prompt:
> You are the reviewer. Apply the rubric against this diff. Output your verdict in the structured JSON format from the system prompt, and if the verdict is fail or partial, write the fix file to `specs/PHASE_N_TO_FIX.md`.

The reviewer produces **two artifacts**:

1. **JSON verdict** in the response, for the human to read:
```json
{
  "verdict": "pass" | "partial" | "fail",
  "hard_constraint_violations": [],
  "acceptance_criteria_results": [
    {"id": "AC-1", "status": "pass" | "fail" | "partial", "evidence": "..."},
    ...
  ],
  "drift_findings": [...],
  "recommended_actions": [...]
}
```

2. **Fix file** at `specs/PHASE_N_TO_FIX.md` (only on `fail` or `partial`), containing every actionable item as a checklist for the implementer to work against.

The fix file is the working surface between reviewer and implementer. Findings in the JSON exist for the human; checkboxes in the fix file exist for the implementer.

### Step 3: Decide

**If `pass`:** The fix file (if any from prior iterations) is deleted. Do the human gate (the manual checks in the spec's "Done Definition" section). If those pass, merge the worktree. Move to Phase N+1.

**If `partial`:** Read the fix file. Decide which items are real and which are reviewer over-reach (rare but possible — strike those from the fix file, with a note in `## Notes from reviewer` explaining why you overrode). Hand the fix file to the implementer Claude Code session: *"Address every checkbox in `specs/PHASE_N_TO_FIX.md`."* When done, request a re-review. The reviewer regenerates the fix file (now with `Iteration: 2`) listing only what remains.

**If `fail`:** Either start over in a fresh worktree (often faster than fixing), or treat as `partial` if the issues are localized to the fix file.

### Step 4: Commit and move on

After merge, the worktree is dead. Next phase starts fresh.

---

## The Fix-File Pattern

When the reviewer finds issues, it writes them to `specs/PHASE_N_TO_FIX.md` as a checklist. This file is the working surface between reviewer and implementer.

**Why a file and not just chat:**
- The implementer Claude Code session is often in a fresh context. Pasting "the reviewer said X, Y, Z" into chat works but loses fidelity. A file persists exactly what was found.
- Checkboxes give the implementer something to mechanically work against. "Address every box in this file" is a clearer instruction than "fix the issues."
- The file is versioned with the rest of the specs. Six months from now, you can see what went wrong on each phase and how it was resolved.
- Multiple review iterations on the same phase don't pile up — the reviewer rewrites the file each time, with only what's still unresolved.

**Fix file lifecycle:**
1. Phase N implementation completes.
2. Reviewer runs. Verdict is `partial` or `fail`. Reviewer writes `specs/PHASE_N_TO_FIX.md`.
3. Implementer reads the file, addresses each checkbox, marks them done.
4. Re-review runs. The reviewer overwrites the file with whatever issues remain. Iteration counter bumps.
5. Loop until verdict is `pass`. On `pass`, the reviewer deletes the file.

**Three categories of items in the file:**
- **Blocking:** hard-constraint violations and failed acceptance criteria. The phase cannot pass with these unresolved.
- **Drift:** scope creep, architectural deviations, anti-patterns. Should fix, but a phase could conceivably pass with documented overrides.
- **Unverifiable:** items the reviewer couldn't check due to missing test outputs, logs, or files. Implementer provides the evidence and re-requests review.

**When you (the human) override the reviewer:**
The reviewer is sometimes wrong. When that happens, strike the item from the fix file and add a note in `## Notes from reviewer` explaining why. This preserves the audit trail — both that the issue was raised and that you consciously decided not to address it.

**Anti-patterns to avoid:**
- Treating every checkbox as equally important. Blocking items first, drift items second.
- Letting the implementer self-mark items as fixed without re-review. Re-review is the verification.
- Skipping the fix file and asking the implementer to "just fix what the reviewer said" via chat. Works once; loses fidelity by the second or third iteration. The file is the source of truth.
- Carrying fix files forward to later phases. Each phase's fix file is local to that phase. When Phase N passes and you move to Phase N+1, the fix file is gone.



Hard constraints are the framework's most important mechanism. They prevent the slow erosion of architectural decisions that LLMs are particularly prone to.

**A hard constraint is:**
- A decision in `PROJECT_OVERVIEW.md` that is **never** relaxed by any phase.
- Mechanically checkable (usually via grep).
- An automatic fail in the review rubric if violated.

**Good hard constraints:**
- "No backend code execution (no `subprocess`, `exec`, `eval` on user-provided code)."
- "No LLM provider abstractions — `anthropic` SDK only."
- "No agent prompts inlined in Python code — they live in `prompts/<name>/<version>.md`."
- "No progress percentages, XP, streaks, or badges in the UI."
- "No models added outside the phase that introduces them."

**Bad hard constraints:**
- "Code should be clean and readable." (Not checkable.)
- "Performance should be good." (Not checkable.)
- "Tests should be comprehensive." (Not checkable.)

The test: can you write a grep that would catch a violation? If not, it's a guideline, not a constraint.

**In the rubric:** for each hard constraint, write the exact grep the reviewer should run. The reviewer's first action on every phase is running these greps. Any match is an automatic fail, no matter what else is good about the implementation.

---

## The Behavioral Contract Pattern

This is the framework's answer to the most common LLM-implementer failure mode: writing code that *looks correct* but doesn't actually do anything when used. The classic instance: a button with a handler attached, a composable that exists, tests that pass, and nothing happens when the user clicks it because the wire from button to API was never connected.

Structural inspection cannot catch this. The code is well-shaped; it's just empty inside. The reviewer reads the file, sees a handler attached, and infers behavior that doesn't exist.

**Behavioral contracts close this gap by specifying observable behavior, not code structure.** For every substantive interactive element on the front-end — and for every effect that should occur on page load, submission, or state change — the spec declares what *should happen*, expressed as something a test can verify.

### The shape of a contract

Every behavioral contract has three parts:

1. **Trigger.** The user action or system event that initiates the behavior. "User clicks Sign in button." "Page mounts." "WebSocket receives message."
2. **Side effects.** What should be called, dispatched, or changed as a result. "POST to `/api/auth/login/` with `{email, password}`." "Pyodide.runPython invoked with editor's current text." "Pinia store user.isAuthenticated becomes true."
3. **Observable result.** What the user actually sees after the behavior completes. "Navigation to /dashboard." "Output panel displays captured stdout." "Inline error message appears below the form."

Each contract must be **testable in isolation** with mocked dependencies. The test asserts all three parts: the trigger fires, the mocked side-effect dependencies are called with the expected arguments, and the rendered output matches the expected observable result.

### Example contracts

```markdown
### BC-1: Login form submission (success path)
- **Trigger:** User fills email + password fields with valid input, clicks "Sign in" button.
- **Side effects:** A POST request to `/api/auth/login/` with body `{email: <typed email>, password: <typed password>}`.
- **Observable result:** On 200 response, navigation to `/dashboard`. The auth store's `isAuthenticated` becomes `true`.

### BC-2: Login form submission (failure path)
- **Trigger:** User fills email + password, clicks "Sign in" button.
- **Side effects:** POST to `/api/auth/login/`.
- **Observable result:** On 401 response, an inline error message "Invalid email or password" appears below the form. No navigation occurs. The auth store remains unauthenticated.

### BC-3: Run button (Python cell)
- **Trigger:** User clicks Run inside a `<RunnableCell language="python">`.
- **Side effects:** `usePyodide().runPython()` is called with the editor's current text. Loading state appears while in flight.
- **Observable result:** Output panel below the editor displays captured stdout. If the run errored, the output panel shows the exception in red with a traceback.
```

Three contracts, three tests, three pieces of behavior that cannot silently fail to be wired up.

### Why this works

A test for BC-1 mocks `fetch` and asserts it was called with the right URL and method. **An empty button handler cannot pass this test.** It doesn't matter how plausible the code looks; if the click handler is empty, the mock is never called, the assertion fails, and the contract test fails. The implementer must actually wire the button to the API call to make the test pass.

Similarly, a test for BC-3 mocks `usePyodide` and asserts `runPython` was called. An implementation that renders a Run button without attaching a working handler fails the test.

The contracts function as **behavioral specifications that survive contact with the implementer's plausibility bias.** LLM implementers can generate code that looks like it does the thing without actually doing the thing. The contract test demands proof of the doing.

### What counts as "substantive"

Not every interactive element needs a contract. The judgment: would a user be surprised if this element did nothing? If yes, write a contract. Examples:

**Needs a contract:**
- Any button that triggers a network request.
- Any form submission.
- Any element that fetches data on mount (page-level data loads).
- Any toggle or control that changes persistent state.
- Any element that triggers navigation to a non-trivial destination.
- Any element that streams data (chat input, real-time updates).
- Any payment, authentication, or destructive action.

**Doesn't need a contract:**
- Static links to the same app (router.push to a known route).
- "Back" buttons that call `router.back()`.
- Pure-presentation toggles (theme switcher, expand/collapse) — unless the state is persisted.
- Decorative animations.

The skill is identifying which elements carry user expectations of consequence. Over-specifying is wasteful but not harmful. Under-specifying is how you ship buttons that do nothing.

### Where contracts live in the spec

In the `PHASE_N_SPEC.md` structure, contracts get their own numbered section, **before** the Tests section and **before** Acceptance Criteria. The Tests section then references the contracts ("a passing contract test must exist for each BC"). The Acceptance Criteria includes a mechanical AC that all contract tests pass.

Like acceptance criteria, contracts are numbered (BC-1, BC-2, ...). They're written by the spec author (you), not invented by the implementer. The implementer's job is to make the existing contracts pass — they don't get to decide what counts as a contract.

### Where contracts live in the rubric

The review rubric inherits contracts automatically. The reviewer's job is now:

1. Verify a contract test file exists for each BC.
2. Verify the test actually exercises the contract (read the test, confirm it triggers the action, asserts on the mock, asserts on the observable result).
3. Verify the test passes.

A reviewer that finds a "passing" contract test which doesn't actually verify behavior (e.g., a test that imports the component and asserts `expect(true).toBe(true)`) treats it as a failed contract. This is non-negotiable.

### How contract tests fit alongside other tests

Different test types catch different failure modes. A complete project uses several:

- **Unit tests:** verify pure logic in isolation. Cheap. Plentiful.
- **Contract tests:** verify the behavioral contracts defined in the spec. One per BC. Per-component scope. Mocks external dependencies.
- **Integration tests:** verify full flows spanning multiple layers (frontend → backend → external service). Few. Slow. Catch wiring failures that span systems.
- **Human gate testing:** an actual person uses the product. Catches the polish, feel, and emergent-property failures that automated tests miss.

Contract tests are the layer most likely to catch the "novice-level misses" — buttons that do nothing, forms that don't submit, fetches that never fire. They're cheap enough to write abundantly and specific enough to fail loudly when behavior is missing.

### What this is, in formal terms

Behavioral contracts are a flavor of **acceptance test-driven development**: declare observable behavior before writing the code; write tests against that behavior; the tests fail until the code actually does what was specified.

This is not a new idea in software engineering. It's an old idea that becomes load-bearing when the implementer is an LLM, because LLMs fail in a specific way that ATDD specifically addresses: generating plausible structure without verified behavior.

### A note on streaming and other awkward cases

Some behaviors don't fit neatly into "trigger → side effect → observable result." Streaming responses, complex async flows, drag-and-drop, file uploads, real-time collaboration — these need contracts too, but the test strategy varies.

For streaming: the contract is "after the user sends a message, text appears incrementally over time." The test mocks the SSE source, pushes events, and asserts the rendered output updates accordingly. Same shape, just async.

For Pyodide / heavy WASM: the contract mocks the runtime and asserts it was called correctly. Actual Pyodide execution is verified separately in a slower integration test or in the human gate.

For interactive flows with multiple steps: write multiple contracts, one per step. Don't try to put a whole flow into one contract.

The goal is never to test everything in one test. The goal is that **every observable behavior the user expects** is covered by at least one test that would fail if the behavior were missing.

---

## The Cost Contract Pattern

Behavioral contracts verify that a thing works. Cost contracts verify that a thing works *at a price you can afford*.

This pattern is necessary when the product depends on per-call external services with variable cost: LLM APIs, payment processors with per-transaction fees, third-party data providers with metered pricing, image generation APIs, transcription services. The unique failure mode here is silent: the product works perfectly, the tests pass, the reviewer passes — and each user costs you $20/day. By the time you notice, you've burned your runway.

This is the failure mode that kills LLM-heavy products specifically. Token costs compound across users, sessions, retries, and background jobs. A single carelessly designed agent flow can 10× your costs without anyone noticing until the monthly invoice arrives.

### The shape of a cost contract

Every cost contract has three parts:

1. **Scope.** The unit being budgeted. "A single lesson generation." "A single chat message." "A single user-day at typical usage." "A single page load."
2. **Budget.** The cost ceiling for the scope, in USD or other unit (tokens, requests). Expressed as a hard number, not a vague target. "$0.20 per lesson generation." "$0.05 per chat exchange." "≤ $2/user/day at p95 usage."
3. **Verification.** How you'll measure actual cost against the budget. A dashboard query, a database aggregation, a synthetic load test. The measurement must be reproducible.

### Example cost contracts

```markdown
### CC-1: Lesson generation cost
- **Scope:** One full lesson generation pipeline run (generator + critic, no revision loop).
- **Budget:** ≤ $0.20 per run. Hard ceiling $0.40 (includes one revision loop).
- **Verification:** `SELECT AVG(cost_usd) FROM generation_jobs WHERE agent_name='lesson_generator' AND created_at > now() - interval '7 days'` after Phase 5 ships; must be ≤ $0.20.

### CC-2: Oracle chat cost per exchange
- **Scope:** One user message + one Oracle response, including context loading.
- **Budget:** ≤ $0.03 per exchange (average); ≤ $0.10 (p95).
- **Verification:** Compute from `ChatMessage` rows: AVG and p95 of `tokens_in * input_price + tokens_out * output_price` per (user_message, oracle_response) pair over 7 days.

### CC-3: Per-user monthly cost ceiling
- **Scope:** All LLM costs incurred by a single subscriber in a calendar month, across all features.
- **Budget:** ≤ $4/user/month at expected usage. Hard ceiling $8/user/month.
- **Verification:** Monthly aggregation query joining all `GenerationJob` and `ChatMessage` rows by profile_id. If any user exceeds the hard ceiling, trigger alert.
```

### Why this works

Cost is normally invisible. You don't see it during development because you're one user. You don't see it in tests because tests mock the API. You don't see it in code review because the diff doesn't have a price tag. By the time costs are visible (the monthly invoice), the architectural decisions that caused them are baked in.

Cost contracts make cost visible **at spec time**, when it's cheap to redesign. Writing CC-1 forces you to ask: "Can we hit a real Anthropic call from a real prompt and stay under $0.20?" If the answer is no, the architecture changes — maybe you use a cheaper model for the generator, maybe you cap output tokens, maybe you cache more aggressively. These decisions belong in the spec, not in a panic email three months in.

### Where cost contracts live

Cost contracts go in `PROJECT_OVERVIEW.md` (the project-wide budgets like per-user/month) and in phase specs (the per-feature budgets relevant to that phase). The phase spec references the project-level CCs to ensure consistency.

The reviewer is required to verify cost contracts at two points:
1. **At phase review:** does the implementation appear capable of meeting the budget? (e.g., does the agent call have `max_tokens` set within a budget-consistent range?)
2. **At Phase 9 (or pre-launch):** has actual measured cost been verified against the contract? This is a human-gate item — you run the verification query and confirm.

A phase cannot pass Phase 9 review if any cost contract's verification has not been run against real data.

### What's not a cost contract

Don't write cost contracts for things that don't have per-unit external costs: hosting, bandwidth (usually negligible per-user at SaaS scale), database queries, compute. Those go in a separate "operational budget" if at all. The cost contract pattern is specifically for *per-user-action* costs that scale linearly with usage and can compound silently.

Also: don't write cost contracts you can't measure. A budget without a verification mechanism is just wishful thinking.

---

## Cross-Phase Integration Verification

Every phase ships with its own tests passing. The framework, as originally written, gives no assurance that phase N's tests still pass after phase N+1 lands. In practice, this is a regular source of regressions — phase 5 adds a field that breaks phase 3's serializer, phase 6 changes an enum and phase 5's tests start failing, etc. The phase 5 reviewer doesn't know to check phase 3. The phase 6 reviewer doesn't know to check phase 5.

This is a structural hole. Each phase is reviewed in isolation, and the *seams between phases* never get tested.

### The fix: a regression contract

After each phase, before the human gate, run the **full accumulated test suite from all prior phases**. Not just the current phase's tests. All of them.

In practice:
- All unit tests from all phases.
- All behavioral contract tests from all phases.
- All integration tests from all phases.
- All cost contract verifications from all phases (using historical data — does the current state still satisfy CC-1 from Phase 5?).

The reviewer treats prior-phase test failures as **hard fails for the current phase**, not "those tests are old, ignore them." The current phase broke them. The current phase has to fix them.

### The structural addition

Add to each `PHASE_N_SPEC.md` Acceptance Criteria section:

> AC-X (mandatory for all phases after Phase 1): The full accumulated test suite from Phases 1 through N passes. Verification: run the full test suite, exit code 0.

The reviewer checks this. If any prior-phase test fails, the verdict is `fail` regardless of how good the current phase's new work is.

### Cross-phase integration tests

Beyond just running old tests, certain integration points deserve **explicit integration tests at the seam**. Specifically:

- Where phase N produces data that phase N+K consumes, write a test in phase N+K that constructs the input the way phase N would have, then runs the consumer end-to-end against it.
- Where phase N exposes an API that phase N+K's frontend calls, write a test that hits the real backend route from the frontend side, not just from a unit test.
- Where phase N defines a contract (output schema, event shape, message format), phase N+K's tests assert against the same contract — ideally by importing the schema, not redefining it.

These integration tests live in the phase that *consumes* the integration, not the phase that produces it. This way, breaking changes show up as failures in the consumer's tests, which is where you actually want them.

### What this catches

The regression contract catches:
- Migrations that break older data.
- Schema changes that break older API contracts.
- Setting changes that disable features the consumer relied on.
- Hard-coded values from earlier phases that now conflict with new logic.
- Test isolation failures (tests that passed because of stale fixtures or test ordering).

These are the failures that produce the experience of "I shipped Phase 6 and now the dashboard from Phase 3 is broken." They're entirely preventable by running prior tests, but only if the framework requires it.

### The cost

Running the full accumulated test suite gets slower over time. Phase 8 might run for several minutes. This is an acceptable tax — the alternative is silent regressions that take hours to diagnose.

If the test suite gets unreasonably slow (>15 minutes), that's a signal to invest in test infrastructure (parallelization, selective test running based on diff analysis), not to skip the regression pass.

---

## Calibrating Spec Density

Not every phase deserves the same level of detail. Calibrating density per phase is the highest-leverage author skill.

**Phases that deserve high density (one layer above pseudocode):**
- Data model phases. Field-by-field exactness prevents downstream chaos.
- Authentication and payments. Bugs here are catastrophic.
- The "hinge phase" — the one most-other-phases depend on (often the second or third phase). Pay the spec cost once, save on every downstream phase.
- Infrastructure with subtle correctness requirements (caching, idempotency, retries).

**Phases that deserve medium density:**
- Business logic phases that orchestrate already-specified infrastructure.
- API endpoints with well-defined contracts.

**Phases that deserve looser specs:**
- UI polish.
- The final "make it launchable" phase.
- Phases where the desired behavior is "reasonable and consistent with what's been built."

A heuristic: **spec density is inversely proportional to forgiveness of mistakes.** Data model wrong on day 1 = rewrite half the codebase later. Button colors wrong on day 30 = fix in 10 minutes.

---

## Phase Splitting

How do you decide what's one phase versus two?

**One phase should:**
- Be implementable in one Claude Code session without context exhaustion. (Empirically: ~1000-2000 lines of net new code is the upper bound.)
- Have a clean "done" state that's demonstrable to a human in under 5 minutes.
- Not require speculative work for phases that haven't been spec'd yet.

**Split a phase when:**
- The diff would be too big to review effectively.
- Some parts can be deployed independently and the others can come later.
- The infrastructure inside the phase is itself a deliverable other phases depend on.

**Don't split when:**
- Two pieces are so tightly coupled that splitting forces speculative interfaces.
- The split would create two phases neither of which is useful alone.

**A typical project shape:**
1. **Skeleton.** The most basic possible "hello world" with the full stack wired up.
2. **Auth + payments.** SaaS plumbing, no domain logic.
3. **Data model + admin.** All the shapes that hold the domain.
4. **Infrastructure for the hard part.** (Agent runtime, search engine, recommendation engine, whatever the core technical magic is.)
5. **First feature using the infrastructure.** End-to-end through the magic.
6. **Second feature.**
7. **Third feature.**
8. **Polish + launch.**

8 phases is a typical large project. 3-5 phases is typical for medium. 1-2 phases means you don't need this framework.

---

## The Out-of-Scope List

Every spec section has an "Out of Scope" subsection. This is critical.

Without it, the implementer fills the gap with reasonable assumptions. Those assumptions become tomorrow's drift.

**What to include:**
- Things that would be reasonable additions but aren't this phase's job.
- Things you specifically considered and decided against (for now).
- Things that look like they'd belong here but are coming in a later phase (cite the phase).

**Examples of good out-of-scope items:**
- "Email verification flow (deferred to launch-prep phase)."
- "Real-time updates via WebSockets (HTTP polling sufficient for v1)."
- "Free trial implementation (Stripe handles via price config; no in-app trial logic)."
- "Streaming responses (Phase 7 will add streaming for the chat feature; this phase is non-streaming)."

The out-of-scope list often grows during the build, as the implementer flags ambiguities. Add to it then.

---

## The Reviewer's Role and Calibration

The reviewer exists because Claude Code grading its own work is unreliable. The reviewer must:

- Default to skeptical.
- Treat hard constraints as absolute. No "well, it's only one `eval()` call, and it's in a test file" — fail.
- Treat the rubric as the floor, not the ceiling. The reviewer can flag drift not explicitly in the rubric.
- Output structured findings, not free-form essays.

**Calibration: when to say what.**

- `pass`: every AC passes, no hard constraint violated, no concerning drift.
- `partial`: most ACs pass, but specific fixable issues remain. The reviewer lists exactly what.
- `fail`: hard constraints violated OR pervasive drift that's easier to redo than fix.

The reviewer should not give `pass` out of generosity. A `pass` means "I'd ship this." A `partial` is the default for "good direction but needs work."

**The reviewer should have a different model OR a fresh context.** If the same context produces both implementation and review, the review will rationalize the implementation. Fresh eyes are the point.

---

## Versioning and Mid-Build Changes

Things change mid-build. Handle them this way:

**If `PROJECT_OVERVIEW.md` needs to change:**
- This is rare and serious. A change to a hard constraint or the architecture means previous phases may need revisiting.
- Make the change explicitly. Note the date and reason.
- Decide: does this require redoing any previous phase, or only affects future phases?

**If a `PHASE_N_SPEC.md` needs to change after Phase N is complete:**
- Don't edit it. Instead, write a `PHASE_N_AMENDMENT.md` documenting what changed.
- Or: introduce a corrective task in a later phase.
- Editing the original spec means future readers (including you in 3 months) lose the history of what was actually built.

**If a `PHASE_N_SPEC.md` is wrong and Phase N hasn't started:**
- Edit it directly. No versioning needed; nothing has been built against it.

---

## What This Framework Does NOT Solve

Be honest about the limits:

- **Bad architecture.** If your `PROJECT_OVERVIEW.md` has bad architecture, this framework will reliably build the wrong thing.
- **Bad product decisions.** This framework is about execution fidelity, not product strategy.
- **Vague goals.** If you don't know what you want, no amount of specification will help. Do discovery first.
- **Prompt quality (for AI projects).** The framework ensures the agent runtime is built right; it doesn't ensure the prompts inside it are good. Prompt iteration is a different practice.
- **Real-world testing.** Reviewer passes are necessary but not sufficient. The human gate at the end of each phase is where reality intrudes.

---

## A Minimal Skeleton

To start a new project with this framework, create this structure:

```
project-root/
├── specs/
│   ├── PROJECT_OVERVIEW.md
│   ├── REVIEW_AGENT_PROMPT.md
│   ├── PHASE_1_SPEC.md
│   ├── PHASE_1_REVIEW_RUBRIC.md
│   ├── PHASE_2_SPEC.md
│   ├── PHASE_2_REVIEW_RUBRIC.md
│   └── ...
└── src/  (created during Phase 1)
```

During active work on a phase, the reviewer may add `PHASE_N_TO_FIX.md` to `specs/`. That file's lifecycle is local to the phase — it's overwritten on re-review and deleted when the phase finally passes.

The `specs/` directory lives in the same repo as the code, so phases and their specs are versioned together.

---

## Templates

Starter templates for each artifact follow. Copy and fill in.

### Template: `PROJECT_OVERVIEW.md`

```markdown
# <Project Name> — Overview

## Product Definition

<2-3 paragraphs: what is this, who is it for, what differentiates it. Be specific about what it is NOT — the negative space matters as much as the positive.>

## Architecture

**Stack:**
- <Backend>
- <Frontend>
- <Data layer>
- <External services>

**Major components:**
- <Component 1: one paragraph>
- <Component 2: one paragraph>

**Data flow:**
<Describe in prose how a typical user action moves through the system.>

## Hard Constraints

These are non-negotiable. The reviewer enforces these as automatic fails.

1. **<Constraint name>:** <description>. **Grep:** `<exact grep command that would catch a violation>`.
2. ...

## Phase Plan

1. **Phase 1 — <name>:** <one paragraph>
2. **Phase 2 — <name>:** <one paragraph>
3. ...

## Open Questions

Things deliberately deferred for now:
- <question 1>
- <question 2>

## Glossary

<Project-specific terms with definitions.>
```

### Template: `PHASE_N_SPEC.md`

```markdown
# Phase N Spec — <name>

**Phase goal:** <one paragraph describing the demonstrable outcome>

**Prerequisites:** Phase N-1 complete and reviewed pass.

**Reading order:** `PROJECT_OVERVIEW.md` → <other relevant docs> → this spec.

**You may NOT:**
- <out-of-scope item that's tempting>
- <out-of-scope item that's tempting>
- <out-of-scope item that's tempting>

---

## 1. New Dependencies

### Backend
- `<package>==<exact_version>`

### Frontend
- `<package>`: `^<version>`

No other dependencies.

---

## 2. Configuration / Settings

<Every env var, every settings change, exactly.>

---

## 3. <First domain section: Models / Endpoints / Components / etc.>

<Exact specifications.>

---

## 4. <Next domain section>

...

---

## N-1. Behavioral Contracts

For any phase that touches user-facing UI, this section is required. Each contract has three parts and must be testable in isolation with mocked dependencies.

### BC-1: <name of the behavior>
- **Trigger:** <user action or system event>
- **Side effects:** <what gets called, dispatched, or changed>
- **Observable result:** <what the user sees after>

### BC-2: ...

(Phases that produce no user-facing UI — pure backend, pure data model — may omit this section. State so explicitly: "No behavioral contracts; this phase has no user-facing surfaces.")

---

## N. Tests (required)

<Unit tests covering pure logic.>

<A contract test for every BC above. Contract tests live under `frontend/tests/contracts/` (or equivalent). Each test mocks side-effect dependencies, triggers the action, and asserts on both the mocked calls and the rendered output.>

---

## N+1. Acceptance Criteria

| # | Criterion | How to verify |
|---|-----------|---------------|
| AC-1 | <criterion> | <verification method> |
| AC-2 | ... | ... |
| AC-X | All behavioral contracts have passing tests | `pnpm test:contracts` (or equivalent) exits 0; test count ≥ number of BCs in §N-1 |

---

## N+2. Out of Scope

- <item> (deferred to Phase X)
- <item> (deliberately not implementing)

---

## N+3. Done Definition

1. All acceptance criteria pass.
2. Reviewer agent returns `verdict: pass` against `PHASE_N_REVIEW_RUBRIC.md`.
3. Human gate: <specific manual verification that proves the phase is real>.
```

### Template: `REVIEW_AGENT_PROMPT.md`

```markdown
# Review Agent — System Prompt

You are the adversarial reviewer for the <project_name> build. Your job is to verify that the most recent phase's implementation matches its specification exactly, with no drift, no scope creep, and no hard-constraint violations.

## Your Authority

You are not the implementer. You did not write this code. Your job is to find what's wrong with it, not to be helpful or generous. A `pass` from you means "I'd ship this." If you're uncertain, the verdict is `partial`.

## Inputs You Will Receive

- `PROJECT_OVERVIEW.md` (the immutable architectural context)
- `PHASE_N_SPEC.md` (the spec the implementer was given)
- `PHASE_N_REVIEW_RUBRIC.md` (your phase-specific checklist)
- The diff between the previous phase's merge and the current state
- Test outputs, lint outputs, any automated signals

## Your Process

1. Read `PROJECT_OVERVIEW.md` end to end. Note every hard constraint.
2. Run the hard-constraint greps from `PROJECT_OVERVIEW.md`. **Any match is an automatic fail.** Stop here, return `fail` with the matched evidence, write the fix file.
3. Read `PHASE_N_SPEC.md` end to end. Note every behavioral contract (BC-1, BC-2, ...).
4. For each BC, verify that a contract test exists, that the test actually exercises the contract (triggers the action, asserts on mocked side-effects, asserts on observable result), and that the test passes. **A "passing" test that asserts trivial truths is treated as a failed contract.** A BC without a test, or with a test that doesn't actually verify the behavior, is a hard fail of that contract.
5. Read `PHASE_N_REVIEW_RUBRIC.md` and follow it.
6. For each AC in the rubric, verify against the diff. Note status: pass / fail / partial.
7. Scan for drift not explicitly listed in the rubric but that violates the spec's spirit.
8. Output your verdict in the JSON format below AND write the fix file if verdict is fail or partial.

When verifying behavioral contracts, do not infer behavior from structure. A handler attached to a button does not mean the handler does anything; you must read the handler's implementation and the corresponding contract test together. If the contract test mocks `fetch` but the test doesn't assert `fetch` was called with specific arguments, the test is hollow — flag it.

## Two Outputs

You produce two outputs:

**1. JSON verdict** in your response, for the human reviewing the build:
```json
{
  "verdict": "pass" | "partial" | "fail",
  "hard_constraint_violations": [
    {"constraint": "...", "evidence": "..."}
  ],
  "behavioral_contract_results": [
    {"id": "BC-1", "status": "pass" | "fail" | "hollow_test" | "no_test", "evidence": "..."}
  ],
  "acceptance_criteria_results": [
    {"id": "AC-1", "status": "pass" | "fail" | "partial", "evidence": "..."}
  ],
  "drift_findings": [
    {"description": "...", "severity": "minor" | "major", "evidence": "..."}
  ],
  "overall_assessment": "2-3 sentences"
}
```

**2. Fix file** at `specs/PHASE_N_TO_FIX.md`, for the implementer to work against. Write this directly via your file-edit tools.

- If verdict is `pass`: do not write a fix file; delete any existing one (the phase is clean).
- If verdict is `partial` or `fail`: write the fix file using the structure below. Every finding in the JSON appears here as a checkbox.

### Fix file structure

```markdown
# Phase N — Fixes Required

**Reviewer verdict:** <fail | partial>
**Generated:** <ISO date>
**Iteration:** <1 for first review, 2+ for re-reviews>

> Read this file before resuming work on Phase N. Address every checkbox. When all boxes are checked and you believe the phase is complete, request a re-review. If you disagree with a finding, surface that to the human rather than ignoring it.

## Blocking (must fix before re-review)

- [ ] **<short title>** — <file:line if applicable>
  - **What's wrong:** <description>
  - **Why it matters:** <which AC or hard constraint>
  - **What to do:** <specific actionable instruction>

## Drift (should fix; re-review may pass without these)

- [ ] **<short title>** — <file:line>
  - **What's wrong:** <description>
  - **What to do:** <instruction>

## Unverifiable (need more info)

- [ ] **<short title>**
  - **What's missing:** <description>
  - **What to provide:** <specific evidence>

## Notes from reviewer

<Optional context that doesn't fit a checkbox.>
```

Rules for the fix file:
- Every item is `- [ ]` so the implementer can check them off as they go.
- Sort each section by severity (most blocking first).
- Items must be actionable; cite paths and line numbers.
- The file replaces any previous fix file at the same path.
- Do not invent items the spec did not require; drift findings are deviations from spec, not your preferred architecture.

## Calibration

- `pass`: every AC passes, no hard constraint violated, no concerning drift. Ready to merge. No fix file.
- `partial`: specific fixable issues. Fix file listed precisely.
- `fail`: hard constraint violated OR pervasive drift. Fix file written; recommend redo if pervasive.

Do not give a `pass` out of generosity. The owner wants to know what's wrong. Be specific. Cite line numbers and file paths in evidence.
```

### Template: `PHASE_N_REVIEW_RUBRIC.md`

```markdown
# Phase N — Review Rubric

Per `REVIEW_AGENT_PROMPT.md`.

**Inputs to gather:**
- <file paths>
- <command outputs>
- <grep results>

---

## Acceptance Criteria

### AC-1: <criterion name>
<How to verify in detail.>
<Drift signals specific to this AC.>

### AC-2: ...

...

---

## Drift Watchlist (Phase N specific)

- **<Drift pattern>:** <why it's drift and how to spot it.>
- ...

---

## Constraint Violations (Phase N specific)

<Restate the relevant hard constraints with the exact greps to run.>

---

## Calibration Reminder

<Phase-specific guidance — what's the biggest risk in this phase? What's the highest-leverage final check?>

After your verdict:
1. <Final sweep item>
2. <Final sweep item>
3. <Final sweep item>
```

---

## Closing Notes

This framework trades upfront writing time for downstream debugging time. For small projects, that trade is bad. For large projects with non-trivial architecture, it's the only way to delegate implementation while preserving the architecture you actually want.

There are five highest-leverage elements, in rough priority order:

1. **Know whether you're in discovery or execution mode.** If discovery, set this framework down and come back later. Spec discipline on an unstable product is wasted effort and worse, it locks in premature decisions.
2. **Behavioral contracts with required tests.** This catches the novice-level misses (buttons that do nothing, forms that don't submit, fetches that never fire) that structural inspection cannot catch.
3. **Cost contracts** if you're building anything with per-call external API costs. This is what keeps the product from being expensive in ways you don't notice until invoices arrive.
4. **Hard constraints with grep enforcement.** This catches the architectural drift that compounds across phases.
5. **The adversarial reviewer in a fresh context.** Without this, the build is on rails of its own making.

If you do nothing else from this framework, do those five, in that order.

Two things that are not optional but easy to skip:

- **The human gate at the end of every phase.** Spend 15 minutes actually using the product, like a user would. Click the buttons. Submit the forms. Watch the network tab. The reviewer cannot replace this. No process can. If nobody on the team is ever actually a user of the product mid-build, the product will not work — and you will not know it doesn't work until you ship.
- **The regression pass.** Run the full accumulated test suite after every phase. Old tests breaking is *information* — almost always news the current phase broke something. Treat it as a hard fail and fix forward.

Everything else is supporting structure.
