# Offline Wi-Fi build-input staging

This helper audits and stages private inputs. It does not start an iPad,
change the Pi kernel, load modules or establish WLAN support. The current
candidate explicitly reports `probe_ready=false`.

Requirements: Python 3, native binutils (`nm`) and kmod (`modinfo`, `depmod`).
All firmware, built modules and generated receipts stay in a private local
directory. Run against the recorded J72 #34 development build and the
continuous-touch build receipt, not an arbitrary same-release kernel.

```sh
python3 code/wifi/prepare-j72-wifi.py \
  --kernel-out /private/wifi-kernel/out \
  --receipt /private/wifi-kernel/build-result.json \
  --touch-module /private/continuous/module34/j72_touch_session.ko \
  --touch-receipt /private/continuous/build-result.json \
  --trx /private/firmware/4324b5/dureza.trx \
  --nvram /private/firmware/4324b5/dureza-u-kk.txt \
  --destination /private/new-wifi-inputs
```

The destination must not exist. A checked module tree, depmod indexes,
unchanged private firmware inputs and `audit.json` are produced. This is
not a boot image; the USB driver still lacks the observed device match
and the J72 HSIC/power/reset integration is unfinished.

Synthetic refusal checks require no kernel, firmware or device:

```sh
python3 -B code/wifi/test-j72-wifi-preparation.py -v
```

The [sanitized result](VALIDATION.json) records build/export/dependency checks,
not hardware qualification. See the [Wi-Fi plan](../../history/plans-and-reports/WIFI-PLAN.md) for
upstream applicability, protocol gaps, first-probe vendor handling and
the remaining steps.
