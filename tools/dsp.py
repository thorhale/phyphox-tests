#!/usr/bin/env python3
"""Signal processing shared by the tests and the offline analyser.

Deliberately dependency-free: this has to run in Pydroid on a phone, which is
exactly the situation where the offline analyser matters most.
"""
import cmath
import math


def fft(x):
    """Radix-2 FFT. Length must be a power of two."""
    n = len(x)
    if n == 1:
        return list(x)
    if n & (n - 1):
        raise ValueError("length must be a power of two")
    ev, od = fft(x[0::2]), fft(x[1::2])
    out = [0j] * n
    for k in range(n // 2):
        t = cmath.exp(-2j * math.pi * k / n) * od[k]
        out[k] = ev[k] + t
        out[k + n // 2] = ev[k] - t
    return out


def hann(n):
    return [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]


def next_pow2_below(n):
    p = 1
    while p * 2 <= n:
        p *= 2
    return p


def num(s):
    """A float from a field that may use a comma decimal separator."""
    s = s.strip().strip('"')
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def read_csv(path):
    """phyphox export -> (headers, list of columns). Copes with the comma,
    semicolon and tab variants phyphox offers, and comma decimals."""
    with open(path, encoding="utf-8-sig") as fh:
        lines = [l for l in fh.read().splitlines() if l.strip()]
    if len(lines) < 2:
        raise SystemExit(f"{path}: needs a header row and at least one data row")
    delim = max([",", ";", "\t"], key=lambda d: len(lines[0].split(d)))
    headers = [h.strip().strip('"') for h in lines[0].split(delim)]
    cols = [[] for _ in headers]
    for line in lines[1:]:
        parts = line.split(delim)
        for i in range(len(headers)):
            v = num(parts[i]) if i < len(parts) else None
            cols[i].append(v)
    return headers, cols


def find_col(headers, keys, exclude=()):
    """Column index whose header contains any keyword, case-insensitively."""
    low = [h.lower() for h in headers]
    for i, h in enumerate(low):
        if any(k in h for k in keys) and not any(x in h for x in exclude):
            return i
    return -1


def rate_from_time(t):
    """Sample rate from a time column.

    Prefer the whole span divided by the number of intervals: rounding in the
    exported timestamps averages out, where a step-by-step estimate inherits it
    directly (a phyphox export rounded to 8 decimals reads 48008 Hz rather than
    48000 that way). Fall back to the median step when the two disagree, which
    means the recording has a gap and the span is no longer trustworthy.
    """
    t = [v for v in t if v is not None]
    if len(t) < 2:
        return None
    span = (len(t) - 1) / (t[-1] - t[0]) if t[-1] > t[0] else None
    steps = sorted(b - a for a, b in zip(t, t[1:]) if b > a)
    median = 1.0 / steps[len(steps) // 2] if steps else None
    if span and median and abs(span - median) / median > 0.1:
        return median
    return span or median
