#!/usr/bin/env python3
"""PreToolUse hook: block subagent spawns that would run on the wrong model.

A Claude Code subagent runs on the session's model unless the spawn passes `model` or the agent's
definition pins one. Without a gate, a role-to-model table is advice: an orchestrator running on the
most expensive model spawns every implementer on it too. This hook is the gate. It runs in every
permission mode, including auto-approve and bypass-permissions.

It inspects two tools:

  Agent / Task  Each spawn is classified by role and denied if its effective model (the `model`
                argument, else the agent definition's `model:` pin) is not allowed for that role's
                tier. Unroled spawns must still resolve to an explicit model.
  Workflow      Every `agent()` call in the script must pass `model`; calls whose label, agentType
                or prompt names a role must pass a model from that role's tier. Workflow agents
                otherwise inherit the session model and never reach the Agent tool.

Role classification, strongest signal first:
  1. Agent name, ignoring any `plugin:` prefix: an exact role (`swe`, `pr-reviewer`), an alias
     (`ticket-reviewer`), or a name pattern (`*reviewer*`, `*analyzer*`, `*architect*`, ...).
  2. The spawn's description ("SWE TICKET-12", "Cold review of PR 88", "Implement ...").
  3. The prompt's opening ("Act as the SWE", "You are the **Test Author**", "You are reviewing").
  4. Structural markers anywhere in the prompt: a `role: <role>` output block, or a reference to a
     role template (`prompts/swe.md`, `.claude/agents/tester.md`).

Policy is layered, each layer overriding the one before:
  1. the defaults in this file;
  2. `subagent_model_policy.json` beside this script (shipped with the plugin, replaced on update);
  3. `<config dir>/subagent_model_policy.json` (a user's own changes; survives plugin updates);
  4. `subagent_model_policy.json` in the OS managed-settings directory (an org's policy; wins over
     everything, so users cannot loosen it).
Decisions are appended to a JSON-lines log. Internal errors fail open: the spawn proceeds and the
error is logged, so a guard bug never stalls work.

Environment:
  SUBAGENT_MODEL_GUARD=off      Disable for sessions launched with it. Ignored when the policy sets
                                "allow_env_disable": false (recommended for managed installs).
  SUBAGENT_MODEL_GUARD_LOG=...  Log file path, or "off". Default: <config dir>/logs/subagent_model_guard.log
"""

import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
POLICY_NAME = "subagent_model_policy.json"

DEFAULT_POLICY = {
    # Tier -> allowed models, most preferred first. Denials tell the caller to pass the first one.
    "tiers": {
        "build": ["sonnet"],
        "judge": ["opus", "fable"],
    },
    # Role -> tier. Roles that write code build; roles that check, plan or decide judge.
    "roles": {
        "swe": "build",
        "test-author": "build",
        "implementer": "build",
        "ci-monitor": "build",
        "spec-author": "judge",
        "pm": "judge",
        "planner": "judge",
        "tester": "judge",
        "pr-reviewer": "judge",
        "phase-reviewer": "judge",
        "reviewer": "judge",
    },
    # Exact agent names (after stripping any plugin prefix) that are a role under another name.
    "agent_aliases": {
        "plan": "planner",
        "ticket-implementer": "implementer",
        "ticket-reviewer": "reviewer",
        "review-only": "reviewer",
        "ticket-ci-monitor": "ci-monitor",
    },
    # Substrings of agent names that imply a role. Checked after exact names and aliases.
    "agent_name_patterns": {
        "phase-reviewer": "phase-reviewer",
        "pr-reviewer": "pr-reviewer",
        "reviewer": "reviewer",
        "review": "reviewer",
        "analyzer": "reviewer",
        "auditor": "reviewer",
        "validator": "reviewer",
        "hunter": "reviewer",
        "verifier": "reviewer",
        "architect": "planner",
        "planner": "planner",
        "implementer": "implementer",
        "simplifier": "implementer",
    },
    # Unroled agents must resolve to one of these explicitly (passed or pinned). Empty list = any.
    "unroled_allowed": ["haiku", "sonnet", "opus", "fable"],
    # Built-in agents that pin their own model and are never role work.
    "builtin_pinned": ["Explore", "statusline-setup", "claude-code-guide", "web-fetch"],
    # Check Workflow scripts' agent() calls.
    "check_workflows": True,
    # Honour SUBAGENT_MODEL_GUARD=off.
    "allow_env_disable": True,
}

