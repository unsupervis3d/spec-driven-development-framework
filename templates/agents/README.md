# Role files for Claude Code subagents

> Copy this directory into a project repo as `.claude/agents/`, replace every `<...>` placeholder
> in each file, and delete this blockquote. Framework v<X.Y.Z>.

This is the **native-subagent install path** for the seven worker roles. It is equivalent to the
pasted-prompt path: each role file points at the same `AGENT_ROSTER.md` definition and the same
`prompts/<role>.md` template, and emits the same structured output. The Facilitator may use either
path; `CLAUDE.md` records which one the project uses. The advantage of this path is that a role is
spawnable by name, in fresh context, with a tool allowlist the harness enforces rather than one the
prompt merely requests.

## Spawning a role

The Facilitator (or a human on the manual path) spawns a role with one instruction:

> Read `.claude/agents/<role>.md` and act as that role for `<TICKET-NNN | Phase N>`. Phase `<N>`,
> delivery mode `<github_pr | local_branch>`, fix round `<0 | R>`, amendments in force
> `<A-n list | none>`.

The spawner passes nothing else. No conversation history, no narrative of what was done, no other
role's structured output. The role's view of the world is its file, the framework docs it names,
and the project repo. Reviewer roles are spawned with a fresh session every time; this is the
property their value depends on.

## Shared operating rules

Every role file inherits these (they mirror `FACILITATOR.md`, "Subagent operating rules"):

1. One file or one command per tool call. Large batched calls hide failures.
2. **No git state changes.** No add, commit, branch, checkout, push, or PR creation. Never edit
   `.gitignore`. Roles write files; the Facilitator or the human does git at the gate. The `tools:`
   allowlist cannot express "Bash without git", so this rule is enforced by instruction; a role that
   mutates git state has violated its file and the Facilitator stops.
3. Reviewer roles (`tester`, `pr-reviewer`, `phase-reviewer`) do not read `reviews/`, `RETRO.md`,
   `.facilitator/`, or `DECISIONS.md` narrative before forming a verdict. They read the rubric, the
   spec, the ticket, the diff, and (in fix rounds) their own prior report.
4. Kill only processes you started, by PID. Leave none behind.
5. Verifiers that share a working tree run one at a time.
6. Every role ends its response with exactly the structured YAML block its `prompts/<role>.md`
   template specifies, and nothing after it. The Facilitator parses that block and quotes it
   verbatim at the human gate.

## Filling the placeholders

| Placeholder | Meaning |
|---|---|
| `<framework-path>` | Absolute path to the framework repo on this machine (same value as in `CLAUDE.md`). |
| `<PROJECT>` | The project name as written in `PROJECT_OVERVIEW.md`. |
| `<github_pr \| local_branch>` | The project's delivery mode from `.facilitator/state.json`. |
| `<test-command>` | The exact per-app test invocation (e.g. `python -m pytest apps/api/tests -q`). |
| `<constraint-scripts>` | The executable hard-constraint greps/scripts from the rubric, or "see rubric". |

Models per role live in `CLAUDE.md` ("Worker models") and in `state.json`, not here, so one role
file works whichever model the project assigns.
