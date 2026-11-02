# #35 bounded input/power observation supervisor

**Prepared and host-tested; device untested.** The original charging module,
watcher, current limits, temperature cutoffs, source qualification and 2.5-second
lease remain unchanged. This wrapper starts that existing watcher in its own
process group and reads input/desktop health over pinned Wi-Fi SSH every 10 seconds.
It does not compete for the serialized USB command channel.

It refuses a changed touch state/session, failed recovery, transfer/layout error,
new input timeout, three stalled frame observations, missing desktop, Wi-Fi loss,
block-backed mount, attached NBD workload or changed brightness/governor.
Healthy recoveries may accumulate over a long continuous session; the new touch
module retains its separate six-per-minute burst bound. Protective charging
holds are recorded without being treated as touch failure.

Initial entry requires an inactive controller and the existing restart limits:
SOC 10..90%, 20..36.5°C and 3.5..4.1V. These are advisory checks; the original kernel
still reads its own fresh vector and applies every source/battery guard. A fully
charged iPad should use the initial Linux time for input/configuration checks,
then enter this observation once eligible. No artificial battery drain is added.

On a health failure, the wrapper interrupts its watcher group so that the
watcher's existing final cleanup runs, then independently checks the disabled
controller and baseline 02 over Wi-Fi. Failed verification remains a failure.
It preserves the last health vector and exports anomaly data only when input
is already stopped; it never bypasses the stable-ring export guard. There is
no automatic fault reset or failed-worker restart.

Twelve host test methods pass, including a real process-group interrupt/finally/
child-reaping test. Shell syntax and pinned local input preflights pass. Actual
Wi-Fi observation, early abort and cleanup on the iPad remain untested.

These are research-workspace references. Restore these files to the
workspace's `tools/` directory to use their private inputs and existing helpers.
Run only the portable host tests here:

```sh
python3 test-j72-observation35.py -v
```

Prepared workspace commands (not run on the device):

```sh
python3 tools/run-j72-observation35.py --preflight
sudo -n python3 tools/run-j72-observation35.py --observe --seconds 5400 --brightness 802
```

The 90-minute measurement uses fixed brightness. No brightness/governor/current
change is made by the wrapper. Analyze the original watcher's fresh current
vectors, including all protective holds, before claiming net gain. This is
Pi-supervised, owner-qualified-hub testing, not autonomous charger qualification.

## Before charging: read-only idle recorder

`record-j72-idle35.py` captures battery/current, temperature, brightness, governor,
input state and ASP presence while all charging workers are absent. Use the
same fixed workload for a five-minute before/after storage-probe comparison.
The exact-boot Wi-Fi transport covers each whole grouped command body. The
recorder has syntax/local-input preflight only; it is device untested. Repeated
gauge cache values and time/temperature drift limit causal interpretation.
There is no current, brightness, governor, storage write or source-lease operation.

```sh
python3 tools/record-j72-idle35.py --preflight
sudo -n python3 tools/record-j72-idle35.py --seconds 300 --asp absent --brightness 802
# Complete the existing guarded native probe/read checks before the next capture.
sudo -n python3 tools/record-j72-idle35.py --seconds 300 --asp present --brightness 802
```
