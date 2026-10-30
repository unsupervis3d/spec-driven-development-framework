# Phase <N> — Human Acceptance Run Sheet

> Copy this file to `reviews/phase_<N>/run_sheet.md` in the project repo. The Spec Author creates it
> in rubric mode (one section per human-run acceptance criterion, steps left blank); each ticket's
> SWE fills in the steps for its slice as the ticket merges; the human executes and signs it at
> `PHASE_ACCEPTANCE_RUN`; the Phase Reviewer checks the signature before passing the phase.
> Delete this blockquote.
>
> Rules:
> - Written for someone who did **not** build the feature. No step assumes knowledge of the diff.
> - Every command is copy-paste complete, environment variables included, from a clean clone.
> - Every log line, status message or screen a step promises needs a real emitter in the code.
> - Every section has at least one **negative control**: an action that should fail, failing.
> - If a step cannot be executed as written, the sheet is the defect. It goes back to the ticket
>   that owns the section; the human does not patch it in their head.
> - Plain text only. No binary, no NUL bytes, no screenshots pasted inline (link a path instead).

**Framework:** spec-driven-build v<X.Y.Z>
**Phase:** <N> — <name>
**Status:** UNSIGNED
**Human-run ACs covered:** <AC-n, AC-m, ...> (must match the phase spec's Done Definition)

---

## 0. Boot from a clean clone

> Copied from "How a human verifies a phase" in `PROJECT_OVERVIEW.md`, then made specific to this phase.

| Step | Action | Expected | Result | Proof |
|---|---|---|---|---|
| 0.1 | `git clone <repo-url> /tmp/<project>-acceptance && cd /tmp/<project>-acceptance && git checkout <commit-or-tag>` | Clone at the exact commit under review | | commit sha shown by `git rev-parse HEAD` |
| 0.2 | `<one-command boot, env vars inline, e.g. DATABASE_URL=... docker compose up --build>` | Whole stack up; `<the readiness line to look for>` appears | | log line |
| 0.3 | Open `<http://localhost:<port>/...>` or start `<CLI/API session command>` | `<what a person sees first>` | | screenshot path or command output |

---

## 1. <AC-n: name of the human-run acceptance criterion>

**Owning ticket(s):** <TICKET-NNN, ...>
**What a user is trying to do:** <one sentence>

| Step | Action | Expected | Result | Proof |
|---|---|---|---|---|
| 1.1 | <exact URL to open, button to click, input to enter, or command to run> | <what the person observes> | | <log line / output / screenshot path> |
| 1.2 | <...> | <...> | | |
| 1.N | **Negative control:** <an action that must fail — wrong input, missing permission, bad state> | <the specific refusal or error the person sees> | | |

---

## 2. <AC-m: ...>

**Owning ticket(s):** <...>
**What a user is trying to do:** <...>

| Step | Action | Expected | Result | Proof |
|---|---|---|---|---|
| 2.1 | <...> | <...> | | |
| 2.N | **Negative control:** <...> | <...> | | |

---

## Signature

| Field | Value |
|---|---|
| Executed by | <human> |
| Date | <YYYY-MM-DD> |
| Environment | <OS, runtime versions, commit sha, how booted> |
| Section 0 (boot) | <pass / fail> |
| Section 1 | <pass / fail> |
| Section 2 | <pass / fail> |
| Walked the whole first-run path, not only the new feature | <yes / no> |
| Negative control present and failed as expected in every section | <yes / no> |
| Findings (if any) | <`B-n` / `N-n` IDs, routed to `reviews/phase_<N>/PHASE_<N>_TO_FIX_round<R>.md`> |

**Status after signing:** <SIGNED — PASS | SIGNED — FAILED, fix round <R> opened>
