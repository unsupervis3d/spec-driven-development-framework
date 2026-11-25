---
name: new-project
description: Start a new project (or adopt an existing repo) on the spec-driven-build framework. Interviews the human to scope it, then scaffolds CLAUDE.md, PROJECT_OVERVIEW.md, DECISIONS.md, RETRO.md, specs/ and reviews/. Use when someone starts a new project, says "new project", "scope this", "set up the framework", or opens Claude Code in an empty or near-empty repo.
argument-hint: "[one-line description of what you want to build]"
---

# Start a spec-driven-build project

You are setting up a project on the spec-driven-build framework. The framework's files are bundled
with this plugin at `${CLAUDE_PLUGIN_ROOT}`. Its method is in
`${CLAUDE_PLUGIN_ROOT}/SPEC_DRIVEN_BUILD_FRAMEWORK.md`; read the "Project overview" and "Phases"
parts before the interview so your questions land.

Your output is a **draft** `PROJECT_OVERVIEW.md` the human approves, plus the project skeleton.
You write no application code in this skill, and you do not start phase 1. The overview is the
highest-leverage artifact in the framework, so it is worth a slow, careful conversation.

## 0. Check where you are

1. Run `git rev-parse --show-toplevel` and list the repo root.
2. **Already a framework project?** If there is a `.facilitator/state.json`, a `PROJECT_OVERVIEW.md`,
   or a `CLAUDE.md` that names the spec-driven-build framework, stop. Say what you found and offer
   `/spec-driven-build:facilitator` to resume.
3. **Not a git repo?** Offer to `git init`. Do nothing else until the human answers.
4. **Greenfield or brownfield?** Greenfield means the repo has no application code yet. Brownfield
   means there is an existing codebase. Say which you think it is and confirm it in the first round
   of questions.

## 1. Interview

Ask in rounds, not all at once. Use the interactive question tools when the session has them
(`AskUserQuestion` for choices, a multi-field prompt for free text). Otherwise ask in plain text,
one round per message. Pre-fill anything you can infer from the repo or from `$ARGUMENTS`, and let
the human correct it.

Never invent an answer. If the human doesn't know yet, record it under "Open decisions" with who
decides and by when.

**Round 1: what and why**
- What is it, in two or three sentences? Who has the problem it solves?
- What is it **not**? Name at least three tempting things that are out of scope.
- Who are the users? For each: what they do, how often, and what "working" means to them.
- Greenfield or brownfield (confirm your guess)?

**Round 2: the core loop and how a human checks it**
- What is the one loop a user goes through that must work end to end? Walk it step by step.
- **How will a human verify each phase?** Every phase ends with a person running steps against a
  real build. Will that be a command (CLI output), a UI (pages and clicks), an API call, or a
  mix? What does "I can see it working" look like? This becomes "How a Human Verifies a Phase",
  the source of every phase's run sheet.

**Round 3: shape and constraints**
- Stack: language, framework, datastore, hosting. Chosen already, or open?
- Major data entities, in a line each.
- **Hard constraints**: rules the code must never break (privacy, security, licensing,
  performance, cost, compliance). Each must be checkable, ideally by a script or a grep. Push back
  on vague ones ("secure") until they are testable ("no secrets in the repo; `gitleaks` passes").
- Cost limits, if any (per request, per user, per month).

**Round 4: phases and delivery**
- A rough phase plan: 2 to 6 phases. Each phase is an end-to-end slice a human can exercise, never
  a layer ("phase 1: database").
- What does done look like for the whole project? Measurable success criteria.
- Delivery mode: `github_pr` (issues and PRs on GitHub) or `local_branch` (markdown tickets and
  local branches). For `github_pr`, run `gh auth status`, show it, and have the human confirm the
  account.
- Test, lint and type-check commands, exact invocations (or "to be decided in phase 1").
- Is there a design document? If so, where?

**Brownfield only:** don't ask the human to describe the existing code from memory. Tell them the
Spec Author will run a **discovery pass** first (step 4 below), which inventories what exists and
drafts the "Existing components" section from the code itself.

## 2. Scaffold

Read the templates first, then create these files at the repo root. Keep the templates' structure
and headings, and fill them from the interview:

| File | From | Notes |
|---|---|---|
| `PROJECT_OVERVIEW.md` | `${CLAUDE_PLUGIN_ROOT}/templates/PROJECT_OVERVIEW.md` | Filled from the interview. Every unknown goes under "Open decisions". Put `Status: DRAFT, awaiting human approval` at the top. |
| `CLAUDE.md` | `${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md` | Framework version (from `${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`), delivery mode, gh identity, test commands. If a `CLAUDE.md` exists, append a "Framework" section instead of replacing the file. |
| `DECISIONS.md` | `${CLAUDE_PLUGIN_ROOT}/templates/DECISIONS.md` | Seed it with the decisions the interview made (stack, delivery mode), as `D-1`, `D-2`, ... |
| `RETRO.md` | `${CLAUDE_PLUGIN_ROOT}/templates/RETRO.md` | As is. |
| `specs/`, `specs/amendments/`, `reviews/phase_1/` | — | Each with a `.gitkeep`. |
| `discovery/` | — | Brownfield only, with a `.gitkeep`. |

Do not create `.facilitator/`. The Facilitator creates it at its first start. Do not commit.

## 3. Approval gate

Show the human the draft `PROJECT_OVERVIEW.md` section by section. Give the hard constraints and
"How a Human Verifies a Phase" the most care. Ask them to correct, cut, or approve each section.
Apply only the edits they make or approve. When they approve the whole document, change its status
line to `Status: APPROVED <today's date>` and add `D-n: PROJECT_OVERVIEW approved` to `DECISIONS.md`.

This is a human gate. An approval given before the human has read the document doesn't count, and
neither does approval under a standing authorization.

## 4. Hand off

Tell the human, in a few lines:
- what was created, as a list of paths;
- that they should review the files and commit them (suggest tagging the commit
  `framework-bootstrap`);
- the next step: `/spec-driven-build:facilitator`, which starts phase 1. For brownfield, it starts
  with the Spec Author's discovery pass.

Make sure the subagent model guard is active: `claude plugin list` should show
`subagent-model-guard` enabled. If it isn't, give the install commands from
`${CLAUDE_PLUGIN_ROOT}/plugins/subagent-model-guard/README.md`. Don't edit settings files yourself.
