# Changelog

All notable changes to the spec-driven-build framework are documented here. The "why" matters more than the "what" — entries explain reasoning, not just list files changed.

## [0.1.0] — 2026-05-18

Initial framework release. Pre-pilot. Captures the framework as designed before any project has been built with it end-to-end.

### Included
- `SPEC_DRIVEN_BUILD_FRAMEWORK.md` — methodology
- `AGENT_ROSTER.md` — the seven-role pipeline
- `README.md` — orientation and status
- `USING_THE_FRAMEWORK.md` — operational glue for applying the framework to a project
- `templates/CLAUDE.md` — per-project bootstrap file

### Known untested
The framework has not been run on a real project. The Trade Trainer pilot is the first application; expect 0.2.0 to fold in retrospective findings from that pilot.

### Design intent for the pilot
Use the framework as written. Do not pre-build infrastructure (CI checks, prompt templates, ticket trackers) before the pilot has surfaced what is actually needed. Build that tooling for 0.2.0 with the benefit of lived experience.
