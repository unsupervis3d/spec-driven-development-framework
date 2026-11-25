---
name: ticket-status
description: Show in-flight lightweight work units, their PRs, and CI state.
argument-hint: "[<work-unit-id>]"
disable-model-invocation: true
---

**Settings.** Values in angle brackets below (`<HOW_TO_FETCH_WORK>`, `<CONSTRAINTS_FILE>`, ...) come
from the "Lightweight settings" section of the project's `CLAUDE.md`. If that section or a key is
missing, ask the human for the value once, offer to add it to `CLAUDE.md`, and don't guess. The
section's format is in `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md`.

Read `<STATE_FILE, e.g. .claude/in_flight.json>`. If `$ARGUMENTS` is given, report only that work unit;
otherwise report all.

For each entry: work unit id, PR number and URL, current status (`implementing`, `awaiting_review`,
`awaiting_human_gate`, `monitoring_ci`, `ci_green`, `ci_failed`, `merged`), last update time, and
the CI summary from `gh pr checks <pr>` if a PR exists. Flag any entry whose last update is older
than `<STALE_THRESHOLD, e.g. 2 days>`.

Do not modify the state file. Report in a table, one row per work unit.
