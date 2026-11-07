Reusable J72 charging profiles
=============================

These tools separate a shared J72 hardware policy from installation identity,
USB topology, authentication and measured source qualification. They do not
copy another owner's qualification or automatically trust a charger rating.
No private firmware, keys, passwords, raw device captures or owner ECID is in
this directory. Changes are local preparation, not an upstream submission.

Scope
  Current driver policy is J72/A7 only, 1050mA input override and the exact
  kernel/module/supervisor builds pinned in hardware.json. It preserves the
  tested one-hour windows, source lease, pack limits and thermal hysteresis.
  The JSON limits section documents compiled policy; editing it cannot change
  limits. A different build requires new pins and evidence.

  Other externally powered USB data hubs can use the configuration format,
  but each installation/source needs its own measured qualification. A hub's
  adapter total rating is not its per-port capability. The current controller
  uses historical JCH377-named wire tokens; those are not source detection.
  Arbitrary wall chargers, unpowered hubs, direct-host charging and other iPad
  models are not enabled by this framework.

Prepare an installation (this DOES NOT start or qualify charging)
  python3 tools/j72-charge-profile.py init /path/to/new-private-profile \
    --ecid YOUR_16_HEX_DIGIT_ECID --hub-model YOUR_HUB_MODEL \
    --port YOUR_USB_DEVICE_ROUTE --hub-port YOUR_USB_HUB_ROUTE \
    --root-device /dev/disk/by-partuuid/YOUR_LINUX_ROOT_PARTUUID \
    --boot-device /dev/disk/by-partuuid/YOUR_BOOT_PARTUUID

The new directory contains hardware.json, installation.json and a PENDING
qualification.json. Init refuses to overwrite an existing directory. Fill
the actual USB hub descriptors and measured source values. No template is
accepted as qualified: every check starts failed, duration zero, evidence
absent and hashes unset.

Qualification
  Perform and preserve all 13 checks listed by j72_charge_profile.CHECKS:
  source capability, unplug restoration, freeze/kill restoration, invalid
  admissions, host independence, fresh-boot default-off, gauge pairing, window
  restoration/restart, two-hour soak, continuous mode, inhibitor and health.
  The existing j72-charge-supervisor and evidence tools provide the runtime
  tests and measurements. Init/verify cannot manufacture those measurements.

  Each check references its own real evidence file and SHA256. Record actual
  net-positive measurements and at least7200s bounded /2700s continuous
  observation. Failures and protective holds must remain visible. Update the
  installation identity hash after recording source details, using
  j72_charge_profile.installation_identity(). The record's hardware hash must
  match. Set QUALIFIED only after the measurements pass; finally record the
  qualification file SHA256 in installation.json.

  python3 tools/j72-charge-profile.py verify /path/to/profile/installation.json

Verification refuses changed evidence, another ECID/source/port/root/boot,
insufficient current rating, failed checks, incomplete duration, non-positive
net charge, faults, restoration errors or changed hardware pins. Evidence is
a local administrator's attestation backed by recorded measurements; file
hashes are integrity checks, not proof that hardware tests were performed.

Generate the host configuration only after verification
  python3 tools/j72-charge-profile.py host-config /path/to/profile/installation.json \
    --ssh-key /private/path/to/key --known-hosts /private/path/to/known_hosts \
    --password-file /private/path/to/sudo-password --output /private/path/to/config.json

Copy tools/j72-charge-auto-target.py to /usr/lib/orchard/j72_charge_auto.py
and tools/j72_charge_profile.py alongside it on the tablet. Install the private
profile/evidence directory at /etc/orchard/j72-charge, owned by root and not
writable by other users. Target admission uses --profile and repeats evidence
and build verification. Root and boot partition identities are per installation.

Run tools/j72-charge-auto-host.py on the Linux host using generated config.
The two .service files are reusable host/tablet units. The tablet unit is
started by qualified admission, not blindly enabled at boot. The host unit can
be enabled after root-private provisioning and hardware qualification. The
existing qualified J72 kernel, gauge, controller, external-power service and
their dependencies must already be installed; this bundle is not a kernel or
firmware installer. Verify each file/hash rather than downloading arbitrary
prebuilt modules into an unrelated kernel.
It verifies exact owner USB boot identity, physical qualified route and live
hub GET_STATUS power/overcurrent before pinned USB SSH admission. Existing
SSH provisioning and root-only systemd/credential setup are prerequisites;
no keys, passwords or device access are created by this tool. Keep the host
configuration private. An optional wifi_ssh_argv supports stale-gadget recovery
only while charging is stopped/restored; it never grants charging over Wi-Fi.

The existing owner session uses the previously hardware-tested compatibility
path. New profile-driven code is host-tested preparation; it has NOT been
deployed over the owner's working charger or qualified by a fresh boot.
Do not treat those two evidence sets as interchangeable.
