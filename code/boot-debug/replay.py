#!/usr/bin/env python3
"""Convert bounded historical receipts to classifier regression fixtures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from flightrec import Event, classify


def v151(receipt: dict) -> list[Event]:
    events = [Event(0x0400, 1, 1), Event(0x0410, 2, 2),
              Event(0x0500, 1, 3), Event(0x0540, 2, 4),
              Event(0x0600, 1, 5)]
    if receipt.get("hoolock_kboot_prepare_dt_passed"):
        events.append(Event(0x0610, 2, len(events) + 1))
    if receipt.get("kboot_boot_sent"):
        events.append(Event(0x0620, 2, len(events) + 1))
    return events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--profile", choices=("v151",), required=True)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text())
    events = v151(receipt)
    result = classify(events)
    print(json.dumps({"synthetic_events": [event.as_dict() for event in events],
                      "classification": result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