# Spoken role names, longest first, mapped to policy roles.
ROLE_WORDS = [
    (r"phase[\s_-]*reviewer", "phase-reviewer"),
    (r"pr[\s_-]*reviewer", "pr-reviewer"),
    (r"spec[\s_-]*author", "spec-author"),
    (r"test[\s_-]*author", "test-author"),
    (r"ticket[\s_-]*reviewer", "reviewer"),
    (r"ticket[\s_-]*implementer", "implementer"),
    (r"ci[\s_-]*monitor", "ci-monitor"),
    (r"code[\s_-]*reviewer", "reviewer"),
    (r"review[\s_-]*gate", "reviewer"),
    (r"reviewer", "reviewer"),
    (r"implementer", "implementer"),
    (r"tester", "tester"),
    (r"swe", "swe"),
    (r"pm", "pm"),
]
ROLE_ALT = "|".join("(?:%s)" % p for p, _ in ROLE_WORDS)
QUALIFIERS = r"(?:(?:fresh|cold|clean)[\s-]*context\s+|adversarial\s+|independent\s+|read-only\s+)*"
INTRO_RE = re.compile(
    r"(?:act\s+as|you\s+are|you're)\s+(?:the\s+|an?\s+)?\**\s*" + QUALIFIERS + r"\**\s*(" + ROLE_ALT + r")\b\**",
    re.IGNORECASE,
)
DESC_RE = re.compile(r"^\W*(" + ROLE_ALT + r")\b", re.IGNORECASE)
DESC_REVIEW_RE = re.compile(
    r"^\W*(?:[\w-]+\s+){0,2}(?:re-?)?review\b(?!\s+(?:findings|feedback|comments|notes|fix))", re.IGNORECASE)
DESC_IMPLEMENT_RE = re.compile(r"^\W*implement(?:s|ing)?\b", re.IGNORECASE)
PROMPT_EXTRA = [
    (re.compile(r"\byou\s+are\s+implementing\b", re.IGNORECASE), "implementer"),
    (re.compile(r"\byou\s+are\s+reviewing\b", re.IGNORECASE), "reviewer"),
]
# Structural markers: an instruction to emit the role's output block, or to follow its template.
# Both need an instructing verb nearby, so a prompt that merely edits or mentions a template
# (framework maintenance, research) is not mistaken for the role.
ROLE_BLOCK_RE = re.compile(
    r"\b(?:end|finish|close|emit|output|return|report)\w*\b[^\n]{0,60}?\brole:\s*`?"
    r"(spec_author|pm|test_author|swe|tester|pr_reviewer|phase_reviewer)\b", re.IGNORECASE)
ROLE_TEMPLATE_RE = re.compile(
    r"\b(?:template|defined\s+in|follow(?:ing)?|instructions\s+(?:in|at|from)|act\s+as|acting\s+as)\b"
    r"[^\n]{0,80}?(?:prompts|agents)/(spec[_-]author|pm|test[_-]author|swe|tester|pr[_-]reviewer|phase[_-]reviewer"
    r"|ticket[_-]implementer|ticket[_-]reviewer|review[_-]only|ticket[_-]ci[_-]monitor)\.md", re.IGNORECASE)
KNOWN_MODELS = ("fable", "opus", "sonnet", "haiku")


def managed_dir():
    if sys.platform == "darwin":
        return "/Library/Application Support/ClaudeCode"
    if os.name == "nt":
        return r"C:\Program Files\ClaudeCode"
    return "/etc/claude-code"


def policy_paths():
    """Policy files in override order, lowest precedence first."""
    paths = [os.path.join(HERE, POLICY_NAME), os.path.join(config_dirs()[0], POLICY_NAME)]
    paths.append(os.environ.get("SUBAGENT_MODEL_GUARD_MANAGED_POLICY") or os.path.join(managed_dir(), POLICY_NAME))
    return paths


def load_policy(paths=None):
    policy = json.loads(json.dumps(DEFAULT_POLICY))
    for path in policy_paths() if paths is None else paths:
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            override = json.load(f)
        for key, value in override.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict) and isinstance(policy.get(key), dict):
                policy[key].update(value)
            else:
                policy[key] = value
    return policy


