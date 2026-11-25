# How we build software with Claude

> Org-wide instructions. Deploy as the managed `CLAUDE.md`: `/Library/Application Support/ClaudeCode/CLAUDE.md`
> (macOS), `/etc/claude-code/CLAUDE.md` (Linux), `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows),
> or inline under the `claudeMd` key of managed settings. Users can't exclude it. Edit the
> bracketed parts and delete this blockquote.

<Org name> builds software with Claude using the **spec-driven-build framework**, installed for
everyone as the `spec-driven-build` plugin.

- **New projects start with `/spec-driven-build:new-project`.** It scopes the project with the
  person and drafts `PROJECT_OVERVIEW.md` for their approval. When someone asks you to start
  building something new, offer it before writing code. A throwaway experiment can skip it if the
  person says so.
- **Framework projects run through `/spec-driven-build:facilitator`.** In a repo with
  `.facilitator/state.json`, specs, tickets and `.facilitator/` state change only through the
  Facilitator, and every human gate waits for the person.
- **Ticket-scale work in existing codebases** uses `/spec-driven-build:ticket <id>`: implement,
  cold-context review, the human walks the testing steps, then the PR.
- **Every change a person is asked to accept comes with numbered testing steps** they can follow
  against a running build, by command or in the UI.
- **Subagents name their model.** Writers run on `sonnet`, and reviewers, testers and planners on
  `opus`. The subagent model guard denies spawns that don't follow this. When it denies one,
  re-issue the call with the model it names.

<Add org specifics: where tickets live, the GitHub org, the review and merge rules, who to ask.>
