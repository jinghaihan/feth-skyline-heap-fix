# Investigation and verification

## Observed failure

With Bench EXP, Fixed Growths, Better Durability, and Aldebaran installed,
Skyline skipped the durability plugin during file loading:

```text
[PluginManager] Failed to read 'rom:/skyline/plugins/feth-infinite-weapon-durability.nro'. (0xffffffff). Skipping.
```

The historical filename above comes from the tested release. It is not a
filename used by this patch.

Removing Bench EXP allowed the durability plugin to initialize. Keeping all
four plugins and expanding the shared allocation pool also allowed every
plugin to load. The observed failure occurred before plugin entry points ran;
it was not evidence of conflicting combat or experience hooks.

## Allocation path

The supplied 1.2.0 main and SDK binaries were inspected independently of the
runtime logs. The allocation path is:

```text
Skyline PluginManager
  -> memalign(0x1000, NRO file size)
  -> SDK memalign
  -> main aligned_alloc
  -> allocator pool 2
```

Skyline allocates the NRO buffer before reading the file. Its `readFile`
returns `-1` when the destination pointer is null, producing the reported
`0xffffffff` failure. Loaded buffers remain allocated while other plugins
are loaded. NRO buffers, BSS, and additional allocations must fit alongside
other users of the pool; the combined NRO file sizes alone are not its total
usage.

Relevant offsets in the reviewed main binary:

| Field or function | Main virtual offset |
| --- | --- |
| `malloc` | `0x00511D00` |
| `aligned_alloc` | `0x00511E30` |
| Allocator selector | `0x005BB220` |
| Allocator table | `0x01A38F18` |
| Allocator entry stride | `0x98` bytes |
| Pool 2 size field | `0x01A39050` |

Both `malloc` and `aligned_alloc` select pool 2. Its initial size is
`0x00300000`, or 3 MiB. This is a specific allocation pool, not the host
computer's total memory or the game's entire heap.

## Final patch

| Property | Value |
| --- | --- |
| Game version | `1.2.0` |
| Title ID | `010055D009F78000` |
| Main Build ID | `89048449BA238C8CF565518B83BF02D3` |
| Main virtual offset | `0x01A39050` |
| IPS32 record offset | `0x01A39150` |
| Original size | `0x0000000000300000` (3 MiB) |
| Replacement size | `0x0000000001000000` (16 MiB) |
| Additional reserved capacity | 13 MiB |
| Record count | 1 |
| Patch size | 23 bytes |
| SHA-256 | `dc4131bd6f4874d1156342a2c01b030806b0466f6d3e4173c2d617ac2563137a` |

The IPS offset includes the `0x100`-byte NSO header. The single record replaces
this 64-bit little-endian size field:

```text
Original:    00 00 30 00 00 00 00 00
Replacement: 00 00 00 01 00 00 00 00
```

An earlier experiment also reduced pool 1 by 13 MiB to keep the total pool
capacity unchanged. It caused allocation failures and unmapped writes because
the game requests a block close to pool 1's original capacity. That experiment
was reverted. The final patch does not change pool 1 or any other pool.

## Verified results

The supplied final Eden log reports the IPS being applied. The accompanying
Skyline startup capture confirms successful Read, Loaded, Running main, and
Finished running main events for all four plugins. Durability diagnostics
report matching signatures and installed hooks. The final Eden log does not
contain the unmapped accesses observed in the reverted experiment.

These results verify startup and simultaneous plugin initialization only.
They do not establish combat correctness, indefinite stability, real Switch
support, or support for another emulator. The final log still contains an
unimplemented network-protocol diagnostic; this patch does not claim to fix
all emulator warnings or errors.

The original executables, ROM, and saves were not overwritten. Disabling the
IPS and restarting restores the original allocation size. Supplied game
files and personal logs are intentionally excluded from this repository.

## Source references

- [Skyline PluginManager](https://github.com/skyline-dev/skyline/blob/e7522cac7adb0c64b9e4874bc900f8d4575fec33/source/skyline/plugin/PluginManager.cpp)
- [Skyline readFile](https://github.com/skyline-dev/skyline/blob/e7522cac7adb0c64b9e4874bc900f8d4575fec33/source/skyline/utils/cpputils.cpp)