def normalize_model(value):
    """Map a model argument or pin to a tier alias; None means 'inherits the session model'."""
    if not value:
        return None
    v = str(value).strip().strip("'\"").lower()
    if v in ("", "inherit", "default"):
        return None
    for name in KNOWN_MODELS:
        if name in v:
            return name
    return v  # custom alias: matched literally against the policy


def canonical(name):
    return name.lower().replace("_", "-").replace(" ", "-")


def word_to_role(word):
    for pattern, role in ROLE_WORDS:
        if re.fullmatch(pattern, word, re.IGNORECASE):
            return role
    return None


def role_from_name(agent_name, policy):
    if not agent_name or agent_name in policy["builtin_pinned"]:
        return None
    name = canonical(agent_name.split(":")[-1])
    if name in ("general-purpose", "fork", "claude"):
        return None
    if name in policy["roles"]:
        return name
    if name in policy["agent_aliases"]:
        return policy["agent_aliases"][name]
    for pattern, role in policy["agent_name_patterns"].items():
        if pattern in name:
            return role
    return None


def role_from_text(description, prompt):
    description = description or ""
    prompt = prompt or ""
    m = DESC_RE.match(description)
    if m:
        return word_to_role(m.group(1))
    if DESC_REVIEW_RE.match(description):
        return "reviewer"
    if DESC_IMPLEMENT_RE.match(description):
        return "implementer"
    head = prompt[:800]
    m = INTRO_RE.search(head)
    if m:
        return word_to_role(m.group(1))
    for regex, role in PROMPT_EXTRA:
        if regex.search(head):
            return role
    m = ROLE_BLOCK_RE.search(prompt)
    if m:
        return canonical(m.group(1))
    m = ROLE_TEMPLATE_RE.search(prompt)
    if m:
        word = canonical(m.group(1))
        return {"ticket-implementer": "implementer", "ticket-reviewer": "reviewer",
                "review-only": "reviewer", "ticket-ci-monitor": "ci-monitor"}.get(word, word)
    return None


def classify(agent_name, description, prompt, policy):
    if agent_name in policy["builtin_pinned"]:
        return None  # read-only built-ins pin their own model and cannot do role work
    return role_from_name(agent_name, policy) or role_from_text(description, prompt)


def frontmatter_model(path):
    try:
        with open(path) as f:
            text = f.read(8192)
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else ""
    m = re.search(r"^model:\s*(.+?)\s*$", block, re.MULTILINE)
    return m.group(1) if m else None


def config_dirs():
    dirs = []
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        dirs.append(os.path.expanduser(os.environ["CLAUDE_CONFIG_DIR"]))
    dirs.append(os.path.expanduser("~/.claude"))
    return [d for i, d in enumerate(dirs) if d not in dirs[:i]]


