#!/usr/bin/env python3
"""Tests for subagent_model_guard.py. Standard library only.

Run from anywhere:  python3 plugins/subagent-model-guard/scripts/test_subagent_model_guard.py
"""

import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True  # keep __pycache__ out of the plugin
HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PLUGIN))
# Isolate from the machine running the tests: no user or managed policy, no real log.
_ISOLATED = tempfile.mkdtemp(prefix="guard-test-")
atexit.register(shutil.rmtree, _ISOLATED, True)
os.environ["CLAUDE_CONFIG_DIR"] = _ISOLATED
os.environ["SUBAGENT_MODEL_GUARD_MANAGED_POLICY"] = os.path.join(_ISOLATED, "no-managed-policy.json")
os.environ["SUBAGENT_MODEL_GUARD_LOG"] = "off"
os.environ.pop("SUBAGENT_MODEL_GUARD", None)
sys.path.insert(0, HERE)
import subagent_model_guard as g  # noqa: E402

GUARD = os.path.join(HERE, "subagent_model_guard.py")


def spawn(subagent_type="general-purpose", model=None, description="", prompt="", cwd=None):
    ti = {"subagent_type": subagent_type, "description": description, "prompt": prompt}
    if model:
        ti["model"] = model
    return g.decide({"tool_name": "Agent", "tool_input": ti, "cwd": cwd or tempfile.gettempdir()},
                    g.load_policy())


def workflow(script, cwd=None):
    return g.decide({"tool_name": "Workflow", "tool_input": {"script": script},
                     "cwd": cwd or tempfile.gettempdir()}, g.load_policy())


class RoleSpawns(unittest.TestCase):
    def test_build_role_without_model_is_denied_with_the_model_to_pass(self):
        decision, reason, role = spawn(description="SWE TICKET-9", prompt="Act as the SWE")
        self.assertEqual((decision, role), ("deny", "swe"))
        self.assertIn("model: 'sonnet'", reason)

    def test_build_role_on_judge_model_is_denied(self):
        self.assertEqual(spawn(model="opus", description="Test Author TICKET-1")[0], "deny")

    def test_build_role_on_build_model_is_allowed(self):
        self.assertEqual(spawn(model="sonnet", description="Test Author TICKET-1")[0], "allow")

    def test_judge_role_on_build_model_is_denied(self):
        decision, reason, role = spawn(model="sonnet", prompt="Act as the PR Reviewer agent defined in ...")
        self.assertEqual((decision, role), ("deny", "pr-reviewer"))
        self.assertIn("model: 'opus'", reason)

    def test_judge_roles_accept_opus_and_fable(self):
        for model in ("opus", "fable", "claude-opus-5-5"):
            self.assertEqual(spawn(model=model, description="Phase 3 adversarial review")[0], "allow", model)

    def test_tester_is_a_judge(self):
        self.assertEqual(spawn(model="sonnet", description="Tester verifies TICKET-2")[0], "deny")

    def test_role_named_in_bold_after_qualifiers(self):
        _, _, role = spawn(model="opus", prompt="You are the fresh-context **Test Author** for Phase 2")
        self.assertEqual(role, "test-author")

    def test_role_detected_from_output_block_deep_in_prompt(self):
        prompt = "Do the work described below.\n" + "context " * 400 + "\nEnd with the `role: swe` YAML block."
        self.assertEqual(spawn(model="opus", prompt=prompt)[2], "swe")

    def test_role_detected_from_template_reference(self):
        prompt = "Follow the instructions in ../framework/prompts/tester.md for TICKET-4."
        self.assertEqual(spawn(model="sonnet", prompt=prompt)[2], "tester")

    def test_mentioning_a_template_while_editing_it_is_not_role_work(self):
        prompt = ("You are the fork handling the templates. In `lightweight/prompts/ticket_implementer.md` "
                  "make the testing steps explicit, and read prompts/swe.md for the output block format.")
        self.assertIsNone(spawn(subagent_type="fork", description="Update templates", prompt=prompt)[2])

    def test_builtin_read_only_agent_is_never_classified(self):
        prompt = "Read FACILITATOR.md, prompts/swe.md. End with the `role: swe` block."
        self.assertEqual(spawn(subagent_type="Explore", description="Mine repo", prompt=prompt)[0], "allow")

    def test_implement_and_review_descriptions(self):
        self.assertEqual(spawn(description="Implement ticket 8763")[2], "implementer")
        self.assertEqual(spawn(description="Code quality review TQS-1")[2], "reviewer")

    def test_review_findings_is_not_a_review(self):
        self.assertIsNone(spawn(model="sonnet", description="Address review findings TICKET-7")[2])

    def test_role_work_in_a_fork_is_denied(self):
        decision, reason, _ = spawn(subagent_type="fork", description="SWE TICKET-1")
        self.assertEqual(decision, "deny")
        self.assertIn("Forks always inherit", reason)

    def test_unroled_fork_is_allowed(self):
        self.assertEqual(spawn(subagent_type="fork", description="Write templates")[0], "allow")


