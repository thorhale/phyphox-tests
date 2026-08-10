#!/usr/bin/env python3
"""Static checks for .phyphox experiment files.

Catches the failure modes that only show up as a silent load error on the phone:
misspelled buffer names, formula placeholders that point past the input list,
analysis modules that do not exist, and views bound to nothing.
"""
import re
import sys
import xml.etree.ElementTree as ET

# modules seen in the official phyphox experiments and the wiki reference
MODULES = {
    "add", "subtract", "multiply", "divide", "power", "log", "gausssmooth", "abs",
    "sin", "cos", "tan", "sinh", "cosh", "tanh", "asin", "acos", "atan", "atan2",
    "first", "max", "min", "threshold", "append", "fft", "autocorrelation",
    "differentiate", "integrate", "crosscorrelation", "rangefilter", "subrange",
    "ramp", "const", "count", "average", "median", "binning", "if", "timer",
    "timer2", "formula", "round", "map", "reduce", "sort", "loess", "match",
    "interpolate", "split",
}
VIEW_ELEMENTS = {
    "value", "graph", "info", "edit", "button", "separator", "toggle", "slider",
    "dropdown", "image", "camera-gui", "depth-gui",
}


def _sz(v):
    """Declared container size as a number; "0" means unlimited."""
    try:
        n = int(v)
    except (TypeError, ValueError):
        return 1
    return 10**9 if n == 0 else n


def literal(el):
    """True if this input carries an inline value rather than a buffer name."""
    return el.get("type") in ("value", "empty")


