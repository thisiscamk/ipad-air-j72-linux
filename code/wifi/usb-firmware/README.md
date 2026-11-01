# Private J72 USB firmware preparation — offline candidate

This helper packages owner-supplied TRX firmware, matching board NVRAM and a
six-byte owner MAC for the measured BCM43241 revision 6 USB/HSIC radio.
It performs no device access and includes no firmware, board data or owner MAC.
The layout follows [Project Cascadia's TRX/NVRAM work](https://github.com/rzxvx/Project-Cascadia/blob/c20b85ebb951c704d7e3a664c378dde8276e3928/scripts/trx-add-nvram.py).

The helper validates the original CRC and offsets, requires unused trailing
bytes to be zero padding, appends aligned NUL-separated NVRAM and its length
token, and updates TRX length/CRC. It requires the owner's real unicast MAC;
there is no default address or fallback board profile. Duplicate NVRAM keys,
foreign embedded MACs, malformed text and oversized images are refused.

`python3 test-packer.py` passes 18 synthetic acceptance/refusal cases. The
owner-local J72 inputs also produced a CRC-checked image within the observed
576 KiB ROM RAM bound; its MAC agreed in two private device records. No radio
firmware has yet been uploaded with this candidate. Startup, radio calibration
behavior and network operation require physical testing.

The current USB driver/provider candidate builds against the exact development
kernel and passes separate synthetic transport/lifecycle tests. Its first
firmware test is pending; this helper alone does not enable Wi-Fi. Keep inputs
and generated firmware private. See [the current Wi-Fi plan](../../../WIFI-PLAN.md).