class UnroledSpawns(unittest.TestCase):
    def test_unroled_without_model_is_denied(self):
        self.assertEqual(spawn(description="Search for usages", prompt="Find callers of foo")[0], "deny")

    def test_unroled_with_model_is_allowed(self):
        self.assertEqual(spawn(model="haiku", description="Search for usages")[0], "allow")

    def test_builtin_pinned_agent_is_allowed_without_model(self):
        self.assertEqual(spawn(subagent_type="Explore", description="Map the repo")[0], "allow")

    def test_plan_agent_is_a_judge(self):
        self.assertEqual(spawn(subagent_type="Plan", description="Plan TQS-1")[0:3:2], ("deny", "planner"))
        self.assertEqual(spawn(subagent_type="Plan", model="opus", description="Plan TQS-1")[0], "allow")


class AgentDefinitions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.agents = os.path.join(self.tmp.name, ".claude", "agents")
        os.makedirs(self.agents)
        self.sub = os.path.join(self.tmp.name, "apps", "api")
        os.makedirs(self.sub)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, model):
        with open(os.path.join(self.agents, name + ".md"), "w") as f:
            f.write("---\nname: %s\ndescription: x\n%s---\nbody\n" % (name, "model: %s\n" % model if model else ""))

    def test_role_file_with_correct_pin_is_allowed_from_a_subdirectory(self):
        self.write("swe", "sonnet")
        self.assertEqual(spawn(subagent_type="swe", description="SWE TICKET-1", cwd=self.sub)[0], "allow")

    def test_role_file_without_pin_is_denied(self):
        self.write("tester", None)
        self.assertEqual(spawn(subagent_type="tester", cwd=self.sub)[0], "deny")

    def test_role_file_with_wrong_pin_is_denied_and_names_the_file(self):
        self.write("pr-reviewer", "sonnet")
        decision, reason, _ = spawn(subagent_type="pr-reviewer", cwd=self.sub)
        self.assertEqual(decision, "deny")
        self.assertIn("pr-reviewer.md", reason)

    def test_explicit_model_overrides_a_wrong_pin(self):
        self.write("pr-reviewer", "sonnet")
        self.assertEqual(spawn(subagent_type="pr-reviewer", model="opus", cwd=self.sub)[0], "allow")

    def test_override_cannot_downgrade_a_correct_pin(self):
        self.write("phase-reviewer", "opus")
        self.assertEqual(spawn(subagent_type="phase-reviewer", model="haiku", cwd=self.sub)[0], "deny")


class PluginAgents(unittest.TestCase):
    def test_reviewer_named_plugin_agents_are_judges(self):
        for name in ("feature-dev:code-reviewer", "pr-review-toolkit:silent-failure-hunter",
                     "pr-review-toolkit:pr-test-analyzer", "acme:pr-qa-validator"):
            self.assertEqual(g.role_from_name(name, g.load_policy()), "reviewer", name)

    def test_reviewer_plugin_agent_on_build_model_is_denied(self):
        self.assertEqual(spawn(subagent_type="feature-dev:code-reviewer", model="sonnet")[0], "deny")

    def test_architect_is_a_judge_and_simplifier_builds(self):
        policy = g.load_policy()
        self.assertEqual(g.role_from_name("feature-dev:code-architect", policy), "planner")
        self.assertEqual(g.role_from_name("code-simplifier:code-simplifier", policy), "implementer")


