# PROJECT_OVERVIEW: <Project Name>

> Copy this file into the root of your project repo, rename to `PROJECT_OVERVIEW.md`, fill in
> every section, and delete this blockquote and the `<...>` / guidance notes as you go.
>
> **This is the highest-leverage artifact in the whole framework.** Everything downstream — specs,
> tickets, tests, code, reviews — is checked against this document. A vague overview produces vague
> specs and drifting code. Spend real time here. It typically takes one or more focused sessions,
> not a few minutes. Do not skip ahead to coding to "come back and fill this in later."
>
> A worked example of a completed overview is intentionally not shipped in this repo (the original
> pilot's overview described a real product). Use the section guidance below to write your own.

> **Framework:** spec-driven-build v<X.Y.Z>
> **Status:** <one line — e.g. "Phase 1 in progress" or "pre-Phase-1, overview under review">

---

## What this is

> One or two paragraphs. What does the product do, for whom, and what is its single core job?
> If you can't write this without hedging, you may still be in *discovery* mode — see the
> "Discovery vs. Execution" section of `SPEC_DRIVEN_BUILD_FRAMEWORK.md` before continuing.

<...>

---

## What this is NOT

> Non-goals. This list is load-bearing: anything appearing in a spec, ticket, or PR that matches
> an item here is auto-rejected. Be specific. "Not a social network" is weak; "No user-to-user
> messaging, no follower graph, no public profiles" is enforceable. Aim for 5-10 concrete items.

- **Not <X>.** <why / what that would mean>
- <...>

---

## Users

> Who specifically uses this? One persona or several? What is their technical level? What are the
> concrete moments the product is designed for (the situations in which someone reaches for it)?

<...>

---

## The core loop

> The central flow of the product, end to end. An ASCII diagram is encouraged — it forces you to
> name every stage and every data handoff. Call out which stage is the long-game / highest-value
> artifact the product accumulates over time, if any.

```
<...>
```

---

## Architecture

### Stack

> Language, framework, database, any external services, deployment target. Mark anything genuinely
> undecided as "deferred to the phase that needs it" rather than guessing now.

- **Backend:** <...>
- **Database:** <...>
- **Frontend:** <...>
- **External services / APIs:** <...>
- **Deployment:** <...>

### Major data entities

> The nouns of the system. For each: what it is, its key fields, and any invariant that defines it
> (e.g. "immutable once created; edits produce a new version").

- **<Entity>** — <description and invariants>
- <...>

---

## Hard constraints

> Auto-fail criteria, grep-checked on every PR. **A constraint that can't be checked by a script
> is not a hard constraint — it's a hope.** Each entry should name the rule AND how it's verified
> (grep target, schema enforcement, behavioral contract test). Number them; downstream specs
> reference them by ID.

1. **<Constraint>.** <statement>. Grep target: `<pattern>` in `<scope>` fails review.
2. **<Constraint>.** <statement>. Schema-enforced via <mechanism>.
3. <...>

---

## Cost contracts

> Only if the product spends money per-operation (LLM calls, paid APIs). Each contract names a
> scope, a budget (and hard ceiling), and a verification query against real data. Delete this
> section if it doesn't apply. See `SPEC_DRIVEN_BUILD_FRAMEWORK.md` for the full pattern.

- **<Per-operation budget>:** ≤ $<X> per <unit>. Hard ceiling $<Y>.
- **Verification:** <query or method against real usage data>.
- <...>

---

## Phase plan

> Break the build into phases (3+ to justify this framework). Each phase is a shippable increment
> with a clear scope boundary. Phase 1 should be deliberately low-stakes — scaffolding that
> exercises the framework before real product logic is on the line.

### Phase 1: <name>

<scope — what's in, what's explicitly deferred>

### Phase 2: <name>

<...>

### Phase N: <name>

<...>

---

## Open decisions (deferred to phase specs)

> Decisions you are deliberately NOT making yet, with a note on which phase will make each one.
> Naming them here prevents an implementer from silently deciding for you mid-phase.

- <decision> — decided in <phase>.
- <...>

---

## Success criteria

> How you'll know the project (or this stage of it) succeeded. Be concrete enough to check.

- <...>

---

## Living document policy

This file is updated only when something at the project level genuinely changes. Phase-level
changes belong in phase specs, not here. If you find yourself wanting to edit this file mid-phase
because something was harder than expected, stop and ask whether the change really belongs at this
layer — that urge is usually drift trying to get in. See the anti-patterns in `USING_THE_FRAMEWORK.md`.
