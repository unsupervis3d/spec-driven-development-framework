<!-- framework-version: 0.3.1 -->
<!-- file-role: lightweight-pattern -->

# Ticket-Scale Pattern — Lightweight Adaptation Reference

This document describes how the spec-driven-build framework adapts to ticket-scale work in an
existing, mature codebase. It's both a usage doc (if you're setting up the adaptation) and a
reference implementation (if you're designing a similar lightweight pattern for another context).

It's written against a concrete-but-generic example — a team working a ticket queue on a mature web
application — so the moving parts are easy to map onto your own tools. Where it names a tool
category ("the CI system," "the issue tracker," "the notes vault"), substitute your own.

## Context

- **Codebase:** existing, mature. No bootstrapping, no architectural decisions to make from scratch.
- **PM role:** filled by a human manager. Tickets are thorough; acceptance criteria are present and
  concrete.
- **Test/review role:** filled by the team — humans review PRs socially after the author.
- **Personal notes:** the developer keeps a personal notes vault (e.g. an Obsidian vault) *outside*
  the project repo, with one file per ticket.
- **CI:** a CI system (e.g. Jenkins, GitHub Actions) with known flake categories — for example,
  search-index timeouts. A magic phrase (e.g. "rerun tests") re-triggers it.
- **Ticket linking:** an issue tracker (e.g. Zenhub, Jira, Linear). Linking is either automatic via
  the PR description, or via an API call (a small script stub handles this).

## What the full framework loses, and why it's OK

In this context, dropping the following framework roles is safe:

- **Spec Author** — the manager writes the spec (the ticket).
- **PM** — same.
- **Tester** — the team tests by reviewing the PR.
- **Phase Reviewer** — there are no phases.
- **Facilitator** — there's no multi-phase state machine to orchestrate.

What's preserved: clean-context adversarial review (the PR Reviewer role), structured outputs (for
parseability), and the human gate (before PR creation). See `../HUMAN_GATES.md` for why that one
gate is the part you cannot drop.

## Workflow

Three slash commands drive the pattern: `/ticket <N>`, `/review <PR>`, and `/ticket-status [<N>]`.
Generic versions live in the framework repo under `templates/commands/`; copy them into the
project's `.claude/commands/` and fill the placeholders. Each command reads its prompt file fresh
at spawn time so the prompt files stay the single source of truth.

```
/ticket <N>
    │
    ▼
Implementer subagent
    - fetches ticket via the issue tracker / gh
    - reads personal notes for the ticket (if any)
    - reads AGENTS.md
    - performs size scan (refuse if too big)
    - writes failing tests
    - implements
    - runs tests locally to green
    - writes PR draft to .claude/scratch/
    - appends implementation notes to the personal vault
    │
    ▼
Reviewer subagent (fresh context)
    - reads ticket, AGENTS.md, PR draft, local diff
    - does NOT read the personal vault, prior context, anything else
    - produces structured verdict
    │
    ▼
[Human gate: verdict + testing steps surfaced in chat]
    - if reviewer rejected → fix and re-run from reviewer
    - if approved → human walks testing steps against a running
      instance, exactly as written (this gate is never skipped,
      and a green CI run does not stand in for it)
    │
    ▼
[Human approval to create PR]
    │
    ▼
PR created via gh
    - PR description = PR draft
    - PR linked to ticket via ticket_link.sh
    - .claude/scratch/ cleaned up
    - .claude/in_flight.json initialized
    │
    ▼
CI Monitor subagent (long-running)
    - polls CI status (e.g. gh pr checks)
    - on flake failure: comment "rerun tests" once
    - on substantive failure: surface to human, stop
    - on green: assign the reviewer, stop
    - hard timeout at 90 minutes
```

A second entry point:

```
/review <PR>
    │
    ▼
Reviewer subagent (fresh context)
    - reads PR diff, linked ticket, AGENTS.md
    - same logic as the ticket reviewer
    - works for own PR or a teammate's PR
```

A third entry point:

