# Measured five-minute desktop charging

The fixed 1,050 mA powered-JCH377 session completed 300.002214 seconds while
the RAM desktop and USB data remained live. All 140 retained worker readings
were positive, +178 to +216 mA, versus a -849 mA baseline. Original input
setting `04c0=02` was restored with no errors or failed guards. Maximum
recorded temperature was 37.8 C. See `VALIDATION.json`.

The owner confirmed the top-bar battery widget and its charging symbol.
The original display brightness was 1604/2047 during this qualification.
A separate, dimmer, longer continuation is being evaluated; this result
does not qualify that duration or autonomous source detection.

This is the exact measured experimental worker, not an installer or an
automatic charger policy. It requires the private exact-kernel build and
a host that verifies the powered hub and renews a 2.5-second lease. Only
PMIC register 04c0 may change; load/arm do not change its value. Home starts
one bounded session. Battery, USB and restoration guards remain active.
Do not use on a different model or unqualified power source.

Source is GPL-2.0-only. Run the companion code offline test runner for the
actual policy, fault-boundary and USB lifetime tests. No firmware, identifying
logs or compiled modules are included.
