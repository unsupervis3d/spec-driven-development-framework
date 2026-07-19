# Human Gates

The single most important idea in this framework. If you take nothing else from it, take this.

A human gate is a point in the pipeline where work **stops** and a human renders judgment before
anything proceeds. Not a notification. Not a status update you skim. A decision you are accountable
for, made with the relevant artifact in front of you.

Everything else in the framework — the seven agent roles, the specs, the behavioral contracts, the
Facilitator — exists to make the gates cheap to staff and hard to fake. The agents do the labor.
The gates are where you stay in command of the product.

---

## Why gates exist

LLM coding agents are extraordinarily good at producing plausible work. That is precisely the
danger. Plausible is not the same as correct, and it is not the same as *what you actually asked
for*. An agent will:

- Implement what you asked **and** what it imagines you might have wanted.
- "Helpfully" add a feature, an abstraction, a config option you never requested.
- Quietly revise an architectural decision because a different one was easier to code.
- Produce tests that pass without verifying the behavior that matters.
- Summarize its own work in a way that sounds clean regardless of whether it is.

None of these are loud failures. They don't throw errors. They look like progress. Over a
multi-week build, they **compound**: every phase inherits the previous phase's unrequested
additions, and the product you end up with is subtly — then badly — not the one you specified.

A human gate is the only mechanism that reliably catches this class of failure, because the failure
is about *intent*, and intent lives in your head, not in the code. No amount of automated review
substitutes for a human who knows what the product is supposed to be looking at what was actually
built and saying "yes, that" or "no, not that."

**The agent that produced the work cannot be the thing that approves it.** Confidence about your own
output is not evidence. This is true for LLMs and it is true for you. That is why review roles run
in fresh context, and why — at the gates that matter most — a *human* makes the call.

---

## The cardinal rule

> A gate you would approve without looking is not a gate. It is a rubber stamp with extra steps.

If you find yourself clicking "approve" because the work is probably fine, stop. Either the gate is
genuinely substantive and deserves your attention, or it is theater and should be removed from your
process honestly — not skipped silently while you tell yourself you're following the framework.

The framework is supposed to feel *slightly* heavy at the gates. That friction is the product
working. The discomfort of being asked to actually evaluate something is the cost of staying in
control. It is much cheaper than the discomfort, six weeks later, of discovering the product went
sideways at a gate you waved through.

---

## The three gates (full framework)

The full framework defines exactly three human gates. Two per feature, one per phase. They are
deliberately few — gate fatigue is real, and a gate you're too tired to staff is worse than no gate
because it launders bad work with the appearance of review. See `AGENT_ROSTER.md` for where each
gate sits in the pipeline.

### Gate 1 — Plan approval + usefulness check (~5–7 min, per feature)

**When:** After the PM produces the task plan and before the SWE writes any implementation code.

**What you do:** Read the task plan. Then — this is the part people skip — *close it* and write
three concrete sentences describing what a user actually does with this feature once it ships.

**What you're catching:**
- **Scope errors, before they cost anything.** This is the cheapest possible place to catch "that's
  not what I meant." No code exists yet. Redirecting here costs a re-plan, not a rewrite.
- **Features that shouldn't be built at all.** If those three sentences come easily and feel
  substantive, the feature is well-motivated — proceed. If they feel forced, generic, or you can't
  write them without hand-waving, the *feature itself* needs reconsideration. The usefulness check
  is a deliberate firebreak against building things that pass every test and still don't matter.

**The failure mode if you skip it:** You discover at Gate 2 (or worse, in production) that a
correctly-implemented, fully-tested feature solves a problem no user has. You paid for the whole
pipeline to build the wrong thing well.

### Gate 2 — PR merge (~5–15 min, per feature)

**When:** After the Tester and the (fresh-context) PR Reviewer have done their passes, before the
PR merges into the base branch.

**What you do:** Read the PR. Read the reviewer's verdict. Confirm the hard-constraint greps came
back empty. Then actually follow the PR's testing steps against a running instance — not just read
them. Make the merge call yourself — the reviewer's verdict is advisory, not binding.

