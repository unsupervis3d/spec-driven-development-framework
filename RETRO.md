# Trade Trainer — Retro Notes

> Append observations during the work, not after. Small annoyances forgotten by phase-end are the most informative data. Date entries. Be honest. The framework is on trial here, not you.

Format suggestion (not enforced):

```
## YYYY-MM-DD — Phase N — <short tag>

What happened:
What I noticed:
What might be a framework problem:
What might be a project problem:
```

---

## Phase 1 — Foundation

2026-05-18 — Phase 1 — PM ticket quality
    PM produced 5 well-siloed GitHub tickets from the Phase 1 spec.
    Substantially better separation than the single-file-per-spec approach used on Theia.
    Possible framework win: the spec/ticket separation (Spec Author writes the phase spec,
    PM splits it into features) produces better feature boundaries than asking one agent to do both.

2026-05-19 — Phase 1 — Test Author found real ticket bugs
Test Author surfaced two ambiguities in TICKET-001:

AC-001-K's grep target . was over-broad and would catch framework documentation references to forbidden terms. Fixed in the ticket; commit <hash>.
AC-001-F left the cookie-flag interface unspecified, requiring tests to accept multiple shapes. Left as-is for this ticket; flagged for review across more tickets.
Framework observation: the Test Author role is doing real spec-validation work in addition to writing tests.
This is a desirable property and probably worth naming explicitly in the role's description in
AGENT_ROSTER.md v0.2.0 — "Test Author surfaces spec ambiguities before code is written" rather than just
"Test Author writes failing tests."

2026-05-18 — Phase 1 — SWE TICKET-001 scope discipline
SWE surfaced three out-of-scope observations (missing tests/contracts/ dir, egg-info gitignore gap,
unconfigured git identity) and implemented zero of them. Reported them in the PR summary instead.
Framework observation: the "note observations, don't implement them" instruction in the SWE prompt
appears to be doing real work. Candidate for explicit inclusion in AGENT_ROSTER.md's SWE role definition.

2026-05-19 — Phase 1 — Tester role earns its keep on TICKET-001
Tester produced four kinds of verification beyond what Test Author + SWE produced:

End-to-end uvicorn launch (TestClient bypasses lifecycle; Tester didn't).
Wire-bytes inspection (caught the AC-001-I whitespace ambiguity).
Project-level scope-creep audit ("nothing trade-related, LLM-related, auth-related, or DB-related leaked in" — verifying absence, not just presence).
Cross-spec judgment (correctly classified RETRO.md as in-scope by reading the phase spec, not the ticket).
Framework conclusion: the Tester role is doing real work distinct from Test Author and PR Reviewer. The earlier open question in AGENT_ROSTER.md about whether Tester earns its keep — at least on this evidence — answers yes.
