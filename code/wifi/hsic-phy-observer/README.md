# J72 HSIC read-only diagnostic

Measured on the exact J72 #33 RAM kernel. The source temporarily attaches a
consumer to the existing HSIC1 power-domain provider, resumes it through
Linux genpd, reads two known PHY offsets and four known clock configuration
words, then suspends/removes the consumer. [Measured result](VALIDATION.json).

The first diagnostic rejected actual state 4 and restored all resources.
The revised source recognizes auto clock gating only with requested state F,
AUTO enabled, and actual state 4; power-gated and target-off states are refused.
No direct power-gate, PHY, reset, GPIO or PMIC write, EHCI registration, DMA or
radio firmware upload is performed. Domain transitions are made by the existing
kernel owner. Unknown PHY offsets are not swept. Failed suspend/detach retains
the consumer for investigation. The module stays resident until reboot.

Run the portable host simulation with `python3 test-observer.py`. It compiles
the actual C initializer against fault-injected kernel API stubs and UBSan.
It tests 16 paths and charging-state refusals; it does not emulate the PHY.

The Python hardware runner is a **workspace harness**, requiring the matching
private image receipts and existing J72 RAM-shell helpers. Its original
location is `tools/run-j72-hsic-phy-observer-v2.py`; it is not a standalone
installer. It requires the charge trial restored, input healthy/stopped, root
unmounted, NBD detached and host export stopped. Source build and exact image
pins are checked before loading. No firmware or private receipts are included.

Next: bounded native PHY transition and exact baseline restoration, then
reset/ready/host enumeration. No Wi-Fi scan or association is claimed here.