**What you're catching:**
- **Hard-constraint violations.** The non-negotiable, grep-enforceable rules from
  `PROJECT_OVERVIEW.md`. This is the most mechanical check and the most important — it is the line
  between "the framework caught it" and "we shipped it."
- **Diff hygiene.** Dead code, debug logging left in, an unrequested dependency, a file committed by
  accident, an abstraction nobody asked for.
- **Drift that survived automated review.** The reviewer reads the diff cold against the spec; you
  read it knowing the whole product. You see things a fresh-context reviewer structurally cannot.
- **Half-built work merged as if it were done.** A button wired to an endpoint that doesn't exist, a
  flag nothing turns on, a form writing to a table that isn't there yet. This is what the PR's
  required testing steps are for — if you can't follow them to a real result, the PR isn't the
  complete slice it claims to be, no matter how green the tests are.

**The failure mode if you skip it:** "Just merge it, it's fine." The single most common way drift
becomes load-bearing. Each individually-fine merge accumulates; the constraint violation or the
helpful little addition that nobody approved is now something the next feature builds on top of.

### Gate 3 — "Be a user" (~15 min, per phase)

**When:** After the Phase Reviewer verifies the cumulative work of the whole phase, before you
declare the phase done and move on.

**What you do:** Actually use the product the way a real user would. Not read about it. Not run the
tests. *Use it.* Click the buttons, upload the file, have the conversation, hit the error paths on
purpose.

**What you're catching:**
- **Integration breakage at the seams.** Individual features can each pass while the phase as a
  whole is broken — the joints between features are exactly what per-feature review can't see.
- **The gap between "tests pass" and "this is good."** Tests verify the contracts you thought to
  write. Being a user surfaces the things you didn't think to specify — the awkward flow, the
  confusing state, the thing that's technically correct and actually wrong.
- **Whether the phase was worth it.** A periodic, embodied re-grounding in the actual product
  before you commit to the next phase of building on top of it.

**The failure mode if you skip it:** You move to the next phase on top of a foundation that demos
green but doesn't actually work end to end. The bug you didn't catch by being a user is now buried
under a phase of new work.

---

## Gates and the Facilitator

The Facilitator (the v0.2.0 orchestrator, see `FACILITATOR.md`) removes the *bookkeeping* around
gates — it tracks which gate is open, prepares the inputs, and quotes the responsible subagent's
structured output **verbatim** so you evaluate the agent's actual words rather than the
Facilitator's paraphrase of them. That verbatim-quoting rule exists specifically to defend the
gates: an orchestrator that summarized a Tester report down to "tests look fine" would be quietly
dismantling Gate 2.

What the Facilitator does **not** do is remove the judgment. It cannot approve a gate for you. It
will not advance past a gate without your explicit confirmation. If it presents a gate and you
notice you'd review it lightly, that is the signal to slow down, not speed up. The Facilitator makes
the gates cheaper to staff. It does not make them optional. **The Facilitator removes bookkeeping,
not judgment.**

---

## Gates in the lightweight pattern

The lightweight adaptations (see `lightweight/`) collapse the roster down for ticket-scale work in
an existing codebase where humans already play most of the roles. They keep exactly **one** gate:
the human review before the PR is created. Everything else can be dropped in that context — but not
that. The one role no human on a typical team plays before merge is the clean-context adversarial
reviewer, and the one decision no automation should make for you is "this is ready to go out." The
lightweight pattern is the proof that gates, not roles, are the irreducible core of this framework.

---

## If a gate feels like pure overhead

Sometimes it will. When that happens, do not bypass it silently. Instead:

1. **Note it in `RETRO.md`** — what you were trying to do, what the gate required, what the catch
   rate has actually been.
2. **Staff the gate this time anyway.** Even if it feels heavy. One more data point.
3. **At the phase retro, decide honestly.** A gate with a consistently low catch rate over real use
   is a framework bug — fix it, move it, or remove it deliberately. A gate that merely *feels*
   annoying while still catching real problems is working as designed. Be ruthless about telling the
   two apart, and be suspicious of the part of you that wants the answer to be "remove it."

The goal is never "follow the framework." The goal is to ship a product you're proud of. Gates serve
that goal. When a gate stops serving it, change the gate — out loud, in the retro, on purpose.