class Workflows(unittest.TestCase):
    def test_agent_call_without_model_is_denied(self):
        decision, reason, _ = workflow("const r = await agent('summarise the log', {label: 'sum'})")
        self.assertEqual(decision, "deny")
        self.assertIn("line 1", reason)

    def test_agent_calls_with_models_are_allowed(self):
        script = """
        export const meta = {name: 'x', description: 'y'}
        const a = await agent(`Act as the SWE for ${t}`, {label: 'swe', model: 'sonnet'})
        const b = await agent('Find bugs', {label: 'Cold review of diff', model: 'opus', schema: S})
        """
        self.assertEqual(workflow(script)[0], "allow")

    def test_role_on_wrong_tier_is_denied(self):
        script = "await agent('Review it', {label: 'PR Reviewer TICKET-3', model: 'sonnet'})"
        self.assertEqual(workflow(script)[0], "deny")

    def test_role_with_computed_model_is_denied_but_unroled_computed_is_allowed(self):
        self.assertEqual(workflow("await agent(p, {label: 'SWE T-1', model: m})")[0], "deny")
        self.assertEqual(workflow("await agent(p, {label: 'summarise', model: m})")[0], "allow")

    def test_strings_and_comments_do_not_confuse_the_parser(self):
        script = ("// agent('ignored comment')\n"
                  "await agent('has ) and } inside', {label: 'x', model: 'haiku'})\n")
        self.assertEqual(workflow(script)[0], "allow")

    def test_builtin_agent_type_needs_no_model(self):
        self.assertEqual(workflow("await agent('map it', {agentType: 'Explore'})")[0], "allow")

    def test_script_path_is_read(self):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write("await agent('x')\n")
        try:
            result = g.decide({"tool_name": "Workflow", "tool_input": {"scriptPath": f.name}}, g.load_policy())
            self.assertEqual(result[0], "deny")
        finally:
            os.unlink(f.name)


class Audit(unittest.TestCase):
    def audit(self, description, resolved):
        payload = {"hook_event_name": "PostToolUse", "tool_name": "Agent",
                   "tool_input": {"description": description, "model": "sonnet"},
                   "tool_response": {"content": [], "resolvedModel": resolved}}
        return g.audit(payload, g.load_policy())

    def test_matching_resolved_model_is_ok(self):
        self.assertEqual(self.audit("SWE TICKET-1", "claude-sonnet-5-5")[0], "audit-ok")

    def test_mismatch_is_reported(self):
        decision, reason, role, resolved = self.audit("SWE TICKET-1", "claude-fable-5-1")
        self.assertEqual((decision, role, resolved), ("audit-mismatch", "swe", "fable"))
        self.assertIn("unverified", reason)

    def test_missing_resolved_model_is_unknown_not_an_error(self):
        payload = {"hook_event_name": "PostToolUse", "tool_name": "Agent",
                   "tool_input": {"description": "SWE T-1"}, "tool_response": "done"}
        self.assertEqual(g.audit(payload, g.load_policy())[0], "audit-unknown")


