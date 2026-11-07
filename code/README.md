# Source map

**[Current 7.3 installed-system snapshot](current/README.md)** is the entry point:
Orchard/kernel source, Wi-Fi ordering, reusable charging profiles/supervisor and
actual speaker audio source. [Replication guide](../QUICKSTART.md).

## Historical experiments

These preserve earlier lab implementations and synthetic tests. They are not
interchangeable with the current kernel or private firmware containers.

| Directory | Purpose |
| --- | --- |
| [spi](spi/) | Early A7 explicit-PIO transport diagnosis and corrected source |
| [touch](touch/) | Pre-native contact workers, state/recovery research and replay tests |
| [battery](battery/) | Original HDQ gauge implementation and host harness |
| [charging](charging/) | Earlier bounded current/thermal/hold experiments |
| [wifi](wifi/) | HSIC/USB transport, firmware conversion and networking research |
| [storage](storage/) | Recovery, read/write qualification and staged storage research |
| [desktop](desktop/) | Battery/Wi-Fi widgets and experimental keyboard/client changes |
| [upstream](upstream/) | Earlier focused Orchard/Omarchy-A review bundles; read each pinned base |

The [historical source overview](../history/pre-cleanup-2026-11-07/CODE-README.md)
retains the original measured explanations. To run its synthetic suite:

```sh
python3 code/run-offline-tests.py
```

Generated firmware, calibration, credentials and modules remain private. Existing
source notices apply; [license texts](LICENSES/) are retained.
