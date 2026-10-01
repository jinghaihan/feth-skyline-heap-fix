# Development

Requires Python 3.10 or newer and Git. Publishing also requires GitHub CLI
authentication with repository and workflow permissions. Scripts use only
Python's standard library. No game files are needed or distributed.

## Test and build

```sh
python3 -m unittest discover -s tests -v
python3 tools/build.py
python3 tools/build.py --verify-directory dist
```

The build writes the reviewed 23-byte IPS32 patch, separate Atmosphere and
emulator installation ZIPs, and `SHA256SUMS` to `dist/`. Archive timestamps,
permissions, entry order, and storage mode are fixed for reproducible output.
The Atmosphere package contains one `atmosphere/exefs_patches/` entry. The
emulator package contains one `feth-skyline-heap-fix/exefs/` entry. Nothing
else is packaged.

To compare with an existing verified IPS before building:

```sh
python3 tools/build.py --reference-patch /path/to/verified.ips
```

The reference must match byte-for-byte. It is read, never modified. Tests
cover the golden patch, offset and size encoding, single-record scope,
version validation, archive layouts, checksums, reproducibility, corrupted
assets, stale output rejection, and release safety checks.

## Release

Commit and push changes before releasing from a clean `main` synchronized
with `origin/main`. For the first release:

```sh
python3 tools/release.py --current
```

For subsequent releases:

```sh
python3 tools/release.py --bump patch
```

The script runs tests and builds packages, then creates the
`chore: release vX.Y.Z` commit, an annotated version tag, and explicit pushes
of `main` and that tag. Use `--yes` for noninteractive confirmation. Do not
create tags, GitHub releases, or uploads manually.

The tag-triggered workflow validates `VERSION`, tests and rebuilds packages,
generates release notes with changelogithub, uploads the assets, downloads
them again, and verifies their contents and checksums. A green workflow does
not imply additional runtime testing.
