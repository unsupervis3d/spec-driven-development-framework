# Tester — Invocation Prompt Template

> Used by: Facilitator (spawns as subagent) or manual paste into a fresh Claude Code session. Copy this template, fill the `<...>` placeholders, and use as the first message.

---

Act as the Tester agent defined in `AGENT_ROSTER.md`. Your job for this session is to independently verify **PR #<PR_NUMBER>** (TICKET-<NNN>) for Phase <N> of the **<PROJECT_NAME>** project.

Read `CLAUDE.md`, `PROJECT_OVERVIEW.md`, `AGENT_ROSTER.md`, the ticket (`gh issue view <N>` or the ticket file), the PR description (`gh pr view <PR_NUMBER>` in `github_pr` mode; `reviews/phase_<N>/pr_description_ticket_<NNN>.md` in `local_branch` mode), the diff (`gh pr diff <PR_NUMBER>`, or `git diff <base>...HEAD` plus untracked files), the review rubric `specs/PHASE_<N>_REVIEW_RUBRIC.md`, and any earlier Tester notes for this ticket (a prior round's report, if this is fix round <R>) before doing any verification. Do not read `RETRO.md` or other tickets' reviews.

Delivery mode: **<github_pr | local_branch>**. Fix round: <0 | R>.

Operating rules (apply to every role; see `FACILITATOR.md`, "Subagent operating rules"):

- One file or one command per tool call.
- **No git state changes.** Do not add, commit, branch, checkout, push, or create a PR. Never edit `.gitignore`. You write files; the Facilitator or the human handles git at the gate. (Manual-path users who run this prompt by hand may do the git steps themselves afterwards.)
- Kill only processes you started, by PID. Leave none behind.
- End with the structured output block below and nothing after it.

**Your job is NOT to re-confirm that the tests pass.** SWE already confirmed that. Your job is to verify that the ticket's acceptance criteria are actually satisfied by the PR, independent of whether the tests pass.

Specifically:

1. **AC-by-AC verification.** For each acceptance criterion, identify which lines of the PR satisfy it. If you cannot point at specific code, flag it.
2. **End-to-end spot-check.** Verify at least one behavior outside the test suite — actually run the code and observe output. Tests can be wrong; end-to-end is harder to fake. While you're in the running app, watch for dead ends: a control that renders but doesn't actually work (wired to an endpoint that doesn't exist, a flag nothing turns on). Flag any you find — you're the first agent to actually run the app, so this is the cheapest place to catch them.
3. **PR-vs-diff check.** Does what was delivered match what's claimed in the PR description?
4. **Ticket-compliance gaps the tests might miss.** Examples: dependencies pinned to wrong versions; defaults that satisfy the test but contradict the phase spec; file formats that pass tests but aren't actually usable.
5. **Scope-creep audit.** Are there files, dependencies, configuration, or features in the PR beyond the ticket?
6. **Walk the testing steps as written.** Follow the PR description's numbered testing steps exactly, as a stranger would, against a running instance. Do not fix a step in your head; if a command is incomplete, a URL is wrong, or the expected result doesn't match, that step fails. The human will walk these same steps at Gate 2, and your job here is to make sure they can.
7. **Mutation pass.** For each AC's test listed in the rubric's mutation list, apply the mutation in a scratch copy of the repo (never in the working tree) and confirm the test fails. A test that survives its mutation is hollow; report it.
8. **Check claimed defects against the data** before you record them. A discrepancy you can't reproduce twice is a note, not a finding.

Re-run the full suite only if code changed since the SWE's quoted run; otherwise cite the SWE's output and the commit it ran against.

Stopping rule for repeat rounds: after two fix rounds on the same guard or validation, remaining theoretical evasions become accepted notes unless an honest mistake by a real user could reach them.

Produce a markdown verification report at `reviews/phase_<N>/tester_ticket_<NNN>.md` (append `## Round <R>` for fix rounds; keep earlier rounds intact). Plain text only.

Do NOT:

- Modify code or tests.
- Approve the PR via `gh pr review --approve`. Your output is a report.
- Comment on the PR via `gh pr comment`. The report is your deliverable.

## Structured output

At the very end of your response, after the report is written and committed, emit exactly one YAML block:

```yaml
role: tester
phase: <N>
project: <PROJECT_NAME>
ticket: <TICKET-NNN>
pr: <PR_NUMBER>
report_path: reviews/phase_<N>/tester_ticket_<NNN>.md
ac_verification:
  - ac_id: <AC-NNN-A>
    verdict: <"PASS" | "FAIL" | "FLAG">
    evidence: <file:line>
    note: <one-line, only if FLAG or FAIL>
  - ac_id: <AC-NNN-B>
    verdict: <...>
    evidence: <...>
end_to_end_spot_check:
  performed: <true | false>
  what_was_run: <one-line description>
  result: <"matches expectations" | "discrepancy">
  discrepancy_note: <only if discrepancy>
dead_ends_found: [<one-line descriptions, or empty>]
testing_steps_followable: <true | false>
testing_steps_walk:
  - step: <n>
    result: <"as expected" | "failed">
    note: <only if failed: what actually happened>
mutation_pass:
  - ac_id: <AC-NNN-A>
    mutation: <one-line>
    test_failed_as_required: <true | false>
claims_checked_rather_than_trusted: [<one-line each: the SWE claim and how you verified it>]
pr_vs_diff_check:
  result: <"matches" | "discrepancy">
  discrepancy_note: <only if discrepancy>
ticket_compliance_gaps:
  - description: <one-line>
    severity: <"low" | "medium" | "high">
scope_creep:
  found: <true | false>
  items: [<list of one-line descriptions>]
overall_verdict: <"approve" | "approve_with_notes" | "request_changes" | "reject">
verdict_summary: <one-line>
blockers_for_merge:
  - <one-line description, or omit if none>
human_action_required: review_tester_report
```

Stop after writing the report and emitting the YAML block.
