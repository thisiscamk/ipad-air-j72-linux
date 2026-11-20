#!/usr/bin/env python3
"""Compare two J72 CPU-state JSON records without contacting the device."""

import argparse
import json
from pathlib import Path


REGISTERS = (
    "current_el", "mpidr_el1", "daif", "sctlr_el1", "tcr_el1",
    "ttbr0_el1", "ttbr1_el1", "mair_el1", "vbar_el1", "cpacr_el1",
    "sp_el1", "sp", "cntkctl_el1", "cntv_ctl_el0", "cntvoff_el2",
)


def descend(value, dotted):
    for part in filter(None, dotted.split(".")):
        value = value[part]
    return value


def integer(value):
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"not an integer or integer string: {value!r}")
    return int(value, 0) if isinstance(value, str) else value


def normalized(record):
    result = {}
    for name in REGISTERS:
        if name in record:
            result[name] = integer(record[name])
    if "sp_el1" not in result and "sp" in result:
        result["sp_el1"] = result.pop("sp")
    return result


def sctlr_flags(value):
    return {"M": bool(value & 1), "C": bool(value & 4), "I": bool(value & 0x1000)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--left-root", default="")
    parser.add_argument("--right-root", default="")
    parser.add_argument("--left-label", default="left")
    parser.add_argument("--right-label", default="right")
    args = parser.parse_args()

    left = normalized(descend(json.loads(args.left.read_text()), args.left_root))
    right = normalized(descend(json.loads(args.right.read_text()), args.right_root))
    rows = []
    for name in REGISTERS:
        canonical = "sp_el1" if name == "sp" else name
        if canonical == "sp" or any(row["register"] == canonical for row in rows):
            continue
        lv, rv = left.get(canonical), right.get(canonical)
        rows.append({
            "register": canonical,
            args.left_label: None if lv is None else f"0x{lv:016x}",
            args.right_label: None if rv is None else f"0x{rv:016x}",
            "status": "missing" if lv is None or rv is None else
                      ("same" if lv == rv else "different"),
            "xor": None if lv is None or rv is None else f"0x{lv ^ rv:016x}",
        })
    output = {
        "schema": "j72-entry-state-diff-v1",
        "labels": [args.left_label, args.right_label],
        "comparable": sum(row["status"] != "missing" for row in rows),
        "different": sum(row["status"] == "different" for row in rows),
        "rows": rows,
    }
    for label, record in ((args.left_label, left), (args.right_label, right)):
        if "sctlr_el1" in record:
            output.setdefault("decoded", {})[label] = {
                "sctlr_el1": sctlr_flags(record["sctlr_el1"])
            }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
