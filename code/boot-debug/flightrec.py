#!/usr/bin/env python3
"""J72 boot flight-recorder binary format and classifier."""
from __future__ import annotations

import dataclasses
import json
import struct
from pathlib import Path
from typing import Iterable

PAGE_SIZE = 16 * 1024
HEADER_SIZE = 256
EVENT_SIZE = 64
EVENT_CAPACITY = (PAGE_SIZE - HEADER_SIZE) // EVENT_SIZE
HEADER_MAGIC = b"J72FLR1\0"
EVENT_MAGIC = b"J72EVT1\0"
VERSION = 1

HEADER_PREFIX = struct.Struct("<8sHHHHII16s16s32s32s")
EVENT_STRUCT = struct.Struct("<8sHHIIIQQQQII")

STAGES = {
    0x0100: "IOS_LAUNCHER_ENTER",
    0x0110: "IOS_LAYOUT_VERIFIED",
    0x0120: "IOS_HOOK_COMMITTED",
    0x0130: "IOS_SLEEP_REQUESTED",
    0x0140: "IOS_SLEEP_RETURNED",
    0x0200: "WAKE_BRIDGE_ENTER",
    0x0210: "WAKE_CPU0_ACCEPTED",
    0x0220: "WAKE_SECONDARY_PARKED",
    0x0300: "GATHER_ENTER",
    0x0310: "GATHER_VALIDATED",
    0x0320: "GATHER_PUBLISHED",
    0x0400: "M1N1_ENTER",
    0x0410: "M1N1_ADT_ACCEPTED",
    0x0420: "M1N1_HEAP_READY",
    0x0500: "HOOLOCK_ENTER",
    0x0510: "ANS_READY",
    0x0520: "STORAGE_READY",
    0x0530: "BLS_SELECTED",
    0x0540: "PAYLOAD_LOADED",
    0x0600: "KBOOT_ENTER",
    0x0610: "KBOOT_DT_PREPARED",
    0x0618: "KBOOT_PAYLOAD_READY",
    0x0620: "KBOOT_BRANCH",
    0x0700: "LINUX_ENTRY",
    0x0710: "LINUX_MMU_ON",
    0x0720: "LINUX_EARLY_INIT",
    0x0800: "INITRAMFS_INIT",
    0x0810: "INITRAMFS_STORAGE_VISIBLE",
    0x0820: "ROOT_MOUNTED",
    0x0830: "SWITCH_ROOT",
    0x0900: "USERSPACE_ENTER",
    0x0910: "LINUX_USB_READY",
    0x0920: "BOOT_COMPLETE",
}

EXPECTED_ORDER = tuple(STAGES)


def crc32c(data: bytes, crc: int = 0) -> int:
    """Castagnoli CRC32, intentionally dependency-free for early tooling."""
    crc ^= 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82F63B78 if crc & 1 else 0)
    return crc ^ 0xFFFFFFFF


@dataclasses.dataclass(frozen=True)
class Header:
    write_sequence: int
    flags: int
    boot_nonce: bytes
    target: str
    payload_sha256: bytes
    config_sha256: bytes


@dataclasses.dataclass(frozen=True)
class Event:
    stage: int
    event: int
    sequence: int
    flags: int = 0
    error: int = 0
    counter: int = 0
    current_el: int = 0
    mpidr: int = 0
    arg0: int = 0

    @property
    def stage_name(self) -> str:
        return STAGES.get(self.stage, f"UNKNOWN_0x{self.stage:04x}")

    def as_dict(self) -> dict:
        result = dataclasses.asdict(self)
        result["stage_name"] = self.stage_name
        return result


def new_page(*, boot_nonce: bytes, target: str, payload_sha256: bytes,
             config_sha256: bytes, events: Iterable[Event] = ()) -> bytes:
    if len(boot_nonce) != 16 or len(payload_sha256) != 32 or len(config_sha256) != 32:
        raise ValueError("nonce and digest sizes differ")
    target_bytes = target.encode("ascii")
    if len(target_bytes) > 15:
        raise ValueError("target is too long")
    page = bytearray(PAGE_SIZE)
    event_list = list(events)
    if len(event_list) > EVENT_CAPACITY:
        raise ValueError("too many events")
    HEADER_PREFIX.pack_into(page, 0, HEADER_MAGIC, VERSION, HEADER_SIZE,
                            EVENT_SIZE, EVENT_CAPACITY, len(event_list), 0,
                            boot_nonce, target_bytes.ljust(16, b"\0"),
                            payload_sha256, config_sha256)
    for slot, event in enumerate(event_list):
        page[HEADER_SIZE + slot * EVENT_SIZE:HEADER_SIZE + (slot + 1) * EVENT_SIZE] = encode_event(event)
    return bytes(page)


