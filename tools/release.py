#!/usr/bin/env python3

"""Test, commit, tag, and push a FETH Skyline Heap Fix release."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from build import ROOT, validate_version


def run(*args: str, capture: bool = False) -> str:
  result = subprocess.run(
    args, cwd=ROOT, check=True, text=True, capture_output=capture
  )
  return result.stdout.strip() if capture else ""


def ensure_clean_main() -> None:
  if Path(run("git", "rev-parse", "--show-toplevel", capture=True)).resolve() != ROOT:
    raise ValueError("Run this script from its own repository")
  if run("git", "branch", "--show-current", capture=True) != "main":
    raise ValueError("Release from main")
  if run("git", "status", "--porcelain", capture=True):
    raise ValueError("Commit working-tree changes before releasing")
  run("git", "fetch", "origin", "main:refs/remotes/origin/main", "--tags")
  if run("git", "rev-parse", "HEAD", capture=True) != run(
    "git", "rev-parse", "origin/main", capture=True
  ):
    raise ValueError("Local main is not synchronized with origin/main")


def bump_version(version: str, part: str) -> str:
  validate_version(version)
  major, minor, patch = (int(value) for value in version.split("."))
  if part == "major":
    return f"{major + 1}.0.0"
  if part == "minor":
    return f"{major}.{minor + 1}.0"
  if part == "patch":
    return f"{major}.{minor}.{patch + 1}"
  raise ValueError(f"Unknown version component: {part}")


def ensure_new_tag(tag: str) -> None:
  result = subprocess.run(
    ("git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"),
    cwd=ROOT, check=False, capture_output=True,
  )
  if result.returncode == 0:
    raise ValueError(f"Tag already exists: {tag}")


def verify_build() -> None:
  run(sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v")
  with tempfile.TemporaryDirectory(prefix="feth-heap-release-") as temporary:
    run(sys.executable, "tools/build.py", "--output", temporary)


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  selection = parser.add_mutually_exclusive_group(required=True)
  selection.add_argument("--current", action="store_true", help="Release VERSION as-is")
  selection.add_argument("--bump", choices=("patch", "minor", "major"))
  parser.add_argument("--yes", action="store_true", help="Skip interactive confirmation")
  args = parser.parse_args()

  ensure_clean_main()
  version_path = ROOT / "VERSION"
  current = validate_version(version_path.read_text(encoding="utf-8").strip())
  version = current if args.current else bump_version(current, args.bump)
  tag = f"v{version}"
  ensure_new_tag(tag)
  print(f"Release {tag}: test, build, commit, tag, and push", flush=True)
  if not args.yes and input("Continue? [y/N] ").strip().lower() not in {"y", "yes"}:
    print("Release cancelled.")
    return

  verify_build()
  if args.current:
    run("git", "commit", "--allow-empty", "-m", f"chore: release {tag}")
  else:
    version_path.write_text(f"{version}\n", encoding="utf-8")
    run("git", "add", "VERSION")
    run("git", "commit", "-m", f"chore: release {tag}")
  run("git", "push", "origin", "main")
  run("git", "tag", "-a", tag, "-m", tag)
  run("git", "push", "origin", tag)
  print(f"Pushed {tag}. CI will generate release notes and publish verified assets.")


if __name__ == "__main__":
  main()
