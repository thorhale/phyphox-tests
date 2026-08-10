#!/usr/bin/env python3
"""Check every experiment against capabilities.json.

A compatibility table is only useful if it is true. This opens each .phyphox
file, works out what hardware it actually asks the phone for, and fails if that
disagrees with what capabilities.json claims. It also enforces the two promises
the suite is built on:

  * a Tier 0 experiment may only require Tier 0 hardware
  * an experiment marked ios:true may not require anything iOS lacks

    python3 tools/check_tiers.py
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def hardware_used(path):
    """(required, optional) hardware sets, read from the file itself."""
    root = ET.parse(path).getroot()
    required, optional = set(), set()

    for s in root.findall("./input/sensor"):
        name = s.get("type")
        if not name:
            continue
        # ignoreUnavailable means the experiment survives without it
        if s.get("ignoreUnavailable") == "true":
            optional.add(name)
        else:
            required.add(name)

    if root.findall("./input/audio"):
        required.add("audio_in")
    if root.findall("./output/audio"):
        required.add("audio_out")
    if root.findall("./output/flashlight"):
        required.add("flashlight")
    if root.findall("./input/bluetooth") or root.findall("./output/bluetooth"):
        required.add("bluetooth")
    if root.findall(".//camera-gui") or root.findall("./input/camera"):
        required.add("camera")

    return required, optional


def main():
    with open(os.path.join(ROOT, "capabilities.json")) as fh:
        caps = json.load(fh)

    tier0 = set(caps["tier0_hardware"])
    ios_missing = set(caps["not_on_ios"])
    claims = caps["experiments"]

    exp_dir = os.path.join(ROOT, "experiments")
    on_disk = {f[:-8] for f in os.listdir(exp_dir) if f.endswith(".phyphox")}

    problems = []

    for name in sorted(on_disk - set(claims)):
        problems.append(f"{name}: on disk but missing from capabilities.json")
    for name in sorted(set(claims) - on_disk):
        problems.append(f"{name}: claimed in capabilities.json but no such file")

    tier0_count = 0
    for name in sorted(on_disk & set(claims)):
        c = claims[name]
        actual_req, actual_opt = hardware_used(os.path.join(exp_dir, name + ".phyphox"))
        claimed_req, claimed_opt = set(c["required"]), set(c.get("optional", []))

        if actual_req != claimed_req:
            missing = claimed_req - actual_req
            extra = actual_req - claimed_req
            detail = []
            if extra:
                detail.append(f"file also requires {sorted(extra)}")
            if missing:
                detail.append(f"json claims {sorted(missing)} which the file never asks for")
            problems.append(f"{name}: required hardware disagrees - " + "; ".join(detail))

        if actual_opt != claimed_opt:
            problems.append(
                f"{name}: optional hardware disagrees - file has {sorted(actual_opt)}, "
                f"json says {sorted(claimed_opt)}"
            )

        # Tier 0 promise
        if c["tier"] == 0:
            tier0_count += 1
            outside = actual_req - tier0
            if outside:
                problems.append(
                    f"{name}: claims Tier 0 but requires {sorted(outside)}, "
                    f"which a basic phone may not have"
                )

        # iOS promise
        if c.get("ios"):
            blocked = actual_req & ios_missing
            if blocked:
                why = "; ".join(caps["not_on_ios"][b] for b in sorted(blocked))
                problems.append(f"{name}: claims iOS support but requires {sorted(blocked)} - {why}")

    print(f"{len(on_disk)} experiments, {tier0_count} of them Tier 0")

    guarantee = 15
    if tier0_count < guarantee:
        problems.append(
            f"only {tier0_count} Tier 0 experiments; the promise to basic phones is {guarantee}"
        )

    for p in problems:
        print(f"  FAIL  {p}")
    if not problems:
        print(f"  ok    every claim matches the files, and the Tier 0 promise ({guarantee}) is met")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
