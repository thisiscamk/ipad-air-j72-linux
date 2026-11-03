#!/usr/bin/env python3
"""Validate private J72 reply-audit snapshots and print counts, never raw data."""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

FIELDS = (
    "magic version done records cs_us sync_enable stream_enable policy seconds "
    "loops zeros padding length_zero length_positive stale bad_header bad_sum "
    "bad_length data_zero frames bad_frame xfer_errors info_end attention_high "
    "attention_low dropped"
).split()
HEADER = struct.Struct("<" + "I" * len(FIELDS))
DATA_BYTES = 2464
RECORD = struct.Struct(f"<IHHIHH16s{DATA_BYTES}s")
CAPACITY = 2048
SNAPSHOT_SIZE = HEADER.size + RECORD.size * CAPACITY
FULL_CAPACITY = 32768
FULL_SNAPSHOT_SIZE = HEADER.size + RECORD.size * FULL_CAPACITY
MAX_SNAPSHOT_SIZE = FULL_SNAPSHOT_SIZE


def valid_short(reply):
    return sum(reply[:14]) & 65535 == int.from_bytes(reply[14:16], "little")


def classic_contacts(body):
    """Decode classic 43..45 layouts without assuming a C struct size.

    Layout reference: Orchard PR28 input/0009 at 25bfbd4d53a6d5acb680711bd0219d1510839637.
    J72 has observed empty 44 headers with stride 30; actual contacts remain
    unqualified. Image bytes precede contacts in reports that include an image.
    """
    if len(body) < 22 or body[0] not in (0x43, 0x44, 0x45):
        raise ValueError("short or unknown classic report")
    header, count, stride = body[2], body[16], body[17]
    offset = header + int.from_bytes(body[14:16], "little")
    if header < 22 or offset > len(body) or count > 32:
        raise ValueError("invalid classic header or count")
    if count and (not 20 <= stride <= 64 or count > (len(body) - offset) // stride):
        raise ValueError("truncated classic contacts or invalid stride")
    contacts = []
    ids = set()
    for index in range(count):
        start = offset + index * stride
        contact = body[start:start + stride]
        if contact[0] in ids:
            raise ValueError("duplicate classic contact ID")
        ids.add(contact[0])
        contacts.append({
            "id": contact[0], "state": contact[1],
            "x": int.from_bytes(contact[4:6], "little", signed=True),
            "y": int.from_bytes(contact[6:8], "little", signed=True),
        })
    return contacts


def analyze(data):
    if len(data) not in (SNAPSHOT_SIZE, FULL_SNAPSHOT_SIZE):
        raise ValueError("unexpected snapshot size")
    h = dict(zip(FIELDS, HEADER.unpack_from(data)))
    if h["magic"] != 0x4A373252 or h["version"] not in (1, 2):
        raise ValueError("unknown snapshot format")
    capacity = CAPACITY if h["version"] == 1 else FULL_CAPACITY
    if len(data) != HEADER.size + RECORD.size * capacity:
        raise ValueError("snapshot version and size disagree")
    if h["done"] not in (1, 2, 3) or h["records"] > capacity:
        raise ValueError("snapshot incomplete or record count invalid")
    if h["cs_us"] not in (0, 10, 1000) or any(
        h[key] > 1 for key in ("sync_enable", "stream_enable", "info_end")
    ) or h["policy"] > 2 or not 1 <= h["seconds"] <= 600:
        raise ValueError("invalid probe configuration")
    if h["attention_high"] + h["attention_low"] != h["loops"]:
        raise ValueError("attention counters do not match polls")
    classified = sum(h[key] for key in (
        "zeros", "padding", "length_zero", "length_positive", "stale",
        "bad_header", "bad_sum", "bad_length"
    ))
    if not h["loops"] - h["xfer_errors"] <= classified <= h["loops"]:
        raise ValueError("length-response counters do not match polls")
    if h["frames"] + h["bad_frame"] + h["data_zero"] > h["length_positive"]:
        raise ValueError("more data replies than positive lengths")
    classes, headers = Counter(), Counter()
    classic_types, classic_counts, classic_states, classic_layouts, classic_formats = (
        Counter(), Counter(), Counter(), Counter(), Counter())
    classic_invalid = active_observations = 0
    coordinate_ranges = {}
    full_frames = truncated_frames = priming_requests = 0
    last_ms = 0
    for index in range(h["records"]):
        ms, kind, length, flags, stored, reserved, tx, rx = RECORD.unpack_from(
            data, HEADER.size + index * RECORD.size
        )
        if ms < last_ms or kind not in (1, 2) or reserved:
            raise ValueError(f"invalid record metadata at {index}")
        last_ms = ms
        if not 7 <= length <= 2459 or stored != min(length, DATA_BYTES):
            raise ValueError(f"invalid wire length at {index}")
        if flags & 0x3000 not in (0x1000, 0x2000):
            raise ValueError(f"invalid attention observation at {index}")
        if tx[0] != 0xEB or tx[1] not in (1, 2) or tx[2] != (kind == 2):
            raise ValueError(f"unexpected request at {index}")
        headers[f"0x{rx[0]:02x}"] += 1
        if kind == 1:
            if flags & 0x400:
                if h["policy"] != 2:
                    raise ValueError("priming request under a different policy")
                priming_requests += 1
            if length != 16 or not valid_short(tx):
                raise ValueError(f"invalid length request at {index}")
            if flags & 1:
                if any(rx[:16]):
                    raise ValueError("silence classification contains nonzero bytes")
                classes["silent"] += 1
            elif flags & 2:
                if any(rx[:14]) or not any(rx[14:16]):
                    raise ValueError("invalid padding classification")
                classes["padding_only"] += 1
            elif flags & 4:
                advertised = int.from_bytes(rx[1:3], "little")
                if rx[0] != 0xE1 or not valid_short(rx) or advertised > 2454 or advertised == 1:
                    raise ValueError("invalid checked length reply")
                if bool(advertised) != bool(flags & 8):
                    raise ValueError("positive-length flag disagrees with reply")
                classes["positive_length" if advertised else "valid_empty"] += 1
            elif flags & 16:
                if rx[0] & 0xF0 != 0xE0 or rx[0] == 0xE1 or not valid_short(rx):
                    raise ValueError("invalid stale-reply classification")
                classes["other_valid_short"] += 1
            elif flags & (32 | 64 | 128):
                classes["malformed_length"] += 1
            else:
                raise ValueError("length reply has no classification")
        elif flags & 256:
            inner = int.from_bytes(rx[2:4], "little")
            if rx[0] not in (0xEA, 0xEB) or sum(rx[:5]) & 255 or inner < 2 or inner + 5 != length:
                raise ValueError("invalid checked data header")
            if stored == length:
                expected = int.from_bytes(rx[length-2:length], "little")
                if sum(rx[5:inner+3]) & 65535 != expected:
                    raise ValueError("invalid checked data checksum")
                full_frames += 1
                body = rx[5:length-2]
                if body and body[0] in (0x43, 0x44, 0x45):
                    classic_types[f"0x{body[0]:02x}"] += 1
                    try:
                        contacts = classic_contacts(body)
                    except ValueError:
                        classic_invalid += 1
                    else:
                        classic_counts[len(contacts)] += 1
                        classic_formats[f"0x{body[10]:02x}"] += 1
                        classic_layouts[(body[2], body[17],
                            int.from_bytes(body[14:16], "little"))] += 1
                        for contact in contacts:
                            classic_states[contact["state"]] += 1
                            if contact["state"] not in (3, 4):
                                continue
                            active_observations += 1
                            for axis in ("x", "y"):
                                value = contact[axis]
                                low, high = coordinate_ranges.get(axis, (value, value))
                                coordinate_ranges[axis] = (min(low, value), max(high, value))
            else:
                truncated_frames += 1
            classes["valid_data"] += 1
        elif flags & 512:
            classes["invalid_data"] += 1
        else:
            raise ValueError("data reply has no classification")
    if classes["valid_data"] > h["frames"] or (
        not h["dropped"] and classes["valid_data"] != h["frames"]
    ):
        raise ValueError("retained data frames disagree with summary")
    return {
        "snapshot_version": h["version"],
        "snapshot_capacity": capacity,
        "complete": h["done"] == 1,
        "setup_failed": h["done"] == 2,
        "stopped_on_error": h["done"] == 3,
        "configuration": {key: h[key] for key in (
            "cs_us", "sync_enable", "stream_enable", "policy", "seconds")},
        "counters": {key: h[key] for key in FIELDS[9:]},
        "retained_records": h["records"],
        "retained_priming_requests": priming_requests,
        "retained_classes": dict(sorted(classes.items())),
        "retained_response_headers": dict(sorted(headers.items())),
        "full_frame_checksums_revalidated": full_frames,
        "valid_frames_stored_as_prefix_only": truncated_frames,
        "classic_reports": {
            "types": dict(sorted(classic_types.items())),
            "format_flags": dict(sorted(classic_formats.items())),
            "invalid_layouts": classic_invalid,
            "contact_counts": dict(sorted(classic_counts.items())),
            "contact_states": dict(sorted(classic_states.items())),
            "active_contact_observations": active_observations,
            "active_coordinate_ranges": coordinate_ranges,
            "layouts": [{"header_bytes": k[0], "stride": k[1],
                         "image_bytes": k[2], "frames": v}
                        for k, v in sorted(classic_layouts.items())],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    args = parser.parse_args()
    try:
        result = analyze(args.snapshot.read_bytes())
    except (OSError, ValueError, struct.error) as exc:
        parser.exit(1, f"snapshot rejected: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
