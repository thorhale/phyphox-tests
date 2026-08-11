#!/usr/bin/env python3
"""Check that the physics tests would actually notice if the physics broke.

A test suite that has never failed proves nothing. This deliberately corrupts
one constant at a time inside the shipped formulas, runs the physics tests, and
requires each corruption to be caught. Every mutation here is a mistake that
could plausibly be made while editing: a constant rounded off, two similar
constants swapped, a scale factor out by ten.

    python3 tests/test_mutations.py

The files are restored afterwards whatever happens. It works on a copy, so an
interrupted run cannot leave the experiments damaged.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (file, what to break, break it to, why anyone would care)
MUTATIONS = [
    ("dimension-survey", "331.3", "340.0",
     "speed of sound rounded to the usual textbook 340"),
    ("dimension-survey", "273.15", "273.0",
     "absolute zero rounded - a change too small to see in the output"),
    ("dimension-survey", "1000*", "100*",
     "slope scale out by a factor of ten"),
    ("sound-level-meter", "4.342944819032518", "8.685889638065035",
     "power and amplitude decibels confused"),
    ("sound-level-meter", "5.333333333333333", "2.666666666666666",
     "window and half-spectrum scaling halved"),
    ("sound-level-meter", "28800", "28000",
     "eight hours mistyped"),
    ("sound-level-meter", "1.584841544872967", "1.5848",
     "A-weighting normalisation truncated"),
    ("magnetic-fingerprint", "57.29577951308232", "57.0",
     "radians to degrees rounded"),
    ("rack-signature", "8.685889638065035", "4.342944819032518",
     "decibel constant swapped the other way"),
    ("ultrasonic-leak", "4.342944819032518", "10.0",
     "decibel conversion replaced with a plain 10"),
    ("vibration-census", "6.283185307179586", "3.141592653589793",
     "the 2*pi*f velocity divisor halved - mm/s would read double"),
    ("fan-tacho", "5.333333333333333", "2.666666666666666",
     "velocity window/half-spectrum scaling halved"),
]


def mutate_formulas(text, old, new):
    """Replace inside formula="..." only - never in the descriptions, or the
    test would be checking prose rather than physics."""
    present = any(old in f for f in re.findall(r'formula="([^"]*)"', text))
    if not present:
        return text, False
    out = re.sub(r'formula="([^"]*)"',
                 lambda m: 'formula="' + m.group(1).replace(old, new) + '"', text)
    return out, True


def main():
    work = tempfile.mkdtemp(prefix="phyphox-mutation-")
    try:
        shutil.copytree(os.path.join(ROOT, "tests"), os.path.join(work, "tests"))
        shutil.copy(os.path.join(ROOT, "capabilities.json"), work)
        shutil.copytree(os.path.join(ROOT, "tools"), os.path.join(work, "tools"))
        pristine = os.path.join(work, "pristine")
        shutil.copytree(os.path.join(ROOT, "experiments"), pristine)
        live = os.path.join(work, "experiments")

        caught = missed = skipped = 0
        for name, old, new, why in MUTATIONS:
            if os.path.exists(live):
                shutil.rmtree(live)
            shutil.copytree(pristine, live)

            target = os.path.join(live, name + ".phyphox")
            with open(target) as fh:
                text = fh.read()
            mutated, did = mutate_formulas(text, old, new)
            if not did:
                print(f"  SKIP    {why}\n            '{old}' is not in any formula in {name}")
                skipped += 1
                continue
            with open(target, "w") as fh:
                fh.write(mutated)

            r = subprocess.run([sys.executable, os.path.join(work, "tests", "test_physics.py")],
                               capture_output=True, text=True, cwd=work)
            if r.returncode:
                fails = [l.split()[1] for l in r.stdout.splitlines()
                         if l.strip().startswith("FAIL")]
                print(f"  caught  {why}\n            by {', '.join(fails[:3])}")
                caught += 1
            else:
                print(f"  MISSED  {why}\n            nothing failed - this physics is untested")
                missed += 1

        print(f"\n{caught} caught, {missed} missed, {skipped} skipped")
        if missed:
            print("A mutation that nothing catches means that number is not really tested.")
        return 1 if missed else 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
