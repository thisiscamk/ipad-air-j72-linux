# Removing the diagnostic touch timeout

The measured worker intentionally bounds a session to 30 minutes. The user
reported unresponsive touch after that interval; the worker had completed
with firmware health and cleanup intact, zero bad layouts/SPI errors/input
timeouts, and one successful recovery. Restarting it restored touch; the
owner confirmed the menu and brightness again.

`continuous-input.patch` adds an explicit opt-in `continuous=1` parameter.
It overrides the time condition while preserving `stop_requested`, every
controller fault check and full shutdown cleanup. Default behavior remains
bounded. Matching candidates have built against both local #33 and #34
kernels, and actual exported-symbol/ABI checks passed. They are **not yet
boot selected or device qualified**. A synthetic test of the actual loop
condition covers finite expiry, continuous operation past expiry, explicit
stop and jiffies wrap.

The planned fast device qualification loads with `continuous=1` and a
three-second finite fallback, then requires input to remain active at five
seconds before explicitly stopping and verifying health/cleanup. It then
restarts for normal desktop use. No 30-minute wait is needed to detect an
incorrect finite timeout. Packaging and this device check are pending.

For that RAM boot, `../desktop/j72-touch-renew.sh` is a temporary RAM
bridge. It watches for a healthy natural timeout, then starts another
session and reconnects the input device. It refuses explicit stops and
failed/unhealthy sessions, and is bounded to two renewals within 4,000
seconds. Eligibility passed one positive and nine refusal cases; a real
manual stop was respected. Automatic natural-expiry renewal was not observed before the owner
rebooted to iOS for charging. A short interruption remains possible at renewal.
Stop its owned PID and wait for exit before desktop/USB teardown. It never
sets charging current; charging uses its own battery/source guards.

The running boot payload and host kernel are unchanged. The patch carries
the original source's GPL-2.0-only license; owner firmware/calibration remain
private and are not included.
