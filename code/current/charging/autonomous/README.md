# Autonomous guarded charging on J72

This is the source-only snapshot of the controller physically qualified on the
owner's iPad Air 1 Cellular. It replaces the host-lease supervisor for normal
Omarchy charging on that exact installation. It does not qualify another
charger, hub, battery or device.

The controller changes only PMIC register `0x04c0`: `0x4e` requests the tested
nominal 1,050 mA input limit and `0x02` restores the original handoff value. An
independent 250 ms deadline, one-hour maximum window, fresh BQ27545 readings,
PMIC ceiling checks, external-source state, temperature, state-of-charge,
voltage and pack-current limits remain mandatory.

Cable removal restores `0x02` immediately. The qualified external-power
reporter can return `-ENODATA` while PMIC `0x0062` moves between its attached
and detached signatures; reconnect can also report exact online before other
PMIC fields settle. Both states keep the controller restored and stopped.
Charging resumes only after exact online, valid PMIC invariants, fresh safe
pack data and the 30-second cooldown.

The measured result is in [RESULT.json](RESULT.json). Ten minutes of continuous
charging produced +279 to +423 mA net battery current, raised the gauge from
60% to 63%, and stayed at 35.8–36.1 C. Physical unplug/replug, automatic resume
and explicit stop/restoration passed without controller or restoration faults.
The installed service was enabled and active; its first automatic start after
a later natural Omarchy boot remains to be observed.

Build against the exact running 4 KiB-page kernel tree:

```sh
make -C "$KERNEL" O="$KERNEL_OUT" M="$PWD/code/current/charging/autonomous/module" \
  ARCH=arm64 LLVM=1 W=1 modules
cc -std=c11 -Wall -Wextra -Wno-unused-function \
  -I code/current/charging/autonomous/module \
  -o /tmp/test-autonomous-core code/current/charging/autonomous/test-autonomous-core.c
/tmp/test-autonomous-core
```

Do not publish or install the generated `.ko` from this repository. Build it
for the exact target kernel and repeat source qualification. The startup helper
contains the measured module hash and intentionally refuses a different build.