class HookProcess(unittest.TestCase):
    """Run the script the way Claude Code does: JSON on stdin, decision JSON on stdout."""

    def run_hook(self, payload, env_extra=None):
        env = dict(os.environ, SUBAGENT_MODEL_GUARD_LOG="off")
        env.pop("SUBAGENT_MODEL_GUARD", None)
        env.update(env_extra or {})
        data = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run([sys.executable, GUARD], input=data, capture_output=True, text=True, env=env)

    def test_deny_is_emitted_as_hook_json(self):
        out = self.run_hook({"tool_name": "Agent", "tool_input": {"description": "SWE T-1"}})
        self.assertEqual(out.returncode, 0)
        self.assertEqual(json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allow_is_silent(self):
        out = self.run_hook({"tool_name": "Agent", "tool_input": {"description": "SWE T-1", "model": "sonnet"}})
        self.assertEqual((out.returncode, out.stdout), (0, ""))

    def test_other_tools_are_ignored(self):
        out = self.run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        self.assertEqual((out.returncode, out.stdout), (0, ""))

    def test_bad_input_fails_open(self):
        out = self.run_hook("not json")
        self.assertEqual((out.returncode, out.stdout), (0, ""))
        self.assertIn("allowing call", out.stderr)

    def test_post_tool_use_mismatch_adds_context(self):
        out = self.run_hook({"hook_event_name": "PostToolUse", "tool_name": "Agent",
                             "tool_input": {"description": "PR Reviewer T-1", "model": "opus"},
                             "tool_response": {"resolvedModel": "claude-sonnet-5-5"}})
        self.assertIn("audit", json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_env_disable_can_be_locked_off_by_a_managed_policy(self):
        with tempfile.TemporaryDirectory() as d:
            managed = os.path.join(d, "subagent_model_policy.json")
            with open(managed, "w") as f:
                json.dump({"allow_env_disable": False}, f)
            out = self.run_hook({"tool_name": "Agent", "tool_input": {"description": "SWE T-1"}},
                                {"SUBAGENT_MODEL_GUARD": "off", "SUBAGENT_MODEL_GUARD_MANAGED_POLICY": managed})
            self.assertIn("deny", out.stdout)

    def test_env_disable(self):
        out = self.run_hook({"tool_name": "Agent", "tool_input": {"description": "SWE T-1"}},
                            {"SUBAGENT_MODEL_GUARD": "off"})
        self.assertEqual(out.stdout, "")


class PolicyLayers(unittest.TestCase):
    def write(self, d, name, data):
        path = os.path.join(d, name)
        with open(path, "w") as f:
            json.dump(data, f)
        return path

    def test_later_layers_override_earlier_ones(self):
        with tempfile.TemporaryDirectory() as d:
            user = self.write(d, "user.json", {"tiers": {"build": ["haiku"]}})
            managed = self.write(d, "managed.json", {"tiers": {"build": ["sonnet"]}, "allow_env_disable": False})
            policy = g.load_policy([os.path.join(HERE, "subagent_model_policy.json"), user, managed])
            self.assertEqual(policy["tiers"]["build"], ["sonnet"])
            self.assertEqual(policy["tiers"]["judge"], ["opus", "fable"])
            self.assertFalse(policy["allow_env_disable"])

    def test_user_policy_applies_without_a_managed_one(self):
        with tempfile.TemporaryDirectory() as d:
            user = self.write(d, "user.json", {"roles": {"tester": "build"}})
            policy = g.load_policy([user, os.path.join(d, "missing.json")])
            self.assertEqual(policy["roles"]["tester"], "build")
            self.assertEqual(policy["roles"]["swe"], "build")

    def test_default_search_order_ends_with_the_managed_file(self):
        paths = g.policy_paths()
        self.assertEqual(paths[0], os.path.join(HERE, "subagent_model_policy.json"))
        self.assertEqual(paths[-1], os.environ["SUBAGENT_MODEL_GUARD_MANAGED_POLICY"])


class PluginPackaging(unittest.TestCase):
    def load(self, *parts):
        with open(os.path.join(*parts)) as f:
            return json.load(f)

    def test_hooks_point_at_this_script(self):
        hooks = self.load(PLUGIN, "hooks", "hooks.json")["hooks"]
        for event, matcher in (("PreToolUse", "Agent|Task|Workflow"), ("PostToolUse", "Agent|Task")):
            entry = hooks[event][0]
            self.assertEqual(entry["matcher"], matcher)
            arg = entry["hooks"][0]["args"][0]
            self.assertTrue(arg.startswith("${CLAUDE_PLUGIN_ROOT}/"))
            self.assertTrue(os.path.isfile(arg.replace("${CLAUDE_PLUGIN_ROOT}", PLUGIN)))

    def test_marketplace_entry_matches_the_manifest(self):
        manifest = self.load(PLUGIN, ".claude-plugin", "plugin.json")
        market = self.load(REPO, ".claude-plugin", "marketplace.json")
        entry = [p for p in market["plugins"] if p["name"] == manifest["name"]][0]
        self.assertEqual(os.path.normpath(os.path.join(REPO, entry["source"])), PLUGIN)

    def test_bundled_policy_is_valid_and_complete(self):
        policy = self.load(HERE, "subagent_model_policy.json")
        for role, tier in policy["roles"].items():
            self.assertIn(tier, policy["tiers"], role)


if __name__ == "__main__":
    unittest.main(verbosity=1)
