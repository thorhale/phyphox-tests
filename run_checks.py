#!/usr/bin/env python3
"""Run everything: file checks, capability claims, and the physics tests.

    python3 run_checks.py

No dependencies, so this also runs in Pydroid on the phone.
"""
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable or "python3"

STEPS = [
    ("file structure", [PY, "tools/lint.py"] + sorted(glob.glob(os.path.join(ROOT, "experiments/*.phyphox")))),
    ("capability claims", [PY, "tools/check_tiers.py"]),
    ("physics and maths", [PY, "tests/test_physics.py"]),
    ("do the tests have teeth", [PY, "tests/test_mutations.py"]),
]

failed = []
for name, cmd in STEPS:
    print(f"\n{'=' * 60}\n{name}\n{'=' * 60}")
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        failed.append(name)

print(f"\n{'=' * 60}")
if failed:
    print("FAILED: " + ", ".join(failed))
    sys.exit(1)
print("all checks passed")
