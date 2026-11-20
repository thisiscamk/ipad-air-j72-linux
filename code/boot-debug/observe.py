#!/usr/bin/env python3
"""Read-only J72 USB/console/flight-recorder observer and classifier."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import signal
import sys
import time
from pathlib import Path

from flightrec import classify, decode_page

IDENTITIES = {
    ("05ac", "1227"): "DFU",
    ("05ac", "4141"): "PONGO",
    ("1209", "316d"): "M1N1_PROXY",
    ("05ac", "4145"): "LINUX_USB",
    ("05ac", "12ab"): "IOS_NORMAL",
}


def usb_snapshot(root: Path = Path("/sys/bus/usb/devices")) -> list[dict]:
    rows = []
    for path in root.iterdir():
        try:
            vid = (path / "idVendor").read_text().strip().lower()
            pid = (path / "idProduct").read_text().strip().lower()
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            continue
        identity = IDENTITIES.get((vid, pid))
        if identity is None:
            continue
        def optional(name: str) -> str | None:
            try:
                return (path / name).read_text(errors="replace").strip()
            except (FileNotFoundError, PermissionError):
                return None
        rows.append({"path": path.name, "vid": vid, "pid": pid,
                     "identity": identity, "devnum": optional("devnum"),
                     "product": optional("product"), "serial": optional("serial")})
    return sorted(rows, key=lambda row: (row["path"], row["identity"]))


def append_jsonl(path: Path, row: dict) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def recorder_events(path: Path, last_sequence: int) -> tuple[list, int, str | None]:
    try:
        header, events = decode_page(path.read_bytes())
    except (FileNotFoundError, PermissionError):
        return [], last_sequence, None
    except ValueError as exc:
        return [], last_sequence, str(exc)
    new = [event for event in events if event.sequence > last_sequence]
    return new, header.write_sequence, None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=float, default=900)
    parser.add_argument("--recorder-file", type=Path,
                        help="read-only 16 KiB recorder image or proxy-updated mirror")
    parser.add_argument("--boot-nonce", help="expected 16-byte nonce in hexadecimal")
    args = parser.parse_args()
    if args.duration <= 0 or args.duration > 3600:
        parser.error("duration must be in (0, 3600]")
    if args.boot_nonce is not None and len(bytes.fromhex(args.boot_nonce)) != 16:
        parser.error("boot nonce must encode 16 bytes")
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    event_path = args.output / "events.jsonl"
    started_wall = datetime.datetime.now().astimezone().isoformat()
    started = time.monotonic()
    manifest = {"schema": "j72-flight-observer-v1", "started_at": started_wall,
                "duration_limit": args.duration, "boot_nonce": args.boot_nonce,
                "recorder_file": str(args.recorder_file) if args.recorder_file else None,
                "read_only": True, "automatic_retry": False,
                "source_media_writes_attempted": False}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    stopped = False
    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    prior_usb = None
    last_sequence = 0
    all_recorder_events = []
    recorder_error = None
    while not stopped and time.monotonic() - started < args.duration:
        now = time.monotonic()
        usb = usb_snapshot()
        if usb != prior_usb:
            append_jsonl(event_path, {"kind": "usb", "host_monotonic": now,
                                      "elapsed": now - started, "devices": usb})
            prior_usb = usb
        if args.recorder_file:
            new, last_sequence, error = recorder_events(args.recorder_file, last_sequence)
            if error and error != recorder_error:
                append_jsonl(event_path, {"kind": "recorder-error",
                                          "host_monotonic": now, "error": error})
                recorder_error = error
            for event in new:
                all_recorder_events.append(event)
                append_jsonl(event_path, {"kind": "recorder",
                                          "host_monotonic": now,
                                          "elapsed": now - started, **event.as_dict()})
        if any(row["identity"] in ("LINUX_USB", "IOS_NORMAL") for row in usb):
            break
        time.sleep(0.05)
    usb_rows = []
    if event_path.exists():
        for line in event_path.read_text().splitlines():
            row = json.loads(line)
            if row.get("kind") == "usb":
                for device in row["devices"]:
                    usb_rows.append(device)
    result = classify(all_recorder_events, usb_rows)
    result.update({"schema": "j72-flight-result-v1",
                   "elapsed": time.monotonic() - started,
                   "last_recorder_sequence": last_sequence,
                   "final_usb": prior_usb or [], "observer_stopped": stopped,
                   "events_sha256": hashlib.sha256(event_path.read_bytes()).hexdigest()
                       if event_path.exists() else None})
    (args.output / "result.json").write_text(json.dumps(result, indent=2,
                                                         sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
