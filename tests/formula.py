#!/usr/bin/env python3
"""Evaluate a phyphox <formula> expression in Python.

The point of this is that the tests check the string that actually ships inside
the .phyphox file, not a hand-copied version of it. A copy tests whether I can
retype an expression; this tests the expression the phone will run.

phyphox syntax that has to be translated:
  [1]   the first input, as a single value
  [1_]  the first input, element by element
  ^     power
Everything else - the operators and the function names - already matches Python's
`math` module closely enough to evaluate directly.
"""
import math
import re
import xml.etree.ElementTree as ET

# The functions phyphox's formula parser documents. Anything outside this set
# appearing in a shipped file is itself a bug worth failing on.
FUNCS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan, "atan2": math.atan2,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh, "exp": math.exp,
    "log": math.log, "abs": abs, "sign": lambda x: (x > 0) - (x < 0),
    "heaviside": lambda x: 1.0 if x >= 0 else 0.0,
    "round": lambda x: float(math.floor(x + 0.5)),
    "ceil": math.ceil, "floor": math.floor, "min": min, "max": max,
}

ALLOWED = set(FUNCS) | {"e"}


def to_python(expr):
    """phyphox formula text -> a Python expression using v1, v2, ..."""
    py = re.sub(r"\[(\d+)_?\]", r"v\1", expr)
    py = py.replace("^", "**")
    # every bare word must be a known function; anything else is a typo that
    # would fail silently on the phone
    for word in set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", py)):
        if word.startswith("v") and word[1:].isdigit():
            continue
        if word not in ALLOWED:
            raise ValueError(f"unknown name {word!r} in formula: {expr}")
    return py


def evaluate(expr, *values):
    """Evaluate a formula with the given input values."""
    env = dict(FUNCS)
    for i, v in enumerate(values, start=1):
        env[f"v{i}"] = v
    return eval(to_python(expr), {"__builtins__": {}}, env)  # noqa: S307


def formulas_in(path):
    """Every formula string in a .phyphox file, in analysis order."""
    root = ET.parse(path).getroot()
    ana = root.find("./analysis")
    out = []
    for mod in (ana if ana is not None else []):
        if mod.tag is ET.Comment or mod.tag != "formula":
            continue
        ins = [(i.text or "").strip() if i.get("type") not in ("value", "empty")
               else (i.text or "").strip()
               for i in mod.findall("./input")]
        outs = [(o.text or "").strip() for o in mod.findall("./output")]
        out.append({"formula": mod.get("formula"), "inputs": ins, "outputs": outs})
    return out


def formula_for(path, output_name):
    """The formula that writes a named buffer. Fails loudly if absent, so a
    renamed buffer breaks the test rather than silently skipping it."""
    for f in formulas_in(path):
        if output_name in f["outputs"]:
            return f["formula"]
    raise AssertionError(f"{path}: no <formula> writes '{output_name}'")