def encode_event(event: Event) -> bytes:
    raw = bytearray(EVENT_SIZE)
    EVENT_STRUCT.pack_into(raw, 0, EVENT_MAGIC, event.stage, event.event,
                           event.sequence, event.flags, event.error,
                           event.counter, event.current_el, event.mpidr,
                           event.arg0, 0, 0)
    struct.pack_into("<I", raw, 56, crc32c(raw[:56] + raw[60:]))
    return bytes(raw)


def decode_page(data: bytes) -> tuple[Header, list[Event]]:
    if len(data) != PAGE_SIZE:
        raise ValueError(f"recorder must be exactly {PAGE_SIZE} bytes")
    fields = HEADER_PREFIX.unpack_from(data)
    magic, version, header_size, event_size, capacity, write_sequence, flags = fields[:7]
    if magic != HEADER_MAGIC or version != VERSION:
        raise ValueError("header identity differs")
    if (header_size, event_size, capacity) != (HEADER_SIZE, EVENT_SIZE, EVENT_CAPACITY):
        raise ValueError("header geometry differs")
    if write_sequence > capacity:
        raise ValueError("write sequence exceeds capacity")
    header = Header(write_sequence, flags, fields[7],
                    fields[8].split(b"\0", 1)[0].decode("ascii"), fields[9], fields[10])
    events = []
    for slot in range(write_sequence):
        raw = data[HEADER_SIZE + slot * EVENT_SIZE:HEADER_SIZE + (slot + 1) * EVENT_SIZE]
        values = EVENT_STRUCT.unpack(raw)
        if values[0] != EVENT_MAGIC:
            raise ValueError(f"event {slot} magic differs")
        stored_crc = values[-2]
        if stored_crc != crc32c(raw[:56] + raw[60:]):
            raise ValueError(f"event {slot} CRC differs")
        event = Event(values[1], values[2], values[3], values[4], values[5],
                      values[6], values[7], values[8], values[9])
        if event.sequence != slot + 1:
            raise ValueError(f"event {slot} sequence differs")
        events.append(event)
    return header, events


def classify(events: Iterable[Event], usb_events: Iterable[dict] = ()) -> dict:
    records = list(events)
    usb = list(usb_events)
    if not records:
        return {"status": "NO_VALID_RECORDER_EVENT", "last_stage": None,
                "next_expected": "IOS_LAUNCHER_ENTER"}
    last = records[-1]
    known = [stage for stage in EXPECTED_ORDER if stage <= last.stage]
    next_stage = next((stage for stage in EXPECTED_ORDER if stage > last.stage), None)
    result = {
        "status": "STAGE_ERROR" if last.error else "STALLED_AFTER_STAGE",
        "last_stage": last.stage_name,
        "last_stage_id": f"0x{last.stage:04x}",
        "error": last.error,
        "next_expected": STAGES.get(next_stage) if next_stage is not None else None,
        "event_count": len(records),
        "usb_outcomes": [row.get("identity") for row in usb if row.get("identity")],
    }
    if last.stage == 0x0620:
        result["boundary"] = "LINUX_ENTRY_CONTRACT"
        result["recommendation"] = "inspect only the bounded Linux head.S entry path"
    elif last.stage == 0x0510:
        result["boundary"] = "ANS_TO_STORAGE"
        result["recommendation"] = "inspect the bounded ANS/storage initialization call"
    elif 0x0400 <= last.stage < 0x0500:
        result["boundary"] = "M1N1_TO_HOOLOCK"
        result["recommendation"] = "stop in the same proxy and inspect Hoolock entry"
    elif last.stage >= 0x0800:
        result["boundary"] = "INITRAMFS_OR_ROOT"
        result["recommendation"] = "use the existing initramfs stage, without another loader change"
    else:
        result["boundary"] = "EARLY_HANDOFF"
        result["recommendation"] = "advance exactly one configured stop gate"
    return result


def page_json(path: Path) -> dict:
    header, events = decode_page(path.read_bytes())
    return {"header": {"write_sequence": header.write_sequence,
                       "flags": header.flags, "boot_nonce": header.boot_nonce.hex(),
                       "target": header.target,
                       "payload_sha256": header.payload_sha256.hex(),
                       "config_sha256": header.config_sha256.hex()},
            "events": [event.as_dict() for event in events],
            "classification": classify(events)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("page", type=Path)
    args = parser.parse_args()
    print(json.dumps(page_json(args.page), indent=2, sort_keys=True))
