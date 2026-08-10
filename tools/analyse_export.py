#!/usr/bin/env python3
"""Do the physics on a computer instead of on the phone.

This is the backup plan. If a custom experiment will not import, or phyphox
behaves differently from what its documentation says, the measurements are still
available: record with one of phyphox's own BUILT-IN experiments, export the
CSV, and analyse it here. The phone becomes a data logger and nothing else.

It matters that this is not a second implementation of the physics. Every
weighting curve, decibel conversion and signature formula is read straight out
of the .phyphox files and evaluated - the same expressions the regression tests
pin down. If the custom experiments turn out to work on your phone, the numbers
from both routes are computed by identical arithmetic.

    python3 tools/analyse_export.py sound     "Raw data.csv"
    python3 tools/analyse_export.py tone      "Raw data.csv" --from 50 --to 2000
    python3 tools/analyse_export.py magnetic  "Magnetometer.csv" --accel "Accelerometer.csv"
    python3 tools/analyse_export.py vibration "Accelerometer.csv"

Which built-in experiment to record with:

    sound, tone   Audio Scope, or Audio Autocorrelation - anything that exports
                  the raw waveform. NOT Audio Amplitude, which only exports a
                  level and has thrown the waveform away.
    magnetic      Magnetometer (plus Acceleration with g for the tilt angle)
    vibration     Acceleration with g, or Acceleration without g
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import fft, find_col, hann, next_pow2_below, rate_from_time, read_csv  # noqa: E402
from formula import evaluate, formula_for  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def exp_path(name):
    return os.path.join(ROOT, "experiments", name + ".phyphox")


TIME_KEYS = ("time", "t (", "timestamp")
AUDIO_KEYS = ("recording", "amplitude", "signal", "raw", "audio")


def column(headers, cols, keys, what, exclude=()):
    i = find_col(headers, keys, exclude)
    if i < 0:
        raise SystemExit(f"could not find {what} among the columns: {headers}")
    return [v for v in cols[i] if v is not None]


def blocks_of(data, n):
    for s in range(0, len(data) - n + 1, n):
        yield data[s:s + n]


# --------------------------------------------------------------------------
def cmd_sound(args):
    """A-, C- and Z-weighted levels from a raw audio export."""
    headers, cols = read_csv(args.csv)
    audio = column(headers, cols, AUDIO_KEYS, "an audio column", exclude=TIME_KEYS)
    ti = find_col(headers, TIME_KEYS)
    rate = args.rate or (rate_from_time([v for v in cols[ti] if v is not None])
                         if ti >= 0 else None)
    if not rate:
        raise SystemExit("no time column, so pass the sample rate with --rate")

    slm = exp_path("sound-level-meter")
    wA, wC = formula_for(slm, "wA"), formula_for(slm, "wC")
    norm = formula_for(slm, "msZ")
    n = 4096
    w = hann(n)
    freqs = None
    levels = {"Z": [], "A": [], "C": []}
    for blk in blocks_of(audio, n):
        spec = fft([blk[i] * w[i] for i in range(n)])
        if freqs is None:
            freqs = [k * rate / n for k in range(1, n // 2)]
            gA = [evaluate(wA, f) for f in freqs]
            gC = [evaluate(wC, f) for f in freqs]
        sZ = sA = sC = 0.0
        for j, k in enumerate(range(1, n // 2)):
            p = spec[k].real ** 2 + spec[k].imag ** 2
            sZ += p
            sA += p * gA[j]
            sC += p * gC[j]
        for key, s in (("Z", sZ), ("A", sA), ("C", sC)):
            levels[key].append(10 * math.log10(evaluate(norm, s, float(n))))
    if not levels["A"]:
        raise SystemExit(f"only {len(audio)} samples; need at least {n}")

    cal = args.calibration
    la = levels["A"]
    leq = 10 * math.log10(sum(10 ** (v / 10) for v in la) / len(la))
    print(f"  {len(la)} blocks of {n} samples at {rate:.0f} Hz "
          f"({len(la) * n / rate:.1f} s)")
    print(f"  calibration offset {cal:+.1f} dB "
          f"({'yours' if args.calibration != 120 else 'the default guess'})")
    print(f"  LAeq   {leq + cal:7.1f} dB(A)")
    print(f"  LAmax  {max(la) + cal:7.1f} dB(A)")
    print(f"  LAmin  {min(la) + cal:7.1f} dB(A)")
    print(f"  LCeq   {10 * math.log10(sum(10 ** (v / 10) for v in levels['C']) / len(la)) + cal:7.1f} dB(C)")
    print(f"  LZeq   {10 * math.log10(sum(10 ** (v / 10) for v in levels['Z']) / len(la)) + cal:7.1f} dB")
    cma = (10 * math.log10(sum(10 ** (v / 10) for v in levels['C']) / len(la))) - leq
    print(f"  LC-LA  {cma:7.1f} dB  ({'low-frequency dominated' if cma > 10 else 'little low-frequency energy' if cma < 3 else 'some low-frequency energy'})")
    peak = max(abs(v) for v in audio)
    print(f"  peak sample {20 * math.log10(max(peak, 1e-12)):.2f} dBFS"
          f"{'   *** CLIPPED, readings invalid ***' if peak >= 0.999 else ''}")


def cmd_tone(args):
    """Strongest frequency in a band - fan blade pass, tile ring, disk spindle."""
    headers, cols = read_csv(args.csv)
    audio = column(headers, cols, AUDIO_KEYS, "an audio column", exclude=TIME_KEYS)
    ti = find_col(headers, TIME_KEYS)
    rate = args.rate or (rate_from_time([v for v in cols[ti] if v is not None])
                         if ti >= 0 else None)
    if not rate:
        raise SystemExit("no time column, so pass the sample rate with --rate")

    n = min(next_pow2_below(len(audio)), 32768)
    if n < 256:
        raise SystemExit(f"only {len(audio)} samples, not enough for a spectrum")
    w = hann(n)
    # peak hold across the whole recording, so a single tap is not averaged away
    held = [0.0] * (n // 2 - 1)
    count = 0
    for blk in blocks_of(audio, n):
        spec = fft([blk[i] * w[i] for i in range(n)])
        for j, k in enumerate(range(1, n // 2)):
            m = math.hypot(spec[k].real, spec[k].imag)
            if m > held[j]:
                held[j] = m
        count += 1
    if not count:
        raise SystemExit("recording shorter than one analysis block")

    freqs = [k * rate / n for k in range(1, n // 2)]
    inband = [(m, f) for m, f in zip(held, freqs) if args.f_from <= f <= args.f_to]
    if not inband:
        raise SystemExit(f"no bins between {args.f_from} and {args.f_to} Hz")
    best_m, best_f = max(inband)
    print(f"  {count} block(s) of {n} at {rate:.0f} Hz, resolution {rate / n:.2f} Hz")
    print(f"  strongest tone between {args.f_from:.0f} and {args.f_to:.0f} Hz:"
          f"  {best_f:.2f} Hz")
    print(f"  as a shaft speed:            {best_f * 60:.0f} RPM")
    if args.blades > 1:
        print(f"  divided by {args.blades} blades:          {best_f * 60 / args.blades:.0f} RPM")
    for rpm, label in ((5400, "5400 rpm disks"), (7200, "7200 rpm disks"),
                       (10000, "10000 rpm disks"), (15000, "15000 rpm disks")):
        if abs(best_f - rpm / 60) < 3:
            print(f"  close to {label} ({rpm / 60:.0f} Hz)")
    ranked = sorted(zip(held, freqs), reverse=True)[:5]
    print("  strongest five overall:")
    for m, f in ranked:
        print(f"    {f:9.2f} Hz   {f * 60:8.0f} RPM   {20 * math.log10(m / best_m):6.1f} dB rel")


def cmd_magnetic(args):
    """The orientation-independent signature: field strength and its angle to
    gravity. Needs a magnetometer export; the angle also needs an accelerometer
    export covering the same moment."""
    headers, cols = read_csv(args.csv)
    bx = column(headers, cols, ("x",), "a magnetometer X column", exclude=TIME_KEYS)
    by = column(headers, cols, ("y",), "a magnetometer Y column", exclude=TIME_KEYS)
    bz = column(headers, cols, ("z",), "a magnetometer Z column", exclude=TIME_KEYS)
    nb = min(len(bx), len(by), len(bz))

    p = exp_path("magnetic-fingerprint")
    bmag_e = formula_for(p, "bMag")
    mags = [evaluate(bmag_e, bx[i], by[i], bz[i]) for i in range(nb)]
    mean = sum(mags) / nb
    var = sum((m - mean) ** 2 for m in mags) / nb
    print(f"  {nb} samples")
    print(f"  field strength   {mean:8.3f} uT   (this is the first half of the signature)")
    print(f"  variation        {math.sqrt(var):8.3f} uT   "
          f"({'steady - a usable fingerprint' if math.sqrt(var) < 1 else 'moving, or something nearby is switching'})")
    print(f"  range            {min(mags):8.3f} to {max(mags):.3f} uT")

    if not args.accel:
        print("  angle to gravity: pass --accel with an accelerometer export to get it")
        return
    ah, ac = read_csv(args.accel)
    ax = column(ah, ac, ("x",), "an accelerometer X column", exclude=TIME_KEYS)
    ay = column(ah, ac, ("y",), "an accelerometer Y column", exclude=TIME_KEYS)
    az = column(ah, ac, ("z",), "an accelerometer Z column", exclude=TIME_KEYS)
    na = min(len(ax), len(ay), len(az), nb)
    gmag_e, dot_e = formula_for(p, "gMag"), formula_for(p, "dot")
    cos_e, ang_e = formula_for(p, "cosAng"), formula_for(p, "incAng")
    angs = []
    for i in range(na):
        bm = evaluate(bmag_e, bx[i], by[i], bz[i])
        gm = evaluate(gmag_e, ax[i], ay[i], az[i])
        d = evaluate(dot_e, bx[i], by[i], bz[i], ax[i], ay[i], az[i])
        angs.append(evaluate(ang_e, evaluate(cos_e, d, bm, gm)))
    am = sum(angs) / na
    print(f"  angle to gravity {am:8.3f} deg  (the second half of the signature)")
    print(f"  variation        {math.sqrt(sum((a - am) ** 2 for a in angs) / na):8.3f} deg")
    print(f"\n  signature: {mean:.2f} uT at {am:.2f} deg")
    print("  Two readings match the same spot if sqrt(dB^2 + dAngle^2/4) is under about 0.5.")


def cmd_vibration(args):
    """Machine census from an accelerometer export."""
    headers, cols = read_csv(args.csv)
    ti = find_col(headers, TIME_KEYS)
    ai = find_col(headers, ("absolute", "abs"), exclude=TIME_KEYS)
    if ai >= 0:
        acc = [v for v in cols[ai] if v is not None]
    else:
        ax = column(headers, cols, ("x",), "an X column", exclude=TIME_KEYS)
        ay = column(headers, cols, ("y",), "a Y column", exclude=TIME_KEYS)
        az = column(headers, cols, ("z",), "a Z column", exclude=TIME_KEYS)
        m = min(len(ax), len(ay), len(az))
        acc = [math.sqrt(ax[i] ** 2 + ay[i] ** 2 + az[i] ** 2) for i in range(m)]
    rate = args.rate or (rate_from_time([v for v in cols[ti] if v is not None])
                         if ti >= 0 else None)
    if not rate:
        raise SystemExit("no time column, so pass the sample rate with --rate")

    n = min(next_pow2_below(len(acc)), 8192)
    if n < 256:
        raise SystemExit(f"only {len(acc)} samples, not enough for a spectrum")
    mean = sum(acc) / len(acc)
    det = [v - mean for v in acc]
    rms = math.sqrt(sum(v * v for v in det) / len(det))
    crest = max(abs(v) for v in det) / max(rms, 1e-12)

    w = hann(n)
    held = [0.0] * (n // 2 - 1)
    for blk in blocks_of(det, n):
        spec = fft([blk[i] * w[i] for i in range(n)])
        for j, k in enumerate(range(1, n // 2)):
            m = math.hypot(spec[k].real, spec[k].imag)
            if m > held[j]:
                held[j] = m
    freqs = [k * rate / n for k in range(1, n // 2)]

    print(f"  {len(acc)} samples at {rate:.1f} Hz ({len(acc) / rate:.1f} s)")
    print(f"  highest frequency visible   {rate / 2:.1f} Hz  "
          f"= {rate / 2 * 60:.0f} RPM. Anything faster folds down into a fake peak.")
    print(f"  resolution                  {rate / n:.3f} Hz = {rate / n * 60:.1f} RPM")
    print(f"  overall vibration           {rms:.5f} m/s^2")
    print(f"  crest factor                {crest:.2f}  "
          f"({'smooth' if crest < 3 else 'some impulsiveness' if crest < 4.5 else 'impulsive - compare with a healthy unit'})")
    print("  strongest tones (ignoring below 2 Hz):")
    ranked = sorted(((m, f) for m, f in zip(held, freqs) if f >= 2.0), reverse=True)
    top = ranked[:8]
    if not top:
        print("    nothing above 2 Hz")
        return
    loudest = top[0][0]
    shown = []
    for m, f in top:
        if any(abs(f - s) < 3 * rate / n for s in shown):
            continue      # same peak, neighbouring bin
        shown.append(f)
        print(f"    {f:8.2f} Hz   {f * 60:7.0f} RPM   {20 * math.log10(m / loudest):6.1f} dB rel")
        if len(shown) >= 5:
            break


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    s = sub.add_parser("sound", help="weighted sound levels from a raw audio export")
    s.add_argument("csv")
    s.add_argument("--rate", type=float, help="sample rate, if there is no time column")
    s.add_argument("--calibration", type=float, default=120.0,
                   help="dB offset; the default 120 is a guess, same as the experiment")
    s.set_defaults(func=cmd_sound)

    t = sub.add_parser("tone", help="strongest frequency in a band")
    t.add_argument("csv")
    t.add_argument("--rate", type=float)
    t.add_argument("--from", dest="f_from", type=float, default=20.0)
    t.add_argument("--to", dest="f_to", type=float, default=2000.0)
    t.add_argument("--blades", type=int, default=1, help="divide the tone by this")
    t.set_defaults(func=cmd_tone)

    m = sub.add_parser("magnetic", help="magnetic landmark signature")
    m.add_argument("csv")
    m.add_argument("--accel", help="accelerometer export, for the angle to gravity")
    m.set_defaults(func=cmd_magnetic)

    v = sub.add_parser("vibration", help="machine census from accelerometer data")
    v.add_argument("csv")
    v.add_argument("--rate", type=float)
    v.set_defaults(func=cmd_vibration)

    args = ap.parse_args()
    print(f"\n{args.mode} - {os.path.basename(args.csv)}")
    args.func(args)
    print()


if __name__ == "__main__":
    main()
