# Remaining work

Updated 7 November 2026. [Current support matrix](J72-PROGRESS.md).

1. **Power reliability:** diagnose the supervisor timing/read failure under load;
   add fresh battery monitoring and low-battery fallback; compare actual iOS and
   Linux source/current policy on the same cable/hub. Requalify continuous use
   before recommending unattended charging. Do not simply raise current limits.
2. **Audio startup:** verify the enabled service on a fresh boot, then audible
   app playback. Resolve overlay teardown references and package J72-only changes.
3. **Usable applications:** address the 1 GB RAM/software-rendering constraints;
   qualify actual browser video and sound without destabilising power/input.
4. **Reproducible release:** clean-checkout Orchard/Omarchy-A build and deployment,
   private-input provisioning and exact installed service integration. The public
   source snapshots are available; a turnkey release remains unqualified.
5. **Startup independence:** fix the direct installed-loader handoff, then research
   a distinct on-device iOS handoff. Neither is implied by successful internal-root boot.
6. **Other hardware:** headphones/microphone, Bluetooth, suspend/resume, sensors,
   cameras and cellular each need separate qualification.
7. **Upstream review:** discuss exact J72-only diffs with the owner before submitting
   or updating any Orchard/Omarchy-A PR. Default to their unchanged components.

Internal installation is already demonstrated on this device. For a new device,
RAM qualification, disk measurements and an approved installation plan are still
required. Do not treat historical DFU counts as a schedule or promise.
