#!/usr/bin/env python3
"""Regression tests for the offline analyser - the backup route.

The backup plan is only worth having if it is known to work, so the analyser is
fed synthetic recordings whose correct answers are known exactly, and checked
against them. If phyphox never runs a single custom experiment, these numbers
are the ones you fall back on, so they had better be right.

    python3 tests/test_analyser.py
"""
import math
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tools", "analyse_export.py")
RATE = 48000.0

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def run(*args):
    r = subprocess.run([sys.executable, TOOL] + list(args),
                       capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(f"analyser failed: {r.stderr.strip() or r.stdout.strip()}")
    return r.stdout


def number_after(text, label):
    """The first number on the line containing `label`."""
    for line in text.splitlines():
        if label in line:
            m = re.search(r"(-?\d+\.?\d*)", line.split(label, 1)[1])
            if m:
                return float(m.group(1))
    raise AssertionError(f"no line containing {label!r} in:\n{text}")


def last_number(text, label):
    """The LAST number on the line containing `label`. Needed where the label
    itself contains numbers, e.g. "strongest tone between 50 and 500 Hz: 120.14"."""
    for line in text.splitlines():
        if label in line:
            nums = re.findall(r"(-?\d+\.?\d*)", line)
            if nums:
                return float(nums[-1])
    raise AssertionError(f"no line containing {label!r} in:\n{text}")


def close(got, want, tol, what):
    if not abs(got - want) <= tol:
        raise AssertionError(f"{what}: got {got}, wanted {want} (tolerance {tol})")


def write_audio(path, freq, amp, secs=1.0, rate=RATE):
    with open(path, "w") as fh:
        fh.write("Time (s),Recording (a.u.)\n")
        for i in range(int(rate * secs)):
            fh.write(f"{i / rate:.9f},{amp * math.sin(2 * math.pi * freq * i / rate):.9f}\n")


@test
def sound_level_matches_the_known_amplitude():
    """A sine of amplitude a has mean square a^2/2. At 1 kHz the A-weighting is
    zero, so all three weightings must agree."""
    with tempfile.TemporaryDirectory() as d:
        for amp in (1.0, 0.1, 0.01):
            p = os.path.join(d, "a.csv")
            write_audio(p, 1000.0, amp)
            out = run("sound", p, "--calibration", "0")
            want = 10 * math.log10(amp * amp / 2)
            close(number_after(out, "LAeq"), want, 0.05, f"LAeq at amplitude {amp}")
            close(number_after(out, "LZeq"), want, 0.05, f"LZeq at amplitude {amp}")
            close(number_after(out, "LCeq"), want, 0.05, f"LCeq at amplitude {amp}")
    return "-3.01, -23.01 and -43.01 dBFS, all three weightings agreeing at 1 kHz"


@test
def sample_rate_is_recovered_from_the_timestamps():
    """Rounded timestamps must not skew the rate - an early version read
    48008 Hz from a clean 48000 Hz recording."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "a.csv")
        write_audio(p, 1000.0, 0.5)
        close(number_after(run("sound", p, "--calibration", "0"), "at "), 48000.0,
              1.0, "recovered sample rate")
    return "48000 Hz recovered exactly"


@test
def a_weighting_is_applied_by_the_analyser():
    """A 125 Hz tone must read 16.1 dB lower than the same tone at 1 kHz."""
    with tempfile.TemporaryDirectory() as d:
        p1, p2 = os.path.join(d, "1k.csv"), os.path.join(d, "125.csv")
        write_audio(p1, 1000.0, 0.1)
        write_audio(p2, 125.0, 0.1)
        a1 = number_after(run("sound", p1, "--calibration", "0"), "LAeq")
        a2 = number_after(run("sound", p2, "--calibration", "0"), "LAeq")
        close(a2 - a1, -16.1, 0.4, "125 Hz relative to 1 kHz, A-weighted")
    return "125 Hz sits 16.1 dB down, as the standard requires"


@test
def clipping_is_reported():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "a.csv")
        write_audio(p, 1000.0, 1.0)
        if "CLIPPED" not in run("sound", p):
            raise AssertionError("a full-scale recording was not flagged as clipped")
        write_audio(p, 1000.0, 0.5)
        if "CLIPPED" in run("sound", p):
            raise AssertionError("a half-scale recording was wrongly flagged")
    return "flagged at full scale, not at half"


@test
def tone_mode_finds_a_spindle_frequency():
    """120 Hz is a 7200 rpm disk, and the analyser should say so."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.csv")
        write_audio(p, 120.0, 0.2)
        out = run("tone", p, "--from", "50", "--to", "500")
        close(last_number(out, "strongest tone between"), 120.0, 1.5, "tone frequency")
        if "7200 rpm disks" not in out:
            raise AssertionError("did not recognise 120 Hz as a 7200 rpm spindle")
        close(number_after(out, "as a shaft speed:"), 7200.0, 90.0, "RPM")
    return "120 Hz found and named as 7200 rpm"


