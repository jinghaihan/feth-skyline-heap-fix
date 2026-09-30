# FETH Skyline Heap Fix

Allows multiple Skyline plugins to load together in Fire Emblem: Three Houses
1.2.0 by expanding the shared allocation pool from 3 MiB to 16 MiB.

[![build](https://github.com/jinghaihan/feth-skyline-heap-fix/actions/workflows/build.yml/badge.svg)](https://github.com/jinghaihan/feth-skyline-heap-fix/actions/workflows/build.yml)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Features

- Fixes the observed plugin-loading failure:
  `Failed to read ... (0xffffffff). Skipping.` when the shared pool runs out.
- Changes one pool-size field only; other pools and plugin binaries stay intact.
- Does not modify saves, weapon durability rules, or experience rules.
- Can be removed independently of the plugins that use it.

## Compatibility

- Fire Emblem: Three Houses **1.2.0**.
- Title ID: `010055D009F78000`.
- Main Build ID: `89048449BA238C8CF565518B83BF02D3`.
- Requires an existing game-specific Skyline installation, such as
  [Aldebaran](https://github.com/three-houses-research-team/aldebaran-rs).

> [!WARNING]
> Verified in Eden: startup and simultaneous loading of Bench EXP, Fixed
> Growths, Better Durability, and Aldebaran. Combat behavior, long-term
> stability, other emulators, and real Switch hardware have not been verified.
> The patch reserves an additional 13 MiB. Back up your saves before testing.

The patch is tied to the exact Build ID above. Do not rename it to apply it to
another game version. It does not fix unrelated plugin errors or hook conflicts.

## Install

Download a package from
[Releases](https://github.com/jinghaihan/feth-skyline-heap-fix/releases/latest).
Close the game completely before installing or removing the patch.

### Eden

1. Download `feth-skyline-heap-fix-v<VERSION>-emulator.zip`.
2. Right-click the game and open its mod directory.
3. Extract the ZIP there. The resulting layout must be:

   ```text
   <game mod directory>/
     feth-skyline-heap-fix/
       exefs/
         89048449BA238C8CF565518B83BF02D3.ips
   ```

4. Enable the mod and restart the game. Eden's startup log should report
   `Applying IPS patch from mod "feth-skyline-heap-fix"`.

Do not place the emulator package in the emulated SD card's ExeFS folder.
Other emulators may accept the same layout, but have not been runtime-tested.

### Atmosphere (untested)

Extract `feth-skyline-heap-fix-v<VERSION>-atmosphere.zip` into the SD card root:

```text
sdmc:/atmosphere/exefs_patches/feth-skyline-heap-fix/
  89048449BA238C8CF565518B83BF02D3.ips
```

The archive uses the standard ExeFS patch layout; real hardware compatibility
has not been verified. The Skyline loader and plugins are not included.

### Updating or uninstalling

Disable or remove an older copy of this heap patch before installing it under
the new folder name. Do not keep both copies enabled. To uninstall, disable the
mod or remove its IPS file, then fully restart the game. The original 3 MiB
pool is restored without changing the ROM or saves.

## Development

Python 3.10 or newer is sufficient; no game files or third-party Python
dependencies are needed. See [Development](docs/development.md) for testing
and the scripted release flow, and [Findings](docs/findings.md) for the
binary evidence and verification limits.

## Credits

- [Skyline](https://github.com/skyline-dev/skyline): plugin loading and
  allocation behavior used to investigate the failure.
- [Aldebaran](https://github.com/three-houses-research-team/aldebaran-rs):
  game-specific Skyline tooling used in the verified setup.

No game executable, ROM, save, private log, or third-party source code is
included. Fire Emblem and related names belong to Nintendo and Intelligent
Systems. This unofficial project is not affiliated with or endorsed by them.

## License

[MIT](./LICENSE) License © [jinghaihan](https://github.com/jinghaihan).
This license covers this project's code and documentation, not the game,
Skyline, Aldebaran, or any other third-party material.
