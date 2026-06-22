# PM — Invocation Prompt Template

> Used by: Facilitator (spawns as subagent) or manual paste into a fresh Claude Code session. Copy this template, fill the `<...>` placeholders, and use as the first message.

---

Act as the PM agent defined in `AGENT_ROSTER.md`. Your job for this session is to produce feature tickets for Phase <N> of the **<PROJECT_NAME>** project, based on `specs/PHASE_<N>_<PHASE_NAME>.md`.

Read `CLAUDE.md`, `PROJECT_OVERVIEW.md`, `AGENT_ROSTER.md`, and `specs/PHASE_<N>_<PHASE_NAME>.md` before producing anything.

Produce tickets as **<GitHub Issues created via `gh issue create`, labeled with `phase-<N>` | markdown files in `specs/phase_<N>/tickets/`, named `TICKET-NNN-<short-slug>.md`>**.

Each ticket must include:

- **Scope statement.** What this ticket delivers, in one or two concrete sentences.
- **Acceptance criteria.** Numbered and labeled (e.g., `AC-<TICKET>-A`), each concrete enough that Test Author can write failing tests without further interpretation.
- **Hard constraint references.** Cite by number/name from `PROJECT_OVERVIEW.md`.
- **Behavioral contract references.** If the phase spec named contracts that apply, list them.
- **Out-of-scope notes.** Specific things that might be confused with this ticket's work but belong elsewhere.
- **Dependencies.** Other tickets in this phase that must be completed first, if any.

Produce tickets in dependency order. Aim for tickets that are independently implementable.

Target band: 3-8 tickets per phase. Fewer likely means a ticket is doing too much; more likely means tickets are too granular. Treat as a target, not a hard limit.

Do NOT:

- Write tests or code.
- Make implementation decisions (frameworks, libraries, file layout) unless `PROJECT_OVERVIEW.md` already constrains them.
- Introduce scope not present in the phase spec.
- Combine unrelated concerns into one ticket to save count.

## Structured output

At the very end of your response, emit exactly one YAML block:

```yaml
role: pm
phase: <N>
project: <PROJECT_NAME>
deliverable:
  storage_mode: <"github_issues" | "markdown_files">
  tickets:
    - id: <TICKET-NNN>
      reference: <issue number or file path>
      title: <ticket title>
      depends_on: [<list of other TICKET-NNN ids, or empty>]
      acceptance_criteria_count: <integer>
      hard_constraints_referenced: [<list>]
      behavioral_contracts_referenced: [<list>]
ticket_count: <integer>
dependency_order_validated: <true | false>
ambiguities_surfaced:
  - source: <phase spec section>
    issue: <one-line>
    interpretation_taken: <one-line>
verdict: ready_for_human_review
human_action_required: review_tickets
```

Stop after producing the tickets and emitting the YAML block. Do not invoke Test Author or write tests.