@test
def blade_count_divides_the_tone():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.csv")
        write_audio(p, 450.0, 0.2)      # 9 blades on a 3000 rpm fan
        out = run("tone", p, "--from", "100", "--to", "1000", "--blades", "9")
        close(number_after(out, "divided by 9 blades:"), 3000.0, 40.0, "shaft speed")
    return "450 Hz over 9 blades = 3000 RPM"


@test
def magnetic_signature_matches_the_hand_computed_value():
    """The same vectors used in the physics tests: 47.634 uT at 22.525 deg."""
    with tempfile.TemporaryDirectory() as d:
        m, a = os.path.join(d, "m.csv"), os.path.join(d, "a.csv")
        with open(m, "w") as fh:
            fh.write("Time (s),Magnetic field x (uT),Magnetic field y (uT),Magnetic field z (uT)\n")
            for i in range(200):
                fh.write(f"{i * 0.01:.3f},18.0,-3.0,-44.0\n")
        with open(a, "w") as fh:
            fh.write("Time (s),Acceleration x (m/s^2),Acceleration y (m/s^2),Acceleration z (m/s^2)\n")
            for i in range(200):
                fh.write(f"{i * 0.01:.3f},0.0,0.0,-9.81\n")
        out = run("magnetic", m, "--accel", a)
        close(number_after(out, "field strength"), 47.634, 0.002, "field strength")
        close(number_after(out, "angle to gravity"), 22.525, 0.002, "angle to gravity")
        close(number_after(out, "variation"), 0.0, 1e-6, "variation of a constant field")
    return "47.634 uT at 22.525 deg, matching the physics tests exactly"


@test
def vibration_finds_the_machine_tone():
    """25 Hz is a 1500 rpm shaft. A pure sine also has a crest factor of
    exactly sqrt(2), which is a free check that the statistics are right."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "v.csv")
        with open(p, "w") as fh:
            fh.write("Time (s),Acceleration x (m/s^2),Acceleration y (m/s^2),Acceleration z (m/s^2)\n")
            for i in range(4096):
                fh.write(f"{i / 200:.6f},0,0,{9.81 + 0.05 * math.sin(2 * math.pi * 25 * i / 200):.6f}\n")
        out = run("vibration", p)
        close(number_after(out, "crest factor"), math.sqrt(2), 0.01,
              "crest factor of a pure sine")
        close(number_after(out, "highest frequency visible"), 100.0, 0.5, "Nyquist")
        first = [l for l in out.splitlines()
                 if "RPM" in l and "highest" not in l and "resolution" not in l][0]
        close(float(re.search(r"(-?\d+\.?\d*)", first).group(1)), 25.0, 0.1,
              "strongest tone")
        if "1500 RPM" not in first:
            raise AssertionError(f"25 Hz not reported as 1500 RPM: {first}")
    return "25 Hz / 1500 RPM found; crest factor sqrt(2) as a pure sine must give"


if __name__ == "__main__":
    passed = failed = 0
    for fn in TESTS:
        try:
            note = fn()
            passed += 1
            print(f"  pass  {fn.__name__}" + (f"  ({note})" if note else ""))
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}\n          {exc}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
