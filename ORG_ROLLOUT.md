# Making spec-driven-build your org's standard

> How to make this framework the default way people in your organization build software with
> Claude: installed for everyone, offered automatically when someone starts a new project, and held
> to its gates and model split once they do.

No single setting makes a methodology standard. Five layers do it together. Each one closes a gap
the previous one leaves open.

| Layer | What it does | Mechanism | Can a user switch it off? |
|---|---|---|---|
| 1. Distribution | One copy of the framework that your org controls | Your fork of this repo, which is also the plugin marketplace | n/a |
| 2. Installation | Every user has both plugins, with no setup step | Managed settings: `extraKnownMarketplaces` + `enabledPlugins` | No |
| 3. Instructions | Claude knows this is how your org works, in every session | Managed `CLAUDE.md` | No |
| 4. Kickoff | A new or empty repo gets the scoping interview offered before any code is written; a framework repo gets pointed at its Facilitator | The plugin's `SessionStart` hook and the `new-project` skill | Only with `SPEC_DRIVEN_BUILD_KICKOFF=off` |
| 5. Enforcement | Output is checked by a human and by reviewers on the right model | Human gates, signed run sheets, the subagent model guard | The guard: no, under a managed policy. The gates: by skipping the Facilitator, which layers 3 and 4 make the unusual path |

## 1. Fork and pin

Fork this repository into your GitHub org. Your fork is the marketplace everyone installs from, so:

- **You decide when people move to a new version.** Both plugins pin their `version`, and users
  only update when that string changes in your fork. Merge upstream releases when you're ready.
- **Org changes live in one place:** extra hard constraints, tighter prompts, a different model
  tier. Edit the fork, bump the version, and push.

Run `python3 verify_framework.py` before every release. It checks the plugin versions match the
changelog.

## 2. Install for everyone

Deploy `templates/org/managed-settings.json` through your Claude Code managed settings:
server-managed settings, MDM, or the `managed-settings.json` file. Replace `<your-org>` first.

```json
{
  "extraKnownMarketplaces": {
    "spec-driven-build-plugins": {
      "source": { "source": "github", "repo": "<your-org>/spec-driven-development-framework" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": {
    "spec-driven-build@spec-driven-build-plugins": true,
    "subagent-model-guard@spec-driven-build-plugins": true
  }
}
```

- **Rollout:** every user gets both plugins at the start of their next session.
- **Users can't opt out.** A plugin enabled in managed settings can't be disabled at user or project
  scope.
- **`allowManagedHooksOnly`:** if you set it, these plugins' hooks still run, because hooks from
  plugins force-enabled in managed settings are exempt.
- **`strictKnownMarketplaces`:** add it if you also want to stop people installing plugins from
  other sources.

**Without managed settings,** people install the plugins themselves:

```
/plugin marketplace add <your-org>/spec-driven-development-framework
/plugin install spec-driven-build@spec-driven-build-plugins
/plugin install subagent-model-guard@spec-driven-build-plugins
```

That works, but it's opt-in, and the rest of this guide assumes the managed route.

## 3. Tell Claude how your org works

Deploy `templates/org/CLAUDE.md` as the managed `CLAUDE.md`:
- `/Library/Application Support/ClaudeCode/CLAUDE.md` on macOS
- `/etc/claude-code/CLAUDE.md` on Linux
- `C:\Program Files\ClaudeCode\CLAUDE.md` on Windows
- or inline under the `claudeMd` key of managed settings

It loads in every session, before user and project instructions, and users can't exclude it. It
says what the standard is: new projects start with the interview, framework projects run through
the Facilitator, every change comes with testing steps, and subagents name their model. Add your
org's specifics, such as where tickets live and the merge rules.

## 4. Kickoff: new projects start with scoping

This layer needs no configuration. When a session starts, the `spec-driven-build` plugin's hook
looks at the repo:

| The repo is | Claude is told to |
|---|---|
| Empty, or only a README, licence or design doc | Offer `/spec-driven-build:new-project` before writing any code |
| Set up for the framework, Facilitator not yet run | Suggest `/spec-driven-build:facilitator` to start phase 1 |
| A framework project in progress | Report the phase and state, and suggest the Facilitator to continue |
| Any other existing repo | Nothing |

`/spec-driven-build:new-project` is the scoping interview. It asks, in rounds:
- what the project is and is not, and who its users are;
- the core loop that must work end to end;
- **how a human will verify each phase** (a command, a UI, or both);
- hard constraints, which it pushes to be checkable by a script;
- a phase plan of end-to-end slices;
- success criteria, the delivery mode, and the test commands.

Then it creates `CLAUDE.md`, a draft `PROJECT_OVERVIEW.md`, `DECISIONS.md`, `RETRO.md`, `specs/` and
`reviews/`. Before anything gets built, the person approves the overview section by section. For an
existing codebase, it sets up a discovery pass that inventories the code itself, so nobody has to
describe it from memory.

## 5. Enforcement: proper output

What makes the output trustworthy once a project is running:

- **Human gates.** The Facilitator stops at every gate and quotes the reviewers' findings word for
  word. The person rules on each finding.
- **Testing steps at every PR.** The SWE writes numbered steps, and the Tester checks a human can
  follow them as written. A gate without followable steps isn't open.
- **A signed run sheet at the end of every phase.** A person runs the phase's steps from a clean
  clone and signs it. The Phase Reviewer blocks the phase while it's unsigned, and no standing
  authorization covers it.
- **The model split.** Writers run on the build tier and every reviewer on the judge tier. The guard
  denies spawns that break this, and audits the model each subagent actually ran on.
- **Fresh-context reviewers.** PR and Phase Reviewers never see the implementer's reasoning.

To stop people switching the guard off with `SUBAGENT_MODEL_GUARD=off`, deploy
`templates/org/subagent_model_policy.json` to the managed-settings directory. The same file is where
you would change the model tiers for the whole org.

## What this can't do

- **It can't make someone use the Facilitator.** A person can ignore the offer and ask Claude to
  write code directly. The layers above make the framework the default and the easiest path. They
  don't make it the only one. If you need a hard stop, add a merge-time check, for example a CI job
  that requires `PROJECT_OVERVIEW.md` and a signed run sheet for the phase being merged.
- **It can't judge whether a scope is good.** The interview makes the right questions unavoidable,
  but the answers are the person's. Review the first few `PROJECT_OVERVIEW.md` files as a team;
  that's where the habit forms.
- **It only covers machines that get your managed settings.** Personal machines and other tools
  are outside it.

## A rollout that works

1. **Pilot** with one team on one new project, using the user-level install. Read their `RETRO.md`
   after the first phase.
2. **Adjust** the fork: tighten the prompts, add org hard constraints, fix whatever confused the
   pilot. Bump the version.
3. **Turn on managed settings** for the wider group, with the managed `CLAUDE.md` alongside.
4. **Hold a review of the first few `PROJECT_OVERVIEW.md` files.** The scoping step is where the
   framework pays off or doesn't.