```
/ticket-status [<N>]
    - reads .claude/in_flight.json
    - reports current state
```

## File layout in the project repo

```
project-repo/
├── CLAUDE.md                                 # slash command dispatch + orientation
├── AGENTS.md                                 # constraints (existing)
└── .claude/
    ├── prompts/
    │   ├── ticket_implementer.md
    │   ├── ticket_reviewer.md
    │   ├── review_only.md
    │   └── ticket_ci_monitor.md
    ├── scripts/
    │   └── ticket_link.sh
    ├── scratch/                              # gitignored; PR drafts live here briefly
    └── in_flight.json                        # gitignored; CI monitor state
```

`.claude/scratch/` and `.claude/in_flight.json` are gitignored. A global `.claude` gitignore entry
handles this.

## File layout for the personal notes vault

The notes vault lives at a stable path outside the repo, e.g. `<notes-vault-path>/`. Within it:

- `tickets/<ticket-number>-<slug>.md` — per-ticket notes. Pre-implementation thinking, conversations
  with the manager, etc.
- `templates/` — note templates.
- `README.md` (or `claude.md`) — usage guide for the vault.

The implementer appends a "Claude implementation notes" section to the existing ticket file, or
creates a new file if none exists. **The reviewer never touches the vault** — this asymmetry is the
point (the implementer reads everything; the reviewer reads only the ticket, the constraints, and
the diff, so its judgment isn't contaminated by the author's intent).

## Constraints — AGENTS.md

The constraints the reviewer checks against live in `AGENTS.md` in the project repo. In a mature
codebase this is usually an existing file that predates the framework adaptation. The reviewer
prompt treats it as the canonical list. Any constraint that's not in `AGENTS.md` is not checked.

If the team adds a constraint, it goes in `AGENTS.md`, not in the prompts. The prompts read
`AGENTS.md` dynamically; updates propagate automatically.

## The size-scan rule

The implementer refuses to proceed if the ticket is too big for the lightweight pattern. Threshold
(rough): more than ~5 acceptance criteria, or more than 2 subsystems touched, or any
schema/architectural change. The implementer outputs `verdict: too_big_for_lite` with findings, and
recommends escalation to the full framework or asking the PM to split the ticket.

This rule matters because the lightweight pattern's discipline assumes ticket scale. Forcing a
too-big ticket through `/ticket` produces a too-big PR that no clean-context reviewer can usefully
evaluate.

## The flake-classification rule

CI failures bucket into:

- **Known flake.** Comment "rerun tests" once. Update `rerun_used: true`. Examples: search-index
  timeouts, port collisions, runner allocation, agent disconnects.
- **Substantive.** Surface to human, stop polling. Anything referencing the diff, or with a real
  test failure message, or "when in doubt."

"Only once" is strict. A second failure after a rerun — flake or not — surfaces.

The detailed error output on the PR is generated by the CI system itself, not by the agent. If the
agent ever finds itself wanting to post error detail, that's a sign the CI isn't surfacing it and a
human should fix the CI side.

## Designing a different lightweight adaptation

If you're designing a lightweight pattern for a different context (consulting, weekend projects,
etc.), the dimensions to specify are:

1. **Who fills which framework role?** Identify which of Spec Author / PM / Tester / Reviewer /
   Phase Reviewer roles are filled by humans in this context. Drop the corresponding agents.
2. **Where do specs come from?** Tickets, written briefs, your own notes, something else.
3. **Where do constraints live?** A file like `AGENTS.md`, a doc somewhere, your head.
4. **What's the personal-notes asymmetry?** What can the implementer read that the reviewer cannot?
5. **What's the CI/post-PR story?** Is there CI? Who reviews after the LLM reviewer? Who merges?
6. **What's the slash command shape?** `/ticket <N>` here; could be `/brief <topic>` for a
   consulting writeup, `/build <prompt>` for a weekend hack.

The shared bones (two agents, asymmetric context, one human gate, scratch artifact) stay. The
specifics vary.
