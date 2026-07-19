#!/usr/bin/env python3
"""
verify_framework.py — verify the spec-driven-build framework repo is correctly
laid out at v0.2.0.

Usage:
    python3 verify_framework.py [--fix] [path/to/framework/repo]

If no path is given, uses the current directory.

Behavior:
    - Reports every file that's missing, present-but-wrong, or extra.
    - Reports specific markers inside files (version strings, structured-output
      sections, the AGENT_ROSTER addendum).
    - With --fix, performs the one safe auto-fix: prepends the AGENT_ROSTER
      addendum if not already present. Backs up the original first.
    - Exits 0 if everything checks out, 1 if anything is wrong.

The script does NOT:
    - Run git commands.
    - Modify SPEC_DRIVEN_BUILD_FRAMEWORK.md.
    - Create files other than backups during --fix.
    - Validate the *content* of structured-output sections beyond confirming
      the section header is present.
"""

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

# -----------------------------------------------------------------------------
# Expected layout
# -----------------------------------------------------------------------------

# Files expected to exist at v0.2.0. Each entry is (path, required_markers).
# required_markers are substrings that must appear somewhere in the file.
# Empty list = existence only.
EXPECTED_FILES = {
    "README.md": [
        "Version:** 0.2.0",
        "FACILITATOR.md",
    ],
    "CHANGELOG.md": [
        "[0.2.0]",
        "Facilitator",
    ],
    "SPEC_DRIVEN_BUILD_FRAMEWORK.md": [],
    "HUMAN_GATES.md": [
        "## The three gates",
    ],
    "LICENSE": [
        "MIT License",
    ],
    "AGENT_ROSTER.md": [
        "A note on the Facilitator",  # from the addendum
    ],
    "FACILITATOR.md": [
        "The Facilitator is the orchestrator role",
        "## State machine",
        "## Structured output",
    ],
    "USING_THE_FRAMEWORK.md": [
        "Facilitator path",
        "Manual path",
    ],
    "templates/CLAUDE.md": [
        "spec-driven-build framework",
        "facilitator_bootstrap.md",
    ],
    "templates/PROJECT_OVERVIEW.md": [
        "PROJECT_OVERVIEW",
        "Hard constraints",
    ],
    "templates/RETRO.md": [
        "Retro Notes",
    ],
    "templates/facilitator_bootstrap.md": [
        "You are the Facilitator",
        "Startup sequence",
    ],
    "prompts/spec_author.md": [
        "## Structured output",
        "role: spec_author",
    ],
    "prompts/pm.md": [
        "## Structured output",
        "role: pm",
    ],
    "prompts/test_author.md": [
        "## Structured output",
        "role: test_author",
    ],
    "prompts/swe.md": [
        "## Structured output",
        "role: swe",
    ],
    "prompts/tester.md": [
        "## Structured output",
        "role: tester",
    ],
    "prompts/pr_reviewer.md": [
        "## Structured output",
        "role: pr_reviewer",
    ],
    "prompts/phase_reviewer.md": [
        "## Structured output",
        "role: phase_reviewer",
    ],
}

# Files that shouldn't be present (delivery vehicles, not final artifacts).
STRAGGLER_FILES = [
    "AGENT_ROSTER_addendum.md",
    "CLAUDE.md",  # at framework repo root — framework is not a project that uses itself
]

# The marker text that, if absent from AGENT_ROSTER.md, indicates the addendum
# hasn't been prepended yet.
ADDENDUM_MARKER = "A note on the Facilitator"

# The addendum content to prepend if --fix is requested. Kept here verbatim so
# the script is self-contained.
ADDENDUM_CONTENT = """## A note on the Facilitator

The seven roles below are the framework's *worker* roles — they produce the artifacts (specs, tickets, tests, code, reports) the framework runs on. As of framework v0.2.0, there is an eighth meta-role, the **Facilitator**, defined in `FACILITATOR.md`.

The Facilitator is not a member of this roster. It does not produce any of the framework's artifacts. Its job is to *orchestrate* the seven worker roles: track project state, prepare invocation prompts, spawn each role as a subagent in fresh context, capture structured outputs, surface human gates, and maintain the audit trail.

In practice this means:

- When you (the human) work on a project, you primarily interact with the Facilitator. The Facilitator interacts with the worker roles.
- The worker roles remain unchanged from earlier framework versions. Their responsibilities, boundaries, and outputs are defined here, not in `FACILITATOR.md`.
- Each worker role's prompt template now includes a **structured output section** (YAML) that the Facilitator parses. The structured output is in addition to, not a replacement for, the prose deliverables.
- A worker role can still be invoked manually (paste the prompt into a fresh Claude Code session) for cases where the Facilitator is unavailable or unhelpful. The structured output section is harmless when read by humans.

The Facilitator does not change *what* the worker roles do. It changes *who keeps track of which one runs when*. Read on for the seven worker roles.

---

"""