def walk_up(start, *parts):
    d = os.path.abspath(start or os.getcwd())
    while True:
        candidate = os.path.join(d, *parts)
        if os.path.exists(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def plugin_roots(plugin):
    """Candidate install directories for a plugin, most authoritative first.

    Claude Code records each install in plugins/installed_plugins.json. Directory-sourced
    marketplaces (a local clone) may load the plugin in place, so their source paths are checked
    too, and the version cache is the last resort.
    """
    roots = []
    for d in config_dirs():
        base = os.path.join(d, "plugins")
        installed = (_load_json(os.path.join(base, "installed_plugins.json")) or {}).get("plugins", {})
        for key, entries in installed.items():
            if key.split("@", 1)[0] == plugin:
                for entry in entries if isinstance(entries, list) else [entries]:
                    if isinstance(entry, dict) and entry.get("installPath"):
                        roots.append(entry["installPath"])
        for market in (_load_json(os.path.join(base, "known_marketplaces.json")) or {}).values():
            location = isinstance(market, dict) and market.get("installLocation")
            catalog = location and _load_json(os.path.join(location, ".claude-plugin", "marketplace.json"))
            for item in (catalog or {}).get("plugins", []):
                source = item.get("source")
                if item.get("name") == plugin and isinstance(source, str) and source.startswith("./"):
                    roots.append(os.path.normpath(os.path.join(location, source)))
        roots.extend(sorted(glob.glob(os.path.join(base, "cache", "*", plugin, "*")),
                            key=os.path.getmtime, reverse=True))
    return [r for i, r in enumerate(roots) if r not in roots[:i]]


def find_definition(agent_name, cwd):
    """Return the definition file for a named agent, or None."""
    if ":" in agent_name:
        plugin, agent = agent_name.split(":", 1)
        for root in plugin_roots(plugin):
            candidate = os.path.join(root, "agents", agent + ".md")
            if os.path.exists(candidate):
                return candidate
        return None
    found = walk_up(cwd, ".claude", "agents", agent_name + ".md")
    if found:
        return found
    for c in config_dirs():
        candidate = os.path.join(c, "agents", agent_name + ".md")
        if os.path.exists(candidate):
            return candidate
    return None


def check_model(label, role, effective, pinned_from, policy, subject):
    """Shared verdict for a classified spawn. Returns (decision, reason)."""
    if role is not None:
        tier = policy["roles"].get(role, "judge")
        allowed = policy["tiers"][tier]
        want = allowed[0]
        if effective is None:
            return "deny", (
                "subagent_model_guard: %s '%s' is %s work (tier '%s'). With no model it would inherit "
                "the session model. Re-issue it with model: '%s' (allowed: %s)."
                % (subject, label, role, tier, want, ", ".join(allowed)))
        if effective not in allowed:
            source = " (pinned by %s)" % pinned_from if pinned_from else ""
            return "deny", (
                "subagent_model_guard: %s '%s' is %s work (tier '%s') and may only run on %s, not '%s'%s. "
                "Re-issue it with model: '%s'. Do not relabel the task or switch agent type to get "
                "around this." % (subject, label, role, tier, ", ".join(allowed), effective, source, want))
        return "allow", None
    if effective is None:
        return "deny", (
            "subagent_model_guard: %s '%s' has no model set and would inherit the session model. "
            "Re-issue it with an explicit model: 'haiku' for search, reading and summaries, 'sonnet' "
            "for building and editing, 'opus' for review, judgement and planning." % (subject, label))
    allowed = policy.get("unroled_allowed") or []
    if allowed and effective not in allowed:
        return "deny", ("subagent_model_guard: model '%s' is not allowed for unroled agents (%s)."
                        % (effective, ", ".join(allowed)))
    return "allow", None


def decide_agent(tool_input, cwd, policy):
    agent_name = tool_input.get("subagent_type") or "general-purpose"
    description = tool_input.get("description") or ""
    prompt = tool_input.get("prompt") or ""
    requested = normalize_model(tool_input.get("model"))
    label = description or agent_name

    if agent_name in policy["builtin_pinned"]:
        return "allow", None, None
    role = classify(agent_name, description, prompt, policy)
    if agent_name == "fork":
        if role is None:
            return "allow", None, None
        tier = policy["roles"].get(role, "judge")
        return "deny", (
            "subagent_model_guard: '%s' is %s work (tier '%s'). Forks always inherit the session model, "
            "so role work cannot run in a fork. Spawn it with subagent_type 'general-purpose' (or the "
            "project's role agent) and model: '%s'." % (label, role, tier, policy["tiers"][tier][0])), role

    pinned_raw, definition = None, None
    if agent_name not in ("general-purpose", "claude"):
        definition = find_definition(agent_name, cwd)
        if definition:
            pinned_raw = frontmatter_model(definition)
    pinned = normalize_model(pinned_raw)
    effective = requested or pinned
    decision, reason = check_model(label, role, effective, definition if not requested else None,
                                   policy, "spawn")
    return decision, reason, role


# ---- Workflow scripts -------------------------------------------------------------------------

def _skip_string(src, i):
    """Return the index just past the string/template literal starting at src[i]."""
    quote = src[i]
    i += 1
    depth = 0
    while i < len(src):
        c = src[i]
        if c == "\\":
            i += 2
            continue
        if quote == "`" and c == "$" and i + 1 < len(src) and src[i + 1] == "{":
            depth += 1
            i += 2
            continue
        if quote == "`" and depth and c == "}":
            depth -= 1
        elif c == quote and not depth:
            return i + 1
        i += 1
    return i


def _call_args(src, open_paren):
    """Return the text between the parenthesis at open_paren and its match."""
    depth, i = 0, open_paren
    while i < len(src):
        c = src[i]
        if c in "'\"`":
            i = _skip_string(src, i)
            continue
        if src.startswith("//", i):
            nl = src.find("\n", i)
            i = len(src) if nl == -1 else nl
            continue
        if src.startswith("/*", i):
            end = src.find("*/", i + 2)
            i = len(src) if end == -1 else end + 2
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                return src[open_paren + 1:i]
        i += 1
    return src[open_paren + 1:]


AGENT_CALL_RE = re.compile(r"(?<![\w.$])agent\s*\(")
OPT_MODEL_RE = re.compile(r"\bmodel\s*:\s*(['\"`])([^'\"`]+)\1")
OPT_MODEL_ANY_RE = re.compile(r"\bmodel\s*:")
OPT_STR_RE = {k: re.compile(r"\b%s\s*:\s*(['\"`])((?:(?!\1).)*)\1" % k) for k in ("label", "agentType")}


def mask_code(src):
    """Blank comments and string contents (keeping offsets) so call matching sees only code."""
    out, i = list(src), 0
    while i < len(src):
        c = src[i]
        if c in "'\"`":
            end = _skip_string(src, i)
            for k in range(i + 1, max(i + 1, end - 1)):
                if out[k] != "\n":
                    out[k] = " "
            i = end
            continue
        if src.startswith("//", i) or src.startswith("/*", i):
            end = src.find("\n", i) if src.startswith("//", i) else src.find("*/", i + 2) + 2
            end = len(src) if end <= i + 1 else end
            for k in range(i, end):
                if out[k] != "\n":
                    out[k] = " "
            i = end
            continue
        i += 1
    return "".join(out)


def agent_calls(script):
    for m in AGENT_CALL_RE.finditer(mask_code(script)):
        line = script.count("\n", 0, m.start()) + 1
        yield line, _call_args(script, m.end() - 1)


def resolve_workflow_script(tool_input, cwd):
    if tool_input.get("script"):
        return tool_input["script"], None
    path = tool_input.get("scriptPath")
    if path:
        path = os.path.expanduser(path)
        if not os.path.isabs(path):
            path = os.path.join(cwd or os.getcwd(), path)
        with open(path) as f:
            return f.read(), path
    name = tool_input.get("name")
    if name:
        for base in [walk_up(cwd, ".claude", "workflows")] + [os.path.join(c, "workflows") for c in config_dirs()]:
            if not base:
                continue
            for ext in (".js", ".mjs", ""):
                candidate = os.path.join(base, name + ext)
                if os.path.isfile(candidate):
                    with open(candidate) as f:
                        return f.read(), candidate
    return None, None


def decide_workflow(tool_input, cwd, policy):
    if not policy.get("check_workflows", True):
        return "allow", None, None
    script, _ = resolve_workflow_script(tool_input, cwd)
    if script is None:
        # A built-in named workflow, or a resume of one already checked. Nothing to inspect.
        return "allow", None, None
    problems, roles = [], []
    for line, args in agent_calls(script):
        model_m = OPT_MODEL_RE.search(args)
        has_model_key = bool(OPT_MODEL_ANY_RE.search(args))
        label_m = OPT_STR_RE["label"].search(args)
        type_m = OPT_STR_RE["agentType"].search(args)
        label = label_m.group(2) if label_m else ""
        agent_type = type_m.group(2) if type_m else ""
        role = classify(agent_type, label, args, policy)
        if role is None and agent_type in policy["builtin_pinned"]:
            continue
        if role:
            roles.append(role)
        if has_model_key and not model_m:
            # model is computed (a variable or expression). Accept it unless the call is role work.
            if role is None:
                continue
            problems.append("line %d: %s work passes a computed model; use a string literal so the "
                            "tier can be checked" % (line, role))
            continue
        effective = normalize_model(model_m.group(2)) if model_m else None
        decision, reason = check_model(label or ("agent() at line %d" % line), role, effective, None,
                                       policy, "workflow agent")
        if decision == "deny":
            problems.append("line %d: %s" % (line, reason.replace("subagent_model_guard: ", "")))
    if not problems:
        return "allow", None, ",".join(sorted(set(roles))) or None
    return "deny", (
        "subagent_model_guard: workflow agents inherit the session model unless agent() passes "
        "opts.model. Fix these calls and re-run:\n- " + "\n- ".join(problems[:20])
        + ("\n- ... and %d more" % (len(problems) - 20) if len(problems) > 20 else "")), \
        ",".join(sorted(set(roles))) or None


# ---- Entry point ------------------------------------------------------------------------------

def log_path():
    configured = os.environ.get("SUBAGENT_MODEL_GUARD_LOG")
    if configured:
        return None if configured.lower() == "off" else os.path.expanduser(configured)
    return os.path.join(config_dirs()[0], "logs", "subagent_model_guard.log")


def log(entry):
    path = log_path()
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def decide(payload, policy):
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    cwd = payload.get("cwd") or os.getcwd()
    if tool in ("Agent", "Task"):
        return decide_agent(tool_input, cwd, policy)
    if tool == "Workflow":
        return decide_workflow(tool_input, cwd, policy)
    return "allow", None, None


def find_key(obj, key, depth=0):
    if depth > 4:
        return None
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], str):
            return obj[key]
        for value in obj.values():
            found = find_key(value, key, depth + 1)
            if found:
                return found
    elif isinstance(obj, list):
        for value in obj[:20]:
            found = find_key(value, key, depth + 1)
            if found:
                return found
    return None


