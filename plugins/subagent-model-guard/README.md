# Subagent Model Guard

> A Claude Code plugin that enforces the spec-driven-build framework's role-to-model split. Without
> it, the split is a suggestion: a subagent with no `model` runs on the session's model, so an
> orchestrator on the most expensive model spawns every implementer on that model too.

## Install

In Claude Code:

```
/plugin marketplace add <owner>/<repo>
/plugin install subagent-model-guard@spec-driven-build-plugins
```

Or from a shell:

```
claude plugin marketplace add <owner>/<repo>
claude plugin install subagent-model-guard@spec-driven-build-plugins
```

`<owner>/<repo>` is the GitHub repository you got this framework from, or your org's fork of it. A
local clone works too: pass its path. New sessions pick the plugin up, and a running session needs
`/reload-plugins`. Requires `python3` (3.8+) on `PATH`.

To use it in a single session without installing: `claude --plugin-dir plugins/subagent-model-guard`.

### Org rollout

The full guide to making the framework an org standard is `ORG_ROLLOUT.md` at the repo root. For the
guard alone, put this in your managed settings (server-managed settings, MDM, or `managed-settings.json`):

```json
{
  "extraKnownMarketplaces": {
    "spec-driven-build-plugins": {
      "source": { "source": "github", "repo": "<owner>/<repo>" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "subagent-model-guard@spec-driven-build-plugins": true
  }
}
```

- **Rollout:** every user gets the plugin at the start of their next session.
- **Users can't disable it.** Managed `enabledPlugins` takes precedence over every other scope.
- **`allowManagedHooksOnly`:** its hooks keep running even if you also set this, because hooks from
  plugins force-enabled in managed settings are exempt.
- **Version control:** to approve each new version before rollout, point the marketplace at your
  org's fork. The plugin pins its `version`, so users only move when that string changes.

To stop users switching the guard off with `SUBAGENT_MODEL_GUARD=off`, also deploy a managed policy
file with `"allow_env_disable": false` (see [Policy](#policy)).

## What it enforces

Roles fall into two tiers. Roles that write code **build**, and roles that check, plan or decide
**judge**. A writer is never checked by a reviewer from its own tier.

| Tier | Roles | Default models |
|---|---|---|
| build | `swe`, `test-author`, implementer, CI monitor | `sonnet` |
| judge | `spec-author`, `pm`, planner, `tester`, `pr-reviewer`, `phase-reviewer`, any reviewer | `opus`, `fable` |

| Call | Rule |
|---|---|
| A role spawn (`Agent`/`Task`) | Its effective model (the `model` argument, else the agent file's `model:` pin) must be in its tier. |
| Any other spawn | Must resolve to an explicit model. Nothing silently inherits the session model. |
| Role work in a `fork` | Denied. Forks always inherit the session model. |
| A `Workflow` script | Every `agent()` call must pass `opts.model`, and role calls must pass a literal from their tier. |
| Read-only built-ins (`Explore`, `web-fetch`, ...) | Allowed as defined. They pin their own model. |
| After every spawn | The model the subagent actually started on (`resolvedModel`) is checked. A mismatch is logged and reported back to the session as unverified work. |

**How roles are recognised**, strongest signal first:
1. **Agent name**, ignoring any plugin prefix: `swe`, `pr-reviewer`, and names containing
   `reviewer`, `analyzer`, `validator`, `architect` or `simplifier`.
2. **The spawn's description**: "SWE TICKET-12", "Cold review of PR 88", "Implement …".
3. **The prompt's opening**: "Act as the SWE", "You are the **Test Author**".
4. **An instruction to use a role's template or output block**: "follow `prompts/tester.md`",
   "end with the `role: swe` block".

**What a denial does.** The calling session receives the exact model to pass, so it re-issues the
call and carries on. The guard runs in every permission mode, including auto-approve and
bypass-permissions.

**If the guard itself breaks.** Internal errors fail open: a bug in the guard never blocks work, and
the error is logged.

## Policy

The policy is layered, and each layer overrides the one before it:

1. **Defaults.** The bundled `scripts/subagent_model_policy.json`, which is replaced on every
   plugin update. Don't edit it.
2. **A user's changes.** `subagent_model_policy.json` in the user's Claude config dir (`~/.claude/`,
   or `$CLAUDE_CONFIG_DIR`).
3. **An org's policy.** `subagent_model_policy.json` in the OS managed-settings directory:
   `/Library/Application Support/ClaudeCode/` on macOS, `/etc/claude-code/` on Linux,
   `C:\Program Files\ClaudeCode\` on Windows. It wins over everything, so users can't loosen it.

A layer only needs the keys it changes. Lists are replaced, and maps are merged key by key.

| Key | Meaning |
|---|---|
| `tiers` | Tier → allowed models, most preferred first. Denials name the first. |
| `roles` | Role → tier. |
| `agent_aliases`, `agent_name_patterns` | Map agent names, including plugin agents, to roles. |
| `unroled_allowed` | Models a non-role spawn may name. An empty list allows any. |
| `check_workflows` | Inspect `Workflow` scripts. |
| `allow_env_disable` | Honour `SUBAGENT_MODEL_GUARD=off`. |

Keep the role agents' `model:` lines (the `spec-driven-build` plugin's `agents/`) in step with the policy. A spawn that
relies on a pin outside its tier is denied, and the denial names the file.

## Logs and switches

- **Log.** Every decision is appended as a JSON line to `<config dir>/logs/subagent_model_guard.log`.
  Each entry records the working directory, agent type, model, description and decision. Prompts
  are never logged. Set `SUBAGENT_MODEL_GUARD_LOG=<path>` to log elsewhere, or `off` to stop logging.
- **Off switch.** Launching Claude Code with `SUBAGENT_MODEL_GUARD=off` disables the guard for that
  session, unless a policy sets `allow_env_disable: false`. The log still records each call as
  `disabled`.

## Without the plugin system

Copy `scripts/` to `.claude/hooks/` (per project) or `~/.claude/hooks/` (per user). Then add this
block to the matching `settings.json`, with the path adjusted:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Agent|Task|Workflow",
        "hooks": [{ "type": "command", "command": "python3 \"/path/to/subagent_model_guard.py\"", "timeout": 10 }] }
    ],
    "PostToolUse": [
      { "matcher": "Agent|Task",
        "hooks": [{ "type": "command", "command": "python3 \"/path/to/subagent_model_guard.py\"", "timeout": 10 }] }
    ]
  }
}
```

## Verify

```
python3 plugins/subagent-model-guard/scripts/test_subagent_model_guard.py
claude plugin validate plugins/subagent-model-guard
```

Then, in a new session, ask Claude to spawn a general-purpose agent described as "SWE test" on
`opus`. It should be denied with "Re-issue it with model: 'sonnet'".

## Limits

- **Detection is lexical.** Role work hidden behind unusual wording passes as unroled, but it still
  has to name a model, so it can't silently inherit the session model.
- **Workflow checks are lexical too.**
  - A role call whose model is computed (for example `model: m`) is denied, because the tier can't
    be checked.
  - Built-in workflows referenced by name have no script to inspect, so they're allowed.
- **Only a managed rollout is tamper-proof.** A user-installed plugin can be disabled by that user.
