<!-- framework-version: 0.2.0 -->
<!-- file-role: lightweight-readme -->

# Lightweight Adaptations

The full spec-driven-build framework (root of this repo) is designed for multi-phase projects where you're building something from scratch and need to defend against product-level drift. It's appropriate for greenfield builds — multiple phases, real architecture decisions, hard constraints to enforce across many features.

It's overkill for ticket-scale work. When you're working on a single ticket in an existing codebase, with a thorough ticket from a human PM and a team that reviews PRs socially, most of the framework's roles are redundant — the humans are already playing them. What remains is the one role no human is playing pre-merge: the clean-context adversarial reviewer.

This directory holds *lightweight adaptations* of the framework — pared-down versions tuned for specific contexts. Each adaptation keeps the framework's load-bearing discipline (clean-context review, structured outputs, human gates) while dropping the scaffolding (`PROJECT_OVERVIEW.md`, phase specs, the full agent roster, the Facilitator's state machine).

## When to use what

- **Full framework** — multi-phase projects, especially greenfield. You own the product definition. Use the Facilitator from day one. See `~/projects/spec-driven-development-framework/README.md`.
- **Lightweight (ticket-scale)** — ticket-driven work in an existing codebase with a PM who writes thorough tickets and a team that does social PR review. The pattern in `TICKET_SCALE_PATTERN.md` is the reference instance. See `lightweight/README.md` (this file) for the shared design and `TICKET_SCALE_PATTERN.md` for the worked example.
- **Nothing** — bug fixes that take an hour, weekend hacks, throwaway exploration. Framework overhead is not justified. Just write the code.

If you're unsure which to pick, the test is: "Could this work surface product-level drift that a human PR reviewer would also miss?" If yes, full framework. If no, lightweight or nothing.

## What lightweight adaptations share

The pattern, regardless of specific instance:

1. **Two agents.** An implementer (combines what the full framework splits into Test Author + SWE), and a reviewer (clean context, reads the diff cold against the ticket and project constraints).
2. **Asymmetric context.** The implementer reads everything — ticket, project constraints, personal notes, codebase. The reviewer reads only the ticket, the constraints, and the diff. Personal notes (if any) are explicitly out of bounds for the reviewer.
3. **One human gate.** Before the PR is created. Not multiple gates per ticket.
4. **A scratch artifact.** The implementer writes a draft PR description (factual, no rationalization) to a scratch location. The reviewer is allowed to read it.
5. **Per-instance customization.** Each adaptation has its own slash commands, its own conventions, its own way of finding tickets and notes, its own CI integration. The common bones are in this directory; the specifics live in the project repo using the adaptation.

## Adaptations included

- **`TICKET_SCALE_PATTERN.md`** — a worked ticket-scale adaptation: ticket-driven work on a mature web codebase. Manager-authored tickets, a CI system with known flake categories, automated ticket linking, an external personal-notes vault. Reference implementation, with all specifics generalized so you can map them onto your own tools.

## Adding a new adaptation

If you encounter a context that doesn't fit the full framework but also doesn't quite fit an existing lightweight pattern, write a new `<CONTEXT>_PATTERN.md` in this directory. Keep the shared properties above; vary what's contextually specific. Update this README to link the new pattern.

## Generic templates

`prompts/` holds generic versions of the lightweight pattern's prompts (implementer, reviewer, review-only, ci-monitor). Each project-specific adaptation forks from these and fills in details.
