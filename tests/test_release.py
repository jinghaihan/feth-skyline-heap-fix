from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import release


class ReleaseTests(unittest.TestCase):
  def setUp(self) -> None:
    printer = patch("builtins.print")
    printer.start()
    self.addCleanup(printer.stop)

  def test_semantic_version_bumps(self) -> None:
    self.assertEqual(release.bump_version("1.2.3", "patch"), "1.2.4")
    self.assertEqual(release.bump_version("1.2.3", "minor"), "1.3.0")
    self.assertEqual(release.bump_version("1.2.3", "major"), "2.0.0")
    with self.assertRaises(ValueError):
      release.bump_version("1.2.3", "unknown")

  def test_rejects_wrong_repository(self) -> None:
    with patch.object(release, "run", return_value="/different/repository"):
      with self.assertRaisesRegex(ValueError, "own repository"):
        release.ensure_clean_main()

  def test_rejects_wrong_branch(self) -> None:
    with patch.object(release, "run", side_effect=[str(release.ROOT), "feature"]):
      with self.assertRaisesRegex(ValueError, "main"):
        release.ensure_clean_main()

  def test_rejects_dirty_worktree(self) -> None:
    with patch.object(release, "run", side_effect=[str(release.ROOT), "main", " M README.md"]):
      with self.assertRaisesRegex(ValueError, "working-tree"):
        release.ensure_clean_main()

  def test_rejects_unsynchronized_main(self) -> None:
    outputs = [str(release.ROOT), "main", "", "", "local", "remote"]
    with patch.object(release, "run", side_effect=outputs):
      with self.assertRaisesRegex(ValueError, "synchronized"):
        release.ensure_clean_main()

  def test_fetches_explicit_tracking_ref(self) -> None:
    outputs = [str(release.ROOT), "main", "", "", "same", "same"]
    with patch.object(release, "run", side_effect=outputs) as run:
      release.ensure_clean_main()
      self.assertIn(
        call("git", "fetch", "origin", "main:refs/remotes/origin/main", "--tags"),
        run.call_args_list,
      )

  def test_rejects_existing_tag(self) -> None:
    result = subprocess.CompletedProcess([], 0)
    with patch.object(release.subprocess, "run", return_value=result):
      with self.assertRaisesRegex(ValueError, "already exists"):
        release.ensure_new_tag("v0.1.0")

  def test_current_release_uses_scripted_commit_tag_and_push(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      (directory / "VERSION").write_text("0.1.0\n", encoding="utf-8")
      with (
        patch.object(release, "ROOT", directory),
        patch.object(release, "ensure_clean_main"),
        patch.object(release, "ensure_new_tag"),
        patch.object(release, "verify_build") as verify,
        patch.object(release, "run") as run,
        patch.object(sys, "argv", ["release.py", "--current", "--yes"]),
      ):
        release.main()
        verify.assert_called_once_with()
        self.assertEqual(run.call_args_list, [
          call("git", "commit", "--allow-empty", "-m", "chore: release v0.1.0"),
          call("git", "push", "origin", "main"),
          call("git", "tag", "-a", "v0.1.0", "-m", "v0.1.0"),
          call("git", "push", "origin", "v0.1.0"),
        ])
        self.assertEqual((directory / "VERSION").read_text(encoding="utf-8"), "0.1.0\n")

  def test_failed_checks_do_not_change_version_or_push(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      (directory / "VERSION").write_text("0.1.0\n", encoding="utf-8")
      with (
        patch.object(release, "ROOT", directory),
        patch.object(release, "ensure_clean_main"),
        patch.object(release, "ensure_new_tag"),
        patch.object(release, "verify_build", side_effect=ValueError("Failed tests")),
        patch.object(release, "run") as run,
        patch.object(sys, "argv", ["release.py", "--bump", "patch", "--yes"]),
      ):
        with self.assertRaisesRegex(ValueError, "Failed tests"):
          release.main()
        run.assert_not_called()
        self.assertEqual((directory / "VERSION").read_text(encoding="utf-8"), "0.1.0\n")

  def test_patch_release_updates_only_version(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      (directory / "VERSION").write_text("0.1.0\n", encoding="utf-8")
      with (
        patch.object(release, "ROOT", directory),
        patch.object(release, "ensure_clean_main"),
        patch.object(release, "ensure_new_tag"),
        patch.object(release, "verify_build"),
        patch.object(release, "run") as run,
        patch.object(sys, "argv", ["release.py", "--bump", "patch", "--yes"]),
      ):
        release.main()
        self.assertEqual((directory / "VERSION").read_text(encoding="utf-8"), "0.1.1\n")
        self.assertEqual(run.call_args_list, [
          call("git", "add", "VERSION"),
          call("git", "commit", "-m", "chore: release v0.1.1"),
          call("git", "push", "origin", "main"),
          call("git", "tag", "-a", "v0.1.1", "-m", "v0.1.1"),
          call("git", "push", "origin", "v0.1.1"),
        ])

  def test_cancelled_release_does_not_run_checks_or_push(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      (directory / "VERSION").write_text("0.1.0\n", encoding="utf-8")
      with (
        patch.object(release, "ROOT", directory),
        patch.object(release, "ensure_clean_main"),
        patch.object(release, "ensure_new_tag"),
        patch.object(release, "verify_build") as verify,
        patch.object(release, "run") as run,
        patch("builtins.input", return_value="no"),
        patch.object(sys, "argv", ["release.py", "--current"]),
      ):
        release.main()
        verify.assert_not_called()
        run.assert_not_called()


if __name__ == "__main__":
  unittest.main()
