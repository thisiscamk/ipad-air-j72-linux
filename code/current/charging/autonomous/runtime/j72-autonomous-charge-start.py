#!/usr/bin/python3
"""Start the sealed J72 charging controller when qualified external power appears."""
from pathlib import Path
import hashlib, os, signal, subprocess, time

RELEASE = "7.3.0-rc1-j72-pw1-orchard-apple-4k"
MODULE = Path("/usr/lib/orchard/j72-modules") / RELEASE / "j72_charge_maintain_auto.ko"
MODULE_SHA256 = "56970240dd103ac86ec3433123e6ec798e6eef64f103eaa97af71ed01ef1ef2d"
EXTERNAL = Path("/sys/class/power_supply/j72-external-power/online")
PARAMS = Path("/sys/module/j72_charge_maintain_auto/parameters")

assert os.geteuid() == 0
assert os.uname().release == RELEASE
assert b"apple,j72\0" in Path("/proc/device-tree/compatible").read_bytes()
assert hashlib.sha256(MODULE.read_bytes()).hexdigest() == MODULE_SHA256
if not PARAMS.exists():
    subprocess.run(["insmod", str(MODULE)], check=True, timeout=20)

status=(PARAMS / "status").read_text()
if "enabled=1\n" not in status:
    if "fault=1\n" in status or "restore_failed=1\n" in status:
        raise RuntimeError(status)
    # Loading is inert. Wait indefinitely for the physically qualified
    # PMIC-backed ONLINE signal; every start still passes all module guards.
    while True:
        if EXTERNAL.exists() and EXTERNAL.read_text().strip() == "1":
            try:
                (PARAMS / "source_lease").write_text("qualified-JCH377-1500mA\n")
                (PARAMS / "arm_hub").write_text("maintain-qualified-JCH377\n")
                (PARAMS / "begin_session").write_text("begin-qualified-maintenance\n")
                break
            except OSError:
                pass
        time.sleep(2)

status=(PARAMS / "status").read_text()
if "enabled=1\n" not in status or "fault=0\n" not in status:
    raise RuntimeError(status)

stopping = False
def stop(_signum, _frame):
    global stopping
    stopping = True
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
while not stopping:
    status=(PARAMS / "status").read_text()
    if "fault=1\n" in status:
        raise RuntimeError(status)
    time.sleep(5)
try:
    (PARAMS / "arm_hub").write_text("stop\n")
finally:
    status=(PARAMS / "status").read_text()
    if "active=0\n" not in status or "restore_failed=0\n" not in status:
        raise RuntimeError(status)