def check(path):
    problems, warnings = [], []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return [f"XML is not well formed: {e}"], []

    if root.tag != "phyphox":
        problems.append(f"root element is <{root.tag}>, expected <phyphox>")
    if not root.get("version"):
        problems.append("root element has no version attribute")

    declared, sizes, static = set(), {}, set()
    for c in root.findall("./data-containers/container"):
        name = (c.text or "").strip()
        if not name:
            problems.append("a <container> has no name")
            continue
        if name in declared:
            problems.append(f"container '{name}' declared twice")
        declared.add(name)
        sizes[name] = c.get("size", "1")
        if c.get("static") == "true":
            static.add(name)

    used = set()

    def buffer_ref(el, where):
        name = (el.text or "").strip()
        if literal(el):
            return
        if not name:
            problems.append(f"{where}: <{el.tag}> has neither a buffer name nor type=value/empty")
            return
        used.add(name)
        if name not in declared:
            problems.append(f"{where}: '{name}' is not declared in <data-containers>")

    # ---- input / output hardware blocks
    for section in ("input", "output"):
        for dev in root.findall(f"./{section}/*"):
            for el in dev.findall(".//output") + dev.findall(".//input"):
                buffer_ref(el, f"<{section}><{dev.tag}>")

    # ---- analysis
    analysis = root.find("./analysis")
    if analysis is None:
        warnings.append("no <analysis> block")
    else:
        for i, mod in enumerate(analysis):
            if mod.tag is ET.Comment:
                continue
            where = f"analysis module #{i+1} <{mod.tag}>"
            if mod.tag not in MODULES:
                problems.append(f"{where}: unknown analysis module")
            ins = mod.findall("./input")
            for el in ins + mod.findall("./output"):
                buffer_ref(el, where)
            if mod.tag == "formula":
                f = mod.get("formula")
                if not f:
                    problems.append(f"{where}: no formula attribute")
                    continue
                refs = [int(m) for m in re.findall(r"\[(\d+)_?\]", f)]
                if not refs:
                    warnings.append(f"{where}: formula references no inputs")
                for r in refs:
                    if r < 1 or r > len(ins):
                        problems.append(
                            f"{where}: formula uses [{r}] but only {len(ins)} inputs are given")
                for j in range(1, len(ins) + 1):
                    if j not in refs:
                        warnings.append(f"{where}: input #{j} is never used by the formula")
                # scientific notation is not part of the documented grammar
                if re.search(r"\d[eE][-+]?\d", f):
                    problems.append(f"{where}: formula uses scientific notation, which is not documented as supported")
                if f.count("(") != f.count(")"):
                    problems.append(f"{where}: unbalanced parentheses in formula")

    # ---- views
    views = root.findall("./views/view")
    if not views:
        warnings.append("no <view> defined")
    for v in views:
        label = v.get("label", "?")
        for el in v:
            if el.tag is ET.Comment:
                continue
            if el.tag not in VIEW_ELEMENTS:
                problems.append(f"view '{label}': unknown element <{el.tag}>")
            for io in el.findall("./input") + el.findall("./output"):
                buffer_ref(io, f"view '{label}' <{el.tag}>")
            if el.tag == "graph":
                axes = {i.get("axis") for i in el.findall("./input")}
                if not {"x", "y"} <= axes:
                    problems.append(f"view '{label}': graph is missing an x or y input")
            if el.tag == "value" and not el.findall("./input"):
                problems.append(f"view '{label}': <value label='{el.get('label')}'> has no input")

    # ---- export
    for s in root.findall("./export/set"):
        for d in s.findall("./data"):
            name = (d.text or "").strip()
            used.add(name)
            if name not in declared:
                problems.append(f"export set '{s.get('name')}': '{name}' is not declared")

    # ---- ring-buffer and ordering checks (the silent killers) ----
    ana2 = root.find("./analysis")
    if ana2 is not None:
        consumed_at, state = {}, {}
        for idx, mod in enumerate(ana2):
            if mod.tag is ET.Comment:
                continue
            ins = [i for i in mod.findall("./input") if not literal(i)]
            names = [(i.text or "").strip() for i in ins]
            # widest array feeding this module
            in_size = max([_sz(sizes.get(n, "1")) for n in names] or [1])

            for i in ins:
                n = (i.text or "").strip()
                if n in consumed_at:
                    problems.append(
                        f"analysis module #{idx+1} <{mod.tag}>: reads '{n}' after module "
                        f"#{consumed_at[n]+1} already emptied it - it will be empty")

            for o in mod.findall("./output"):
                n = (o.text or "").strip()
                dest = _sz(sizes.get(n, "1"))
                # An array written with clear=false into a ring of comparable size
                # leaves stale values at the front and shifts every element after
                # them. Accumulating a SHORT array into a long one is a different,
                # legitimate pattern (waterfall plots), so only flag comparable sizes.
                if (o.get("clear") == "false" and 1 < dest < 10**9
                        and in_size >= dest):
                    warnings.append(
                        f"analysis module #{idx+1} <{mod.tag}>: writes an array to '{n}' "
                        f"(ring size {dest}) with clear=false - safe ONLY if the write is "
                        f"exactly {dest} long every cycle; one short leaves a stale value "
                        f"at the front and shifts the whole array. Prefer clear=true.")
                consumed_at.pop(n, None)
                state[n] = "filled"

            for i in ins:
                n = (i.text or "").strip()
                if i.get("clear") != "false" and n not in static:
                    consumed_at[n] = idx
                    state[n] = "emptied"

        hw = {(o.text or "").strip() for sec in ("input", "output")
              for dev in root.findall(f"./{sec}/*") for o in dev.findall(".//output")}
        for name in sorted(used):
            if state.get(name) == "emptied" and name not in hw:
                shown = any(name == (io.text or "").strip()
                            for v in root.findall("./views/view") for el in v
                            for io in el.findall("./input") if el.tag is not ET.Comment)
                exported = any(name == (d.text or "").strip()
                               for s in root.findall("./export/set") for d in s.findall("./data"))
                if shown or exported:
                    where = "a view" if shown else "the export"
                    problems.append(
                        f"'{name}' is shown by {where} but the analysis pass empties it - "
                        f"it will come out blank")

    for name in sorted(declared - used):
        warnings.append(f"container '{name}' (size {sizes[name]}) is declared but never used")

    return problems, warnings


if __name__ == "__main__":
    failed = False
    for path in sys.argv[1:]:
        problems, warnings = check(path)
        print(f"\n=== {path.split('/')[-1]} ===")
        for w in warnings:
            print(f"  warn  {w}")
        for p in problems:
            print(f"  FAIL  {p}")
        if not problems:
            print(f"  ok    no errors ({len(warnings)} warnings)")
        failed |= bool(problems)
    sys.exit(1 if failed else 0)
