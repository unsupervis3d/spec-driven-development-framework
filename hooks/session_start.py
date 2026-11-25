#!/usr/bin/env python3
"""SessionStart hook: point Claude at the spec-driven-build framework when the repo calls for it.

Claude Code adds this hook's stdout to Claude's context at the start of a session. The hook is
silent unless the working directory is one of:

  a framework project   `.facilitator/state.json` exists: report the phase and state, and suggest
                        `/spec-driven-build:facilitator` to continue.
  a framework project   `PROJECT_OVERVIEW.md` exists, or `CLAUDE.md` names the framework, but
  not yet started       the Facilitator has not run: suggest the Facilitator.
  a new project         no source files yet: offer `/spec-driven-build:new-project` before any
                        code is written.

Existing repos that don't use the framework get nothing, so everyday work elsewhere isn't nagged.

Environment:
  SPEC_DRIVEN_BUILD_KICKOFF=off     Disable.
  SPEC_DRIVEN_BUILD_KICKOFF=always  Also mention the lightweight commands in other git repos.
Never fails a session: any error prints nothing and exits 0.
"""

import json
import os
import sys

# Files that don't make a directory a project yet.
SCAFFOLD_NAMES = {
    ".git", ".gitignore", ".gitattributes", ".DS_Store", ".claude", ".vscode", ".idea",
    ".editorconfig", "CLAUDE.md", "AGENTS.md", ".github", "docs",
}
SCAFFOLD_PREFIXES = ("readme", "license", "licence", "copying", "code_of_conduct", "contributing")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".claude", ".idea", ".vscode"}
MAX_SCAN = 2000  # stop walking big trees early; a tree this big is not a new project


def project_root(cwd):
    d = os.path.abspath(cwd)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d, True
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.abspath(cwd), False
        d = parent


def is_scaffold(name):
    lower = name.lower()
    return name in SCAFFOLD_NAMES or lower.startswith(SCAFFOLD_PREFIXES)


def has_source_files(root):
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        top = os.path.abspath(dirpath) == os.path.abspath(root)
        for name in filenames:
            seen += 1
            if seen > MAX_SCAN:
                return True
            if top and is_scaffold(name):
                continue
            return True
        if top:
            dirnames[:] = [d for d in dirnames if not is_scaffold(d)]
    return False


def read(path, limit=20000):
    try:
        with open(path, errors="ignore") as f:
            return f.read(limit)
    except OSError:
        return ""


def message(root, is_git, mode):
    state_path = os.path.join(root, ".facilitator", "state.json")
    if os.path.isfile(state_path):
        try:
            state = json.loads(read(state_path, 200000) or "{}")
        except ValueError:
            state = {}
        phase = str(state.get("current_phase", "?"))[:80]
        current = str(state.get("current_state", "?"))[:200]
        version = state.get("framework_version", "?")
        return (
            "spec-driven-build: this repo is a framework project (framework %s, phase %s, state: %s). "
            "Work here follows the framework's phases and human gates. If the user wants to continue "
            "the project, ask where things stand, or start the next step, suggest they run "
            "/spec-driven-build:facilitator. For a small change outside the current phase, follow "
            "the user's lead, but don't edit specs, tickets or .facilitator/ state outside the "
            "Facilitator." % (version, phase, current))

    overview = os.path.isfile(os.path.join(root, "PROJECT_OVERVIEW.md"))
    claude_md = read(os.path.join(root, "CLAUDE.md"))
    if overview or "spec-driven-build" in claude_md:
        return (
            "spec-driven-build: this repo is set up for the framework but its Facilitator hasn't run "
            "yet. If PROJECT_OVERVIEW.md is marked DRAFT, it needs the user's approval first. When "
            "the user wants to start building, suggest /spec-driven-build:facilitator, which begins "
            "phase 1.")

    home = os.path.abspath(os.path.expanduser("~"))
    if root in (home, os.path.abspath(os.sep)):
        return None
    if not has_source_files(root):
        return (
            "spec-driven-build (your organization's standard way to build software with Claude): "
            "this directory has no source files yet, so it looks like a new project. Before writing "
            "any code, offer the user /spec-driven-build:new-project. It interviews them to scope "
            "the project (what it is and isn't, users, the core loop, how a human will verify each "
            "phase, hard constraints, phases, delivery) and creates the project skeleton. Offer it "
            "once, briefly. If the user declines or wants a throwaway experiment, go along with "
            "that.")

    if mode == "always" and is_git:
        return (
            "spec-driven-build: this repo doesn't use the full framework. For ticket-scale work the "
            "lightweight commands are available: /spec-driven-build:ticket <id> (implement, cold "
            "review, human gate, PR) and /spec-driven-build:review <pr>. Mention them only if they "
            "fit what the user is doing.")
    return None


def main():
    mode = os.environ.get("SPEC_DRIVEN_BUILD_KICKOFF", "").strip().lower()
    if mode in ("off", "0", "false"):
        return 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    try:
        cwd = payload.get("cwd") or os.getcwd()
        root, is_git = project_root(cwd)
        text = message(root, is_git, mode)
        if text:
            sys.stdout.write(text + "\n")
    except Exception:  # never break a session start
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
