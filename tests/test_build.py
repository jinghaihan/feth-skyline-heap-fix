from __future__ import annotations

import hashlib
import io
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import build


class PatchTests(unittest.TestCase):
  def test_matches_reviewed_reference(self) -> None:
    expected = bytes.fromhex("495053333201a391500008000000010000000045454f46")
    self.assertEqual(build.patch_bytes(), expected)
    self.assertEqual(len(expected), 23)
    self.assertEqual(hashlib.sha256(expected).hexdigest(), build.REFERENCE_SHA256)

  def test_changes_only_pool_two_size(self) -> None:
    patch = build.patch_bytes()
    offset, length = struct.unpack_from(">IH", patch, 5)
    self.assertEqual(offset, 0x01A39150)
    self.assertEqual(length, 8)
    self.assertEqual(offset - build.NSO_HEADER_SIZE, build.VIRTUAL_OFFSET)
    self.assertEqual(patch[11:19], struct.pack("<Q", 16 * 1024 * 1024))
    self.assertEqual(patch[19:], b"EEOF")
    self.assertEqual(build.ORIGINAL_HEAP_SIZE, 3 * 1024 * 1024)

  def test_supported_identity(self) -> None:
    self.assertEqual(build.BUILD_ID, "89048449BA238C8CF565518B83BF02D3")
    self.assertEqual(build.PATCH_NAME, build.BUILD_ID + ".ips")

  def test_accepts_stable_versions(self) -> None:
    for version in ("0.1.0", "1.0.0", "12.34.56"):
      with self.subTest(version=version):
        self.assertEqual(build.validate_version(version), version)

  def test_rejects_invalid_versions(self) -> None:
    for version in ("v1.2.3", "01.2.3", "1.2", "1.2.3-beta", "1.2.3+build", "../x", ""):
      with self.subTest(version=version):
        with self.assertRaises(ValueError):
          build.validate_version(version)


class PackageTests(unittest.TestCase):
  VERSION = "0.1.0"

  def test_archive_layouts_and_contents(self) -> None:
    files = build.release_files(self.VERSION)
    layouts = {
      "emulator": f"feth-skyline-heap-fix/exefs/{build.PATCH_NAME}",
      "atmosphere": f"atmosphere/exefs_patches/feth-skyline-heap-fix/{build.PATCH_NAME}",
    }
    for kind, member in layouts.items():
      with self.subTest(kind=kind):
        name = f"feth-skyline-heap-fix-v{self.VERSION}-{kind}.zip"
        with zipfile.ZipFile(io.BytesIO(files[name])) as archive:
          self.assertEqual(archive.namelist(), [member])
          self.assertEqual(archive.read(member), build.patch_bytes())
          self.assertIsNone(archive.testzip())

  def test_exact_release_file_set(self) -> None:
    self.assertEqual(set(build.release_files(self.VERSION)), {
      build.PATCH_NAME,
      "feth-skyline-heap-fix-v0.1.0-emulator.zip",
      "feth-skyline-heap-fix-v0.1.0-atmosphere.zip",
      "SHA256SUMS",
    })

  def test_checksum_manifest(self) -> None:
    files = build.release_files(self.VERSION)
    entries = files["SHA256SUMS"].decode("ascii").splitlines()
    self.assertEqual(len(entries), 3)
    for entry in entries:
      digest, name = entry.split("  ")
      self.assertEqual(digest, hashlib.sha256(files[name]).hexdigest())

  def test_reproducible_output(self) -> None:
    self.assertEqual(build.release_files(self.VERSION), build.release_files(self.VERSION))
    for data in build.release_files(self.VERSION).values():
      if data.startswith(b"PK"):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
          info = archive.infolist()[0]
          self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
          self.assertEqual(info.compress_type, zipfile.ZIP_STORED)
          self.assertEqual(info.external_attr >> 16, 0o100644)

  def test_build_and_verify(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary) / "dist"
      build.build(directory, self.VERSION)
      build.verify_directory(directory, self.VERSION)
      build.build(directory, self.VERSION)

  def test_rejects_changed_assets(self) -> None:
    for name in build.release_files(self.VERSION):
      with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        build.build(directory, self.VERSION)
        (directory / name).write_bytes(b"corrupted")
        with self.assertRaises(ValueError):
          build.verify_directory(directory, self.VERSION)

  def test_rejects_missing_asset(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      build.build(directory, self.VERSION)
      (directory / build.PATCH_NAME).unlink()
      with self.assertRaises(ValueError):
        build.verify_directory(directory, self.VERSION)

  def test_rejects_stale_output_without_deleting_it(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      stale = directory / "old-version.zip"
      stale.write_bytes(b"keep this file")
      with self.assertRaises(ValueError):
        build.build(directory, self.VERSION)
      self.assertEqual(stale.read_bytes(), b"keep this file")

  def test_rejects_unexpected_download(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      build.build(directory, self.VERSION)
      (directory / "unexpected.txt").write_bytes(b"extra")
      with self.assertRaises(ValueError):
        build.verify_directory(directory, self.VERSION)

  def test_rejects_wrong_package_version(self) -> None:
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      build.build(directory, self.VERSION)
      with self.assertRaises(ValueError):
        build.verify_directory(directory, "0.1.1")


if __name__ == "__main__":
  unittest.main()
