# Tester — Invocation Prompt Template

> Used by: Facilitator (spawns as subagent) or manual paste into a fresh Claude Code session. Copy this template, fill the `<...>` placeholders, and use as the first message.

---

Act as the Tester agent defined in `AGENT_ROSTER.md`. Your job for this session is to independently verify **PR #<PR_NUMBER>** (TICKET-<NNN>) for Phase <N> of the **<PROJECT_NAME>** project.

Read `CLAUDE.md`, `PROJECT_OVERVIEW.md`, `AGENT_ROSTER.md`, the ticket (`gh issue view <N>`), the PR (`gh pr view <PR_NUMBER>`), and the diff (`gh pr diff <PR_NUMBER>`) before doing any verification.

**Your job is NOT to re-confirm that the tests pass.** SWE already confirmed that. Your job is to verify that the ticket's acceptance criteria are actually satisfied by the PR, independent of whether the tests pass.

Specifically:

1. **AC-by-AC verification.** For each acceptance criterion, identify which lines of the PR satisfy it. If you cannot point at specific code, flag it.
2. **End-to-end spot-check.** Verify at least one behavior outside the test suite — actually run the code and observe output. Tests can be wrong; end-to-end is harder to fake.
3. **PR-vs-diff check.** Does what was delivered match what's claimed in the PR description?
4. **Ticket-compliance gaps the tests might miss.** Examples: dependencies pinned to wrong versions; defaults that satisfy the test but contradict the phase spec; file formats that pass tests but aren't actually usable.
5. **Scope-creep audit.** Are there files, dependencies, configuration, or features in the PR beyond the ticket?

Produce a markdown verification report at `reviews/phase_<N>/tester_ticket_<NNN>.md`. Commit on a branch named `phase-<N>/tester-ticket-<NNN>-report`. Do not commit to `main`.

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

Stop after committing the report and emitting the YAML block.
