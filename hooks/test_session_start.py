#!/usr/bin/env python3
"""Tests for session_start.py. Standard library only: python3 hooks/test_session_start.py"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "session_start.py")


def run(cwd, env_extra=None):
    env = dict(os.environ)
    env.pop("SPEC_DRIVEN_BUILD_KICKOFF", None)
    env.update(env_extra or {})
    payload = json.dumps({"hook_event_name": "SessionStart", "source": "startup", "cwd": cwd})
    out = subprocess.run([sys.executable, HOOK], input=payload, capture_output=True, text=True, env=env)
    assert out.returncode == 0, out.stderr
    return out.stdout


class Kickoff(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "proj")
        os.makedirs(os.path.join(self.root, ".git"))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, text="x"):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)

    def test_empty_repo_offers_the_interview(self):
        self.assertIn("/spec-driven-build:new-project", run(self.root))

    def test_repo_with_only_scaffold_files_is_still_new(self):
        for rel in ("README.md", "LICENSE", ".gitignore", "docs/plans/idea.md", ".claude/settings.json"):
            self.write(rel)
        self.assertIn("new project", run(self.root))

    def test_existing_codebase_is_left_alone(self):
        self.write("src/app.py", "print('hi')")
        self.assertEqual(run(self.root), "")

    def test_existing_codebase_mentions_lightweight_when_asked(self):
        self.write("src/app.py")
        self.assertIn("/spec-driven-build:ticket", run(self.root, {"SPEC_DRIVEN_BUILD_KICKOFF": "always"}))

    def test_framework_project_reports_phase_and_state(self):
        self.write("src/app.py")
        self.write(".facilitator/state.json", json.dumps(
            {"framework_version": "0.4.0", "current_phase": 2, "current_state": "PR_REVIEW"}))
        out = run(os.path.join(self.root, "src"))
        self.assertIn("phase 2", out)
        self.assertIn("PR_REVIEW", out)
        self.assertIn("/spec-driven-build:facilitator", out)

    def test_scaffolded_project_before_first_facilitator_run(self):
        self.write("PROJECT_OVERVIEW.md", "Status: DRAFT")
        self.assertIn("hasn't run", run(self.root))

    def test_corrupt_state_file_does_not_break_the_session(self):
        self.write(".facilitator/state.json", "{not json")
        self.assertIn("framework project", run(self.root))

    def test_disabled(self):
        self.assertEqual(run(self.root, {"SPEC_DRIVEN_BUILD_KICKOFF": "off"}), "")

    def test_home_directory_is_left_alone(self):
        self.assertEqual(run(os.path.expanduser("~"), {"HOME": os.path.expanduser("~")}), "")

    def test_bad_input_is_silent(self):
        out = subprocess.run([sys.executable, HOOK], input="nope", capture_output=True, text=True,
                             cwd=self.root)
        self.assertEqual(out.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