def audit(payload, policy):
    """PostToolUse on Agent: compare the model the subagent actually started on with its tier.

    The spawn has already run, so this cannot block. It logs the resolved model and, on a mismatch,
    tells the calling session so the result is treated as unverified and re-run on the right tier.
    """
    tool_input = payload.get("tool_input") or {}
    resolved = normalize_model(find_key(payload.get("tool_response"), "resolvedModel"))
    agent_name = tool_input.get("subagent_type") or "general-purpose"
    role = classify(agent_name, tool_input.get("description"), tool_input.get("prompt"), policy)
    if role is None or resolved is None:
        return "audit-ok" if resolved else "audit-unknown", None, role, resolved
    tier = policy["roles"].get(role, "judge")
    allowed = policy["tiers"][tier]
    if resolved in allowed:
        return "audit-ok", None, role, resolved
    return "audit-mismatch", (
        "subagent_model_guard audit: '%s' is %s work (tier '%s', allowed: %s) but the subagent started "
        "on '%s'. Treat its result as unverified and re-run it with model: '%s'."
        % (tool_input.get("description") or agent_name, role, tier, ", ".join(allowed), resolved,
           allowed[0])), role, resolved


def main():
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        payload = json.load(sys.stdin)
        tool = payload.get("tool_name")
        if tool not in ("Agent", "Task", "Workflow"):
            return 0
        policy = load_policy()
        if payload.get("hook_event_name") == "PostToolUse":
            if tool not in ("Agent", "Task"):
                return 0
            decision, reason, role, resolved = audit(payload, policy)
            ti = payload.get("tool_input") or {}
            log({"ts": stamp, "cwd": payload.get("cwd"), "tool": tool, "event": "PostToolUse",
                 "subagent_type": ti.get("subagent_type"), "model": ti.get("model"),
                 "resolved_model": resolved, "description": ti.get("description"),
                 "role": role, "decision": decision})
            if reason:
                sys.stderr.write(reason + "\n")
                json.dump({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                  "additionalContext": reason}}, sys.stdout)
            return 0
        if os.environ.get("SUBAGENT_MODEL_GUARD", "").lower() in ("off", "0", "false"):
            if policy.get("allow_env_disable", True):
                log({"ts": stamp, "cwd": payload.get("cwd"), "tool": tool, "decision": "disabled"})
                return 0
        decision, reason, role = decide(payload, policy)
        ti = payload.get("tool_input") or {}
        log({"ts": stamp, "cwd": payload.get("cwd"), "tool": tool,
             "subagent_type": ti.get("subagent_type"), "model": ti.get("model"),
             "description": ti.get("description") or ti.get("name") or ti.get("scriptPath"),
             "role": role, "decision": decision})
        if decision == "deny":
            json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                              "permissionDecision": "deny",
                                              "permissionDecisionReason": reason}}, sys.stdout)
        return 0
    except Exception as exc:  # fail open: a guard bug must not block all subagent work
        sys.stderr.write("subagent_model_guard error (allowing call): %r\n" % (exc,))
        log({"ts": stamp, "error": repr(exc)})
        return 0


if __name__ == "__main__":
    sys.exit(main())
