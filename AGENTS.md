# Repository instructions

- Write all repository content in English, including documentation, comments,
  scripts, commit messages, and release notes.
- Keep this project limited to the reviewed Fire Emblem: Three Houses 1.2.0
  Skyline heap patch. Never distribute game executables, ROMs, saves, or logs.
- The patch changes allocator pool 2 from 3 MiB to 16 MiB. Do not shrink other
  pools or change offsets without new binary evidence and runtime verification.
- Keep documentation honest: Eden startup and simultaneous plugin loading were
  verified; hardware, other emulators, combat, and long-term stability were not.
- Use Python's standard library and two-space indentation.
- Run `python3 -m unittest discover -s tests -v` and `python3 scripts/build.py`
  before committing. Verify the generated IPS against the known reference hash.
- Use Conventional Commits and push completed changes to `origin/main`.
- `VERSION` is the only release version source. Use `python3 scripts/release.py`
  to create the `chore: release vX.Y.Z` commit, annotated tag, and explicit pushes.
  Do not publish releases or upload assets manually.
- Tag pushes trigger CI, which builds packages, runs changelogithub, uploads
  assets, and downloads them again for verification.
