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
kernels, and exported-symbol/build-provenance checks passed. The #33 candidate
has now booted and passed the short lifetime/cleanup check below; #34 remains
unbooted. Long uninterrupted use is not yet qualified. A synthetic test of the actual loop
condition covers finite expiry, continuous operation past expiry, explicit
stop and jiffies wrap.

The fresh #33 RAM boot loaded with `continuous=1` and a three-second finite
fallback. Input remained active at five seconds, explicit stop returned to
state 0 with firmware health and cleanup passing, and automatic restart
entered session 2. The desktop started with 1,566 frames observed, zero bad
layouts, input timeouts or SPI transfer errors at that snapshot. Owner visual
confirmation is pending. This demonstrates timeout bypass and clean restart;
it does not establish long-session reliability.

For the previous RAM boot, `../desktop/j72-touch-renew.sh` was a temporary RAM
bridge. It watches for a healthy natural timeout, then starts another
session and reconnects the input device. It refuses explicit stops and
failed/unhealthy sessions, and is bounded to two renewals within 4,000
seconds. Eligibility passed one positive and nine refusal cases; a real
manual stop was respected. Automatic natural-expiry renewal was not observed before the owner
rebooted to iOS for charging. A short interruption remains possible at renewal.
Stop its owned PID and wait for exit before desktop/USB teardown. It never
sets charging current; charging uses its own battery/source guards.

The new boot changes the private startup overlay while retaining the #33
kernel, DT and loader. It packages the battery widget and starts at no more
than 802/2047 brightness. No renewal bridge is needed in this boot. The patch carries
the original source's GPL-2.0-only license; owner firmware/calibration remain
private and are not included.
