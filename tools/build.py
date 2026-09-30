#!/usr/bin/env python3

"""Build and verify the reviewed FETH 1.2.0 Skyline heap patch packages."""

from __future__ import annotations

import argparse
import hashlib
import io
import re
import struct
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PROJECT = "feth-skyline-heap-fix"
BUILD_ID = "89048449BA238C8CF565518B83BF02D3"
VIRTUAL_OFFSET = 0x01A39050
NSO_HEADER_SIZE = 0x100
ORIGINAL_HEAP_SIZE = 3 * 1024 * 1024
PATCHED_HEAP_SIZE = 16 * 1024 * 1024
REFERENCE_SHA256 = "dc4131bd6f4874d1156342a2c01b030806b0466f6d3e4173c2d617ac2563137a"
PATCH_NAME = f"{BUILD_ID}.ips"


def validate_version(version: str) -> str:
  if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version):
    raise ValueError(f"Not a stable semantic version: {version}")
  return version


def read_version() -> str:
  return validate_version((ROOT / "VERSION").read_text(encoding="utf-8").strip())


def patch_bytes() -> bytes:
  record = struct.pack(
    ">IH", VIRTUAL_OFFSET + NSO_HEADER_SIZE, struct.calcsize("<Q")
  )
  patch = b"IPS32" + record + struct.pack("<Q", PATCHED_HEAP_SIZE) + b"EEOF"
  if hashlib.sha256(patch).hexdigest() != REFERENCE_SHA256:
    raise ValueError("Generated patch differs from the reviewed reference")
  return patch


def archive_bytes(member: str, data: bytes) -> bytes:
  buffer = io.BytesIO()
  info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
  info.create_system = 3
  info.external_attr = 0o100644 << 16
  with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
    archive.writestr(info, data)
  return buffer.getvalue()


def release_files(version: str) -> dict[str, bytes]:
  validate_version(version)
  patch = patch_bytes()
  files = {
    PATCH_NAME: patch,
    f"{PROJECT}-v{version}-emulator.zip": archive_bytes(
      f"{PROJECT}/exefs/{PATCH_NAME}", patch
    ),
    f"{PROJECT}-v{version}-atmosphere.zip": archive_bytes(
      f"atmosphere/exefs_patches/{PROJECT}/{PATCH_NAME}", patch
    ),
  }
  checksums = "".join(
    f"{hashlib.sha256(data).hexdigest()}  {name}\n"
    for name, data in sorted(files.items())
  )
  files["SHA256SUMS"] = checksums.encode("ascii")
  return files


def verify_directory(directory: Path, version: str) -> None:
  expected = release_files(version)
  actual_names = {path.name for path in directory.iterdir()}
  if actual_names != set(expected):
    raise ValueError("Release directory has missing or unexpected files")
  for name, data in expected.items():
    if (directory / name).read_bytes() != data:
      raise ValueError(f"Release asset differs from the reviewed build: {name}")


def build(directory: Path, version: str) -> None:
  files = release_files(version)
  if directory.exists():
    extra = {path.name for path in directory.iterdir()} - set(files)
    if extra:
      raise ValueError(f"Use an empty output directory; unexpected files: {sorted(extra)}")
  directory.mkdir(parents=True, exist_ok=True)
  for name, data in files.items():
    (directory / name).write_bytes(data)
  verify_directory(directory, version)


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--output", type=Path, default=ROOT / "dist")
  parser.add_argument("--reference-patch", type=Path)
  parser.add_argument("--verify-directory", type=Path)
  args = parser.parse_args()
  version = read_version()
  if args.reference_patch is not None:
    if args.reference_patch.read_bytes() != patch_bytes():
      raise ValueError("Reference patch does not match the reviewed patch")
  if args.verify_directory is not None:
    verify_directory(args.verify_directory, version)
    print(f"Verified release assets in {args.verify_directory}")
  else:
    build(args.output, version)
    print(f"Built and verified {PROJECT} v{version} in {args.output}")


if __name__ == "__main__":
  main()
