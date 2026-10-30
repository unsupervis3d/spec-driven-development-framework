---
description: Show in-flight work units, their PRs, and CI state (lightweight pattern)
argument-hint: [<work-unit-id>]
---

Read `<STATE_FILE, e.g. .claude/in_flight.json>`. If `$1` is given, report only that work unit;
otherwise report all.

For each entry: work unit id, PR number and URL, current status (`implementing`, `awaiting_review`,
`awaiting_human_gate`, `monitoring_ci`, `ci_green`, `ci_failed`, `merged`), last update time, and
the CI summary from `gh pr checks <pr>` if a PR exists. Flag any entry whose last update is older
than `<STALE_THRESHOLD, e.g. 2 days>`.

Do not modify the state file. Report in a table, one row per work unit.
