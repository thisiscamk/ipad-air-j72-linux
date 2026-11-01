# J72 #34 charging with Wi-Fi — guarded development worker

A matching rebuild of the earlier powered-hub worker for the exact #34 kernel,
with one bounded fresh-gauge refresh and read-failure telemetry. No firmware,
board calibration, credentials, compiled modules or private logs are included.

The first unmodified #34 attempt ended after about two seconds with error
-110. The kernel recorded an HDQ flags-read timeout (complete eight-byte
command echo, no response). The original input limit was independently
verified restored; no settled charging samples were retained. That is a
failed charging test, not a charging pass.

The battery core caches a failed flags refresh for five seconds. Simply
repeating property reads can therefore repeat the cached error. This worker
performs at most one explicit `bq27xxx_battery_update()` after EIO/ETIMEDOUT,
then restarts **all five** property reads. Every returned value must pass the
original presence/SOC/temperature/voltage/current guard. There is no fallback
to earlier readings; another error stops charging. The independent deadline
and USB/source-lease checks continue while gauge I/O runs outside the policy
lock. The numerical policy header is unchanged from the prior worker.

Only the previously qualified powered JCH377 charging/data port is allowed.
The host must verify that exact source and renew its 2.5-second lease. The
fixed input setting remains 1050 mA nominal; the kernel maximum remains one
hour, with unchanged battery and charger ceilings. Loading starts unarmed
and performs no input-limit write. This is not autonomous source detection.

```sh
python3 code/charging/wifi34-refresh/test-fresh-gauge.py
```

This compiles the real retry/pack-guard functions and exercises 31 synthetic
success, fresh-vector restart, persistent failure and range-failure cases
under UBSan. It verifies that gauge I/O occurs outside the policy lock.
These tests do not establish physical recovery from a gauge timeout.
The source requires the exact configured development kernel and its existing
HDQ/UART frontend. It is not a portable module or native Orchard integration.
## Measured five-minute result

[The full bounded run](FIVE-MINUTE-RESULT.json) lasted 300.273 seconds and
restored the original input setting independently. Its 140 settled samples
cover 293.559 seconds: time-weighted mean +211.332 mA, range -140 to +394 mA,
with one negative sample. It is net-positive charging under an interactive
workload, not an all-positive idle pass. The owner confirmed menu, keyboard
and charging indication; Wi-Fi-bound HTTPS returned 200 during charging.
Brightness was reduced from 1604 to 1203 when the unchanged 38C test ceiling
was approached. No numerical kernel protection limit was changed.

The successful run had zero gauge failures/refreshes. It therefore qualifies
the workload and restoration, but does not demonstrate physical recovery from
the earlier timeout. The [fifteen-minute continuation](FIFTEEN-MINUTE-RESULT.json) then completed
900.447 seconds with 424 settled samples, all +239..+397 mA, time-weighted
mean +306.965 mA. Brightness stayed at 1203. It ended without a protection
fault and independently restored the original input setting. Gauge failures
and refresh recoveries were zero. Automatic charger/source policy, longer
thermal runs and SOC trends remain open.