# -----------------------------------------------------------------------------
# Result accumulator
# -----------------------------------------------------------------------------

@dataclass
class Results:
    missing: list[str] = field(default_factory=list)
    marker_failures: list[tuple[str, str]] = field(default_factory=list)  # (path, marker)
    stragglers: list[str] = field(default_factory=list)
    fixed: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.missing or self.marker_failures or self.stragglers)

# -----------------------------------------------------------------------------
# Checks
# -----------------------------------------------------------------------------

def check_files(root: Path, results: Results) -> None:
    """Check that each expected file exists and contains its required markers."""
    for rel_path, markers in EXPECTED_FILES.items():
        path = root / rel_path
        if not path.exists():
            results.missing.append(rel_path)
            continue
        if not markers:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            results.marker_failures.append((rel_path, f"<could not read: {e}>"))
            continue
        for marker in markers:
            if marker not in content:
                results.marker_failures.append((rel_path, marker))

def check_stragglers(root: Path, results: Results) -> None:
    """Check for files that shouldn't be in the framework repo."""
    for rel_path in STRAGGLER_FILES:
        if (root / rel_path).exists():
            results.stragglers.append(rel_path)

def maybe_fix_addendum(root: Path, results: Results, fix: bool) -> None:
    """If AGENT_ROSTER.md is missing the addendum and --fix is on, prepend it."""
    roster = root / "AGENT_ROSTER.md"
    if not roster.exists():
        # Already reported as missing.
        return
    content = roster.read_text(encoding="utf-8")
    if ADDENDUM_MARKER in content:
        return  # Already has it.
    if not fix:
        # Reported via the marker check; nothing more to do here.
        return
    # Back up and prepend.
    backup = root / "AGENT_ROSTER.md.bak"
    if backup.exists():
        results.notes.append(
            f"AGENT_ROSTER.md.bak already exists; not overwriting. "
            f"Move it aside and re-run --fix if you want to re-fix."
        )
        return
    shutil.copy2(roster, backup)
    roster.write_text(ADDENDUM_CONTENT + content, encoding="utf-8")
    results.fixed.append(
        "AGENT_ROSTER.md: prepended addendum (backup at AGENT_ROSTER.md.bak)"
    )

# -----------------------------------------------------------------------------
# Reporting
# -----------------------------------------------------------------------------

def report(results: Results) -> None:
    """Print a human-readable report."""
    print()
    if results.ok and not results.fixed:
        print("Framework repo is at v0.2.0 and complete. Ready to commit and tag.")
        print()
        print("Suggested next steps:")
        print("  git add -A")
        print("  git commit -m '0.2.0: Facilitator + structured outputs'")
        print("  git tag v0.2.0")
        return

    if results.missing:
        print(f"Missing files ({len(results.missing)}):")
        for p in results.missing:
            print(f"  - {p}")
        print()

    if results.marker_failures:
        print(f"Files present but missing required content ({len(results.marker_failures)}):")
        for path, marker in results.marker_failures:
            print(f"  - {path}")
            print(f"      missing marker: {marker!r}")
        print()

    if results.stragglers:
        print(f"Stragglers — files that should not be present ({len(results.stragglers)}):")
        for p in results.stragglers:
            print(f"  - {p}")
            if p == "AGENT_ROSTER_addendum.md":
                print("      (the addendum content should be prepended to AGENT_ROSTER.md, "
                      "then this delivery file deleted)")
            elif p == "CLAUDE.md":
                print("      (the framework repo does not use the framework on itself; "
                      "templates/CLAUDE.md is the per-project template)")
        print()

    if results.fixed:
        print(f"Auto-fixed ({len(results.fixed)}):")
        for f in results.fixed:
            print(f"  - {f}")
        print()

    if results.notes:
        print("Notes:")
        for n in results.notes:
            print(f"  - {n}")
        print()

    if not results.ok:
        print("Verification failed. Address the issues above and re-run.")
        if (results.marker_failures
                and any("A note on the Facilitator" in m
                        for _, m in results.marker_failures)):
            print()
            print("Tip: re-run with --fix to prepend the AGENT_ROSTER.md addendum "
                  "automatically.")

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify spec-driven-build framework repo layout at v0.2.0."
    )
    parser.add_argument(
        "path", nargs="?", default=".",
        help="Path to the framework repo (default: current directory)"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Auto-fix the AGENT_ROSTER addendum if missing (backs up first)"
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    print(f"Verifying framework repo at: {root}")

    results = Results()
    check_files(root, results)
    check_stragglers(root, results)
    maybe_fix_addendum(root, results, args.fix)

    # Re-check after fix, so the final report reflects the fixed state.
    if args.fix and results.fixed:
        results.missing.clear()
        results.marker_failures.clear()
        results.stragglers.clear()
        check_files(root, results)
        check_stragglers(root, results)

    report(results)
    return 0 if results.ok else 1

if __name__ == "__main__":
    sys.exit(main())
