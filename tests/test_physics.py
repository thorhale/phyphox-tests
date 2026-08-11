#!/usr/bin/env python3
"""Regression tests for the physics and arithmetic behind every experiment.

Run with no arguments:

    python3 tests/test_physics.py

No dependencies, so it runs anywhere - including in Pydroid on the phone.

Two kinds of test here, and the distinction matters:

  * behaviour  - simulate the analysis chain and check it against a known
                 answer (a full-scale sine must read -3.010 dBFS)
  * contract   - pull the actual formula string or constant out of the .phyphox
                 file and check THAT. These fail if a file is edited in a way
                 that breaks a documented claim, which is the whole point of a
                 regression test.

Every number asserted here is quoted somewhere in the experiment descriptions or
the README. If a test fails, either the file is wrong or the documentation is -
and both matter equally, because a confident wrong number is worse than no
number at all.
"""
import cmath
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from formula import evaluate, formula_for  # noqa: E402
from dsp import fft  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments")


def path(name):
    return os.path.join(EXP, name + ".phyphox")


def source(name):
    with open(path(name)) as fh:
        return fh.read()


# --------------------------------------------------------------------------
# a tiny test harness, so there is nothing to install
# --------------------------------------------------------------------------
TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def close(got, want, tol, what):
    if not abs(got - want) <= tol:
        raise AssertionError(f"{what}: got {got!r}, wanted {want!r} (tolerance {tol})")


def contains(name, needle, why):
    if needle not in source(name):
        raise AssertionError(f"{name}.phyphox no longer contains {needle!r} - {why}")


# ==========================================================================
# Sound level meter
# ==========================================================================
IEC_A = {10: -70.4, 12.5: -63.4, 16: -56.7, 20: -50.5, 25: -44.7, 31.5: -39.4,
         40: -34.6, 50: -30.2, 63: -26.2, 80: -22.5, 100: -19.1, 125: -16.1,
         160: -13.4, 200: -10.9, 250: -8.6, 315: -6.6, 400: -4.8, 500: -3.2,
         630: -1.9, 800: -0.8, 1000: 0.0, 1250: 0.6, 1600: 1.0, 2000: 1.2,
         2500: 1.3, 3150: 1.2, 4000: 1.0, 5000: 0.5, 6300: -0.1, 8000: -1.1,
         10000: -2.5, 12500: -4.3, 16000: -6.6, 20000: -9.3}

IEC_C = {10: -14.3, 12.5: -11.2, 16: -8.5, 20: -6.2, 25: -4.4, 31.5: -3.0,
         40: -2.0, 50: -1.3, 63: -0.8, 80: -0.5, 100: -0.3, 125: -0.2,
         160: -0.1, 200: 0.0, 250: 0.0, 315: 0.0, 400: 0.0, 500: 0.0, 630: 0.0,
         800: 0.0, 1000: 0.0, 1250: 0.0, 1600: -0.1, 2000: -0.2, 2500: -0.3,
         3150: -0.5, 4000: -0.8, 5000: -1.3, 6300: -2.0, 8000: -3.0,
         10000: -4.4, 12500: -6.2, 16000: -8.5, 20000: -11.2}


@test
def a_weighting_matches_iec_61672():
    """The shipped A-weighting expression against the standard's own table.

    README claims agreement within 0.27 dB from 10 Hz to 20 kHz.
    """
    expr = formula_for(path("sound-level-meter"), "wA")
    worst, worst_f = 0.0, None
    for f, want in IEC_A.items():
        got = 10 * math.log10(evaluate(expr, f))   # the formula gives weight SQUARED
        if abs(got - want) > worst:
            worst, worst_f = abs(got - want), f
        close(got, want, 0.4, f"A-weighting at {f} Hz")
    if worst > 0.28:
        raise AssertionError(f"worst A deviation {worst:.3f} dB at {worst_f} Hz, "
                             f"README claims 0.27")
    return f"worst {worst:.3f} dB at {worst_f} Hz"


@test
def c_weighting_matches_iec_61672():
    expr = formula_for(path("sound-level-meter"), "wC")
    worst, worst_f = 0.0, None
    for f, want in IEC_C.items():
        got = 10 * math.log10(evaluate(expr, f))
        if abs(got - want) > worst:
            worst, worst_f = abs(got - want), f
        close(got, want, 0.4, f"C-weighting at {f} Hz")
    return f"worst {worst:.3f} dB at {worst_f} Hz"


@test
def weighting_curves_are_zero_at_1_khz():
    """Both curves are defined to pass through 0 dB at 1 kHz. If the
    normalisation constants drift, every reading shifts."""
    for name in ("wA", "wC"):
        expr = formula_for(path("sound-level-meter"), name)
        close(10 * math.log10(evaluate(expr, 1000.0)), 0.0, 0.01, f"{name} at 1 kHz")
    return "both 0.00 dB"


def level_chain(signal, n, rate, weight_expr=None):
    """Mirror of the sound level meter's analysis chain, using the shipped
    normalisation constant read out of the file."""
    norm_expr = formula_for(path("sound-level-meter"), "msZ")
    w = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    blk = [signal[i] * w[i] for i in range(n)]
    spec = fft(blk)
    total = 0.0
    for k in range(1, n // 2):
        p = spec[k].real ** 2 + spec[k].imag ** 2
        if weight_expr is not None:
            p *= evaluate(weight_expr, k * rate / n)
        total += p
    ms = evaluate(norm_expr, total, float(n))
    return 10 * math.log10(ms)


@test
def full_scale_sine_reads_minus_3_01_dbfs():
    """A full-scale sine has mean square 0.5, so -3.010 dBFS. This is the
    single number that proves the whole scaling chain - window power, the
    half-spectrum doubling and the 1/N^2 all have to be right together."""
    rate = 48000.0
    for n in (1024, 2048, 4096):
        sig = [math.sin(2 * math.pi * 1000 * i / rate) for i in range(n)]
        close(level_chain(sig, n, rate), -3.010, 0.02, f"full-scale sine, N={n}")
    return "-3.010 dBFS at N=1024, 2048, 4096"


@test
def level_is_linear_in_amplitude():
    """Halving the amplitude must drop the level by exactly 6.02 dB."""
    rate, n = 48000.0, 2048
    prev = None
    for amp in (1.0, 0.5, 0.25, 0.1, 0.01):
        sig = [amp * math.sin(2 * math.pi * 1000 * i / rate) for i in range(n)]
        got = level_chain(sig, n, rate)
        close(got, 10 * math.log10(amp * amp / 2), 0.02, f"amplitude {amp}")
        if prev is not None and amp == 0.25:
            close(prev - got, 6.02, 0.05, "halving amplitude")
        prev = got
    return "linear to 0.02 dB over 40 dB"


@test
def weighted_level_tracks_the_curve():
    """A tone at 125 Hz must come out 16.1 dB below the same tone at 1 kHz
    once A-weighted - i.e. the weighting really is being applied to the
    spectrum, not just computed and discarded."""
    rate, n = 48000.0, 8192
    wA = formula_for(path("sound-level-meter"), "wA")
    ref = level_chain([math.sin(2 * math.pi * 1000 * i / rate) for i in range(n)],
                      n, rate, wA)
    for f, want in ((125, -16.1), (500, -3.2), (4000, 1.0)):
        got = level_chain([math.sin(2 * math.pi * f * i / rate) for i in range(n)],
                          n, rate, wA)
        close(got - ref, want, 0.3, f"A-weighted tone at {f} Hz")
    return "125, 500 and 4000 Hz all within 0.3 dB of the table"


@test
def noise_dose_matches_the_three_db_exchange_rate():
    """At the criterion level the allowed time is exactly 8 hours, and every
    3 dB above it halves that. This is the rule the file claims to implement."""
    expr = formula_for(path("sound-level-meter"), "tAllowed")
    close(evaluate(expr, 85.0, 85.0), 28800.0, 1.0, "8 h at the criterion level")
    # "3 dB exchange rate" is shorthand for equal energy, and a true doubling
    # of energy is 10*log10(2) = 3.0103 dB, not a round 3. Assert the exact
    # halving, then pin what a round 3 dB actually gives so the 0.24 %
    # difference can never be mistaken for an error later.
    half = 10 * math.log10(2)
    close(evaluate(expr, 85.0 + half, 85.0), 14400.0, 1.0, "4 h at one doubling")
    close(evaluate(expr, 85.0 + 2 * half, 85.0), 7200.0, 1.0, "2 h at two doublings")
    close(evaluate(expr, 85.0 - half, 85.0), 57600.0, 2.0, "16 h one halving down")
    close(evaluate(expr, 88.0, 85.0), 14434.2, 1.0, "a round +3 dB is 14434 s, not 14400")
    dose = formula_for(path("sound-level-meter"), "dose")
    close(evaluate(dose, 85.0, 28800.0, 85.0), 100.0, 0.1, "full shift at 85 dB = 100 %")
    close(evaluate(dose, 85.0 + half, 14400.0, 85.0), 100.0, 0.1,
          "half a shift at one doubling = 100 %")
    return "8 h at 85 dB; exact halving at 3.0103 dB, not a round 3"


# ==========================================================================
# Vibration census / fan tacho: acceleration spectrum -> velocity in mm/s
# ==========================================================================
def velocity_chain(name, signal, n, rate):
    """Mirror of the shipped acceleration->velocity chain, using the actual
    velPow / velMS / velRms formula strings read out of the file. Returns the
    band-limited (10 Hz..Nyquist) velocity RMS in mm/s."""
    vel_pow = formula_for(path(name), "velPow")
    vel_ms = formula_for(path(name), "velMS")
    vel_rms = formula_for(path(name), "velRms")
    w = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    mean = sum(signal) / n
    blk = [(signal[i] - mean) * w[i] for i in range(n)]
    spec = fft(blk)
    total = 0.0
    for k in range(1, n // 2):
        f = k * rate / n
        if f < 10.0:
            continue
        mag = math.sqrt(spec[k].real ** 2 + spec[k].imag ** 2)
        total += evaluate(vel_pow, mag, f)          # power / (2*pi*f)^2
    ms = evaluate(vel_ms, total, float(n))           # * 5.3333/N^2
    return evaluate(vel_rms, ms)                      # 1000 * sqrt


@test
def vibration_velocity_matches_the_analytic_mm_per_s():
    """A pure acceleration sine of amplitude A at f0 is velocity A/(2*pi*f0)
    peak, i.e. A/(2*pi*f0*sqrt2) RMS. The shipped chain has to reproduce that
    physical number in mm/s, which is what makes it comparable to ISO 10816.
    This pins the 2*pi*f divisor, the 5.3333/N^2 window+half-spectrum scaling
    and the x1000 all at once."""
    rate, n = 470.6, 2048
    worst = 0.0
    for A, f0 in ((2.0, 50.0), (1.0, 30.0), (0.5, 80.0), (3.0, 24.0)):
        sig = [A * math.sin(2 * math.pi * f0 * i / rate) for i in range(n)]
        want = 1000.0 * A / (2 * math.pi * f0 * math.sqrt(2))
        for name in ("vibration-census", "fan-tacho"):
            got = velocity_chain(name, sig, n, rate)
            worst = max(worst, abs(got - want) / want)
            close(got, want, want * 0.02, f"{name} velocity, A={A} f0={f0}")
    return f"worst {worst * 100:.2f}% of analytic across both files"


@test
def kurtosis_is_three_for_gaussian_and_1p5_for_a_sine():
    """Kurtosis is the bearing early-warning that survives where crest factor
    fails. A healthy random buzz reads 3, a pure sine reads exactly 1.5, and
    sharp impacts read well above 3. Evaluates the shipped vibKurt formula, so a
    structural edit (rms^4 mistyped as rms^2) is caught by the sine no longer
    landing on 1.5."""
    expr = formula_for(path("fan-tacho"), "vibKurt")

    def chain(sig):
        n = len(sig)
        mean = sum(sig) / n
        d = [v - mean for v in sig]
        mean4 = sum(v ** 4 for v in d) / n
        rms = math.sqrt(sum(v * v for v in d) / (n - 1))  # phyphox corrected stddev
        return evaluate(expr, mean4, rms)

    n = 8192
    sine = [math.sin(2 * math.pi * i / 64) for i in range(n)]
    close(chain(sine), 1.5, 0.01, "kurtosis of a sine")
    random.seed(7)
    g = [random.gauss(0, 1) for _ in range(n)]
    close(chain(g), 3.0, 0.25, "kurtosis of Gaussian noise")
    spiky = list(g)
    for i in range(0, n, 150):
        spiky[i] += 15.0
    if chain(spiky) < 6.0:
        raise AssertionError("kurtosis failed to flag a spiky (early-fault) signal")
    return "sine 1.50, Gaussian ~3, spiky well above"


@test
def spectral_flatness_reads_e_minus_gamma_for_white_noise():
    """The leak texture score is geometric mean / arithmetic mean of the band
    power. The trap most implementations miss: a single spectrum of true
    broadband noise reads e^-gamma = 0.5615, NOT 1.0, because each bin is an
    exponentially-distributed estimate. Evaluates the shipped nP / lnNP /
    flatness formulas, so both the estimator and that value are pinned."""
    name = "ultrasonic-leak"
    f_np = formula_for(path(name), "nP")            # [1_]/max([2],tiny)
    f_ln = formula_for(path(name), "lnNP")          # log([1_]+tiny)
    f_flat = formula_for(path(name), "flatness")    # exp([1])

    def flat(power):
        n = len(power)
        arith = sum(power) / n
        nP = [evaluate(f_np, p, arith) for p in power]
        lns = [evaluate(f_ln, v) for v in nP]
        return evaluate(f_flat, sum(lns) / n)

    close(flat([1.0] * 2048), 1.0, 0.001, "a perfectly flat band reads 1.0")
    random.seed(11)
    exp_bins = [-math.log(random.random()) for _ in range(20000)]  # Exp(1)
    close(flat(exp_bins), math.exp(-0.5772156649015329), 0.02,
          "white-noise flatness = e^-gamma = 0.5615")
    tonal = [0.0001] * 2048
    tonal[500] = 1000.0
    if flat(tonal) > 0.1:
        raise AssertionError("a tone should read flatness near 0, not high")
    return "flat 1.00, white noise 0.5615 (e^-gamma), tone ~0"


@test
def statistical_levels_pick_the_right_percentiles():
    """L90 (the background) must be the level exceeded 90% of the time, i.e. the
    10th percentile of the sorted levels; L10 the 90th; L50 the median. Reads the
    shipped index formulas and checks them against a known ramp, so a swapped
    0.1/0.9 (which would report the peaks as the background) is caught."""
    i90 = formula_for(path("sound-level-meter"), "i90")
    i50 = formula_for(path("sound-level-meter"), "i50")
    i10 = formula_for(path("sound-level-meter"), "i10")
    n = 1000
    levels = list(range(1, n + 1))          # uniform 1..1000, already ascending
    got90 = levels[int(evaluate(i90, float(n)))]
    got50 = levels[int(evaluate(i50, float(n)))]
    got10 = levels[int(evaluate(i10, float(n)))]
    close(got90, 100, 1, "L90 at the 10th percentile")
    close(got50, 500, 1, "L50 at the median")
    close(got10, 900, 1, "L10 at the 90th percentile")
    if not got90 < got50 < got10:
        raise AssertionError("L90 must be the quiet end, L10 the loud end")
    return "L90=100, L50=500, L10=900 on a uniform 1..1000"


# ==========================================================================
# Dimension survey: speed of sound as a thermometer
# ==========================================================================
@test
def speed_of_sound_round_trips():
    """Temperature -> speed -> temperature must return the original. The two
    expressions are written separately in the file and could drift apart."""
    fwd = formula_for(path("dimension-survey"), "speedofsound")
    rev = formula_for(path("dimension-survey"), "measuredTemp")
    for t in (0.0, 15.0, 22.0, 24.0, 40.0):
        close(evaluate(rev, evaluate(fwd, t)), t, 1e-6, f"round trip at {t} C")
    # A round trip alone is not enough: change 273.15 in both directions and it
    # still round trips perfectly while every reading is wrong. So check
    # absolute values too, computed here independently of the file.
    for t_c, want in ((0.0, 331.3000), (20.0, 343.2146), (24.0, 345.5483), (40.0, 354.7293)):
        close(evaluate(fwd, t_c), want, 0.002, f"speed of sound at {t_c} C")
    # Rounding 273.15 to 273 moves the answer by under 0.01 m/s - too small for
    # a value check to catch reliably, and still a change nobody intended. So
    # the constants are pinned in the formula text itself.
    for name in ("speedofsound", "measuredTemp"):
        text = formula_for(path("dimension-survey"), name)
        for needle in ("331.3", "273.15"):
            if needle not in text:
                raise AssertionError(f"{name} no longer uses {needle}: {text}")
    return "absolute values right at 0-40 C; 331.3 and 273.15 pinned in both directions"


@test
def thermometer_sensitivity_is_as_documented():
    """The file warns that 1 % error in the typed distance becomes about 6 C.
    That warning is the main thing keeping the reading honest, so it is tested."""
    fwd = formula_for(path("dimension-survey"), "speedofsound")
    rev = formula_for(path("dimension-survey"), "measuredTemp")
    c24 = evaluate(fwd, 24.0)
    close(evaluate(fwd, 25.0) - c24, 0.58, 0.02, "speed change per degree")
    err = evaluate(rev, c24 * 1.01) - 24.0
    close(err, 5.97, 0.1, "1 % distance error in degrees")
    return f"0.58 m/s per C; 1 % distance error = {err:.2f} C"


@test
def hot_and_cold_aisle_differ_by_three_percent():
    """The claim that justifies temperature-correcting the sonar at all."""
    fwd = formula_for(path("dimension-survey"), "speedofsound")
    ratio = evaluate(fwd, 40.0) / evaluate(fwd, 22.0)
    close(100 * (ratio - 1), 3.0, 0.1, "22 C vs 40 C")
    close(300 * (ratio - 1), 9.0, 0.3, "error over a 3 m span, in cm")
    return "3.0 %, which is 9 cm over 3 m"


@test
def inclinometer_slope_is_a_true_tangent():
    """Slope in mm/m must be 1000*tan(angle), and the tilt in degrees must
    agree with the slope. Two separate formulas in the file, one physics."""
    tilt = formula_for(path("dimension-survey"), "tiltY")
    slope = formula_for(path("dimension-survey"), "slopeY")
    g = 9.81
    for deg in (0.0, 0.1, 0.5, 1.0, 5.0):
        r = math.radians(deg)
        ay, az, ax = g * math.sin(r), g * math.cos(r), 0.0
        close(evaluate(tilt, ay, ax, az), deg, 1e-6, f"tilt at {deg} deg")
        close(evaluate(slope, ay, ax, az), 1000 * math.tan(r), 1e-6,
              f"slope at {deg} deg")
    close(evaluate(slope, g * math.sin(math.radians(0.0573)), 0.0,
                   g * math.cos(math.radians(0.0573))), 1.0, 0.01,
          "1 mm/m is about 0.0573 degrees")
    return "tan exact; 1 mm/m = 0.0573 deg"


# ==========================================================================
# Magnetic landmark
# ==========================================================================
def rand_rotation(rng):
    q = [rng.gauss(0, 1) for _ in range(4)]
    n = math.sqrt(sum(v * v for v in q))
    w, x, y, z = [v / n for v in q]
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def rotate(m, v):
    return [sum(m[i][j] * v[j] for j in range(3)) for i in range(3)]


def signature(B, G):
    """Field strength and the angle to gravity, using the shipped formulas."""
    p = path("magnetic-fingerprint")
    bmag = evaluate(formula_for(p, "bMag"), *B)
    gmag = evaluate(formula_for(p, "gMag"), *G)
    dot = evaluate(formula_for(p, "dot"), B[0], B[1], B[2], G[0], G[1], G[2])
    cos = evaluate(formula_for(p, "cosAng"), dot, bmag, gmag)
    return bmag, evaluate(formula_for(p, "incAng"), cos)


@test
def magnetic_signature_survives_any_phone_orientation():
    """The headline claim: it does not matter how you hold the phone. Checked
    over 200 random orientations, as stated in the commit history."""
    rng = random.Random(11)
    B, G = [18.0, -3.0, -44.0], [0.0, 0.0, -9.81]
    sigs = [signature(rotate(r, B), rotate(r, G))
            for r in (rand_rotation(rng) for _ in range(200))]
    spread_b = max(s[0] for s in sigs) - min(s[0] for s in sigs)
    spread_a = max(s[1] for s in sigs) - min(s[1] for s in sigs)
    if spread_b > 1e-9 or spread_a > 1e-9:
        raise AssertionError(f"not orientation invariant: |B| varies by {spread_b}, "
                             f"angle by {spread_a}")
    return f"200 orientations, spread {max(spread_b, spread_a):.1e}"


@test
def magnetic_mismatch_thresholds_mean_what_they_say():
    """'On the spot' is under 0.5. Check that corresponds to a field change
    small enough to be a genuine claim about standing in the same place."""
    p = path("magnetic-fingerprint")
    mis = formula_for(p, "mismatch")
    close(evaluate(mis, 0.0, 0.0), 0.0, 1e-12, "identical readings")
    close(evaluate(mis, 1.0, 0.0), 1.0, 1e-12, "1 uT of field difference")
    close(evaluate(mis, 0.0, 2.0), 1.0, 1e-12, "2 degrees of angle difference")
    B, G = [18.0, -3.0, -44.0], [0.0, 0.0, -9.81]
    b0, a0 = signature(B, G)
    for d, want in ((0.5, 0.33), (1.0, 0.67), (3.0, 2.01)):
        b1, a1 = signature([B[0] + d, B[1], B[2]], G)
        close(evaluate(mis, b1 - b0, a1 - a0), want, 0.02,
              f"{d} uT change on one axis")
    return "1 uT == 2 deg == 1.0 mismatch, as documented"


# ==========================================================================
# Spectral comparison (rack signature, room echo)
# ==========================================================================
@test
def spectral_distance_is_a_proper_rms():
    """The bug that shipped: integrate emptied the buffer before count read it,
    so the sum was never divided by the number of bins and the answer was out
    by a factor of sqrt(N). This pins the arithmetic."""
    for name, nbins in (("rack-signature", 4095), ("acoustic-fingerprint", 1200)):
        expr = formula_for(path(name), "mismatch")
        close(evaluate(expr, nbins * 9.0, float(nbins)), 3.0, 1e-9,
              f"{name}: a uniform 3-unit difference")
        close(evaluate(expr, 0.0, float(nbins)), 0.0, 1e-12, f"{name}: identical")
        naive = math.sqrt(nbins * 9.0)
        if abs(evaluate(expr, nbins * 9.0, float(nbins)) - naive) < 1.0:
            raise AssertionError(f"{name}: still looks like the un-normalised form")
    return "rack-signature and room echo both divide by N"


@test
def decibel_conversion_constants_are_right():
    """dB from a natural log needs 10/ln(10) for power and 20/ln(10) for
    amplitude. Getting these confused scales every reading by two."""
    close(10 / math.log(10), 4.342944819032518, 1e-15, "10/ln(10)")
    close(20 / math.log(10), 8.685889638065035, 1e-15, "20/ln(10)")
    contains("sound-level-meter", "4.342944819032518", "power-to-dB constant")
    contains("rack-signature", "8.685889638065035", "amplitude-to-dB constant")
    x = 100.0
    close(4.342944819032518 * math.log(x), 10 * math.log10(x), 1e-12, "power dB")
    close(8.685889638065035 * math.log(x), 20 * math.log10(x), 1e-12, "amplitude dB")
    return "both constants present and correct"


# ==========================================================================
# Constants embedded in the files
# ==========================================================================
@test
def hann_window_normalisation_is_correct():
    """5.3333 = 2 / 0.375: doubling for using half the spectrum, divided by the
    Hann window's mean square. Verified against a directly computed window."""
    n = 4096
    w = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    close(sum(v * v for v in w) / n, 0.375, 1e-3, "Hann mean square")
    close(2 / 0.375, 5.333333333333333, 1e-12, "the shipped constant")
    contains("sound-level-meter", "5.333333333333333", "Hann + half-spectrum scaling")
    return "0.375 confirmed, 2/0.375 = 5.3333"


@test
def hardcoded_maths_constants_are_what_they_claim():
    """Every magic number in the files, checked against what it should be."""
    checks = [
        (6.283185307179586, 2 * math.pi, "2*pi, for the Hann window"),
        (57.29577951308232, 180 / math.pi, "radians to degrees"),
        (148693636.0, 12194.0 ** 2, "12194^2, the weighting pole"),
        (424.36, 20.6 ** 2, "20.6^2"),
        (11599.29, 107.7 ** 2, "107.7^2"),
        (544496.41, 737.9 ** 2, "737.9^2"),
    ]
    for got, want, why in checks:
        close(got, want, abs(want) * 1e-12 + 1e-9, why)
    contains("sound-level-meter", "6.283185307179586", "2*pi")
    contains("dimension-survey", "57.29577951308232", "radians to degrees")
    contains("sound-level-meter", "28800", "eight hours in seconds")
    close(8 * 3600, 28800, 0, "eight hours")
    return f"{len(checks)} constants verified"


@test
def a_and_c_normalisation_constants_hold():
    """The two numbers that put both curves through 0 dB at 1 kHz."""
    f = 1000.0
    ra = (12194.0 ** 2 * f ** 4) / ((f ** 2 + 20.6 ** 2)
                                    * math.sqrt((f ** 2 + 107.7 ** 2) * (f ** 2 + 737.9 ** 2))
                                    * (f ** 2 + 12194.0 ** 2))
    rc = (12194.0 ** 2 * f ** 2) / ((f ** 2 + 20.6 ** 2) * (f ** 2 + 12194.0 ** 2))
    close((1 / ra) ** 2, 1.584841544872967, 1e-12, "A normalisation squared")
    close((1 / rc) ** 2, 1.0143560601767088, 1e-12, "C normalisation squared")
    contains("sound-level-meter", "1.584841544872967", "A normalisation")
    contains("sound-level-meter", "1.0143560601767088", "C normalisation")
    return "both derived from the pole definitions"


# ==========================================================================
# Frequency bin arithmetic
# ==========================================================================
@test
def frequency_bin_indices_land_on_the_right_bin():
    """Every band-limited search converts Hz to a bin index. Off by one here
    and the band quietly shifts."""
    expr = formula_for(path("ultrasonic-leak"), "iLow")
    for rate, n, f in ((48000.0, 8192.0, 15000.0), (44100.0, 8192.0, 15000.0),
                       (48000.0, 8192.0, 1000.0)):
        idx = evaluate(expr, f, n, rate)
        # halfF starts at bin 1, so index i in halfF is FFT bin i+1
        close((idx + 1) * rate / n, f, rate / n, f"{f} Hz at {rate} Hz sampling")
    return "bin centre within one bin width at 44.1 and 48 kHz"


@test
def the_leak_band_cannot_run_past_nyquist():
    """At 44.1 kHz a 22 kHz limit is only just inside the spectrum. The clamp
    has to hold, or the subrange reads past the end of the buffer."""
    expr = formula_for(path("ultrasonic-leak"), "iHigh")
    for rate in (44100.0, 48000.0):
        n, nhalf = 8192.0, 4096.0
        idx = evaluate(expr, 22000.0, n, rate, nhalf)
        if not 2 <= idx <= nhalf - 2:
            raise AssertionError(f"index {idx} outside the buffer at {rate} Hz")
        huge = evaluate(expr, 96000.0, n, rate, nhalf)
        close(huge, nhalf - 2, 0, f"absurd upper limit clamps at {rate} Hz")
    return "clamped at both sample rates"


@test
def disk_spindle_tones_match_the_verdict_thresholds():
    """The rack signature names disk speeds from a tone. The named speeds must
    fall inside the bands the file maps them to."""
    bands = [(70, 100, 5400), (100, 135, 7200), (135, 200, 10000), (200, 280, 15000)]
    src = source("rack-signature")
    for lo, hi, rpm in bands:
        hz = rpm / 60.0
        if not lo < hz < hi:
            raise AssertionError(f"{rpm} rpm is {hz:.1f} Hz, outside its {lo}-{hi} band")
        if f'"{hi}"' not in src:
            raise AssertionError(f"the {lo}-{hi} band is no longer in the file")
    close(7200 / 60.0, 120.0, 1e-12, "7200 rpm")
    close(5400 / 60.0, 90.0, 1e-12, "5400 rpm")
    return "90, 120, 167 and 250 Hz all inside their bands"


# ==========================================================================
# Ring buffer semantics - the bug class that shipped
# ==========================================================================
@test
def appending_a_short_array_to_a_ring_corrupts_it():
    """Documents why every array output now clears first. If this ever stops
    being true, the linter rule can be relaxed - until then it must not be."""
    from collections import deque
    n = 1024
    values = [i * 0.1 for i in range(1, n)]      # n-1 values, as subrange gives

    ring = deque(maxlen=n)
    for _ in range(3):
        for v in values:
            ring.append(v)
    if list(ring)[0] == values[0]:
        raise AssertionError("expected the append pattern to misalign, but it did not")
    close(list(ring)[0], values[-1], 1e-12, "the stale value that wraps to the front")

    ring = deque(maxlen=n)
    for _ in range(3):
        ring.clear()
        for v in values:
            ring.append(v)
    close(list(ring)[0], values[0], 1e-12, "clearing first keeps the alignment")
    close(48000 / 8192, 5.859375, 1e-9, "one bin at 48 kHz, N=8192")
    return "one stale value shifts everything; 5.86 Hz per bin"


@test
def no_experiment_appends_an_array_to_a_comparable_ring():
    """The contract the linter enforces, asserted here too so the test suite
    fails on its own if someone loosens the linter."""
    import glob
    import xml.etree.ElementTree as ET
    offenders = []
    for p in sorted(glob.glob(os.path.join(EXP, "*.phyphox"))):
        root = ET.parse(p).getroot()
        sizes = {(c.text or "").strip(): c.get("size", "1")
                 for c in root.findall("./data-containers/container")}

        def sz(v):
            v = int(v)
            return 10 ** 9 if v == 0 else v

        ana = root.find("./analysis")
        for mod in (ana if ana is not None else []):
            if mod.tag is ET.Comment:
                continue
            ins = [(i.text or "").strip() for i in mod.findall("./input")
                   if i.get("type") not in ("value", "empty")]
            widest = max([sz(sizes.get(x, "1")) for x in ins] or [1])
            for o in mod.findall("./output"):
                dest = sz(sizes.get((o.text or "").strip(), "1"))
                if o.get("clear") == "false" and 1 < dest < 10 ** 9 and widest >= dest:
                    offenders.append(f"{os.path.basename(p)}:{(o.text or '').strip()}")
    if offenders:
        raise AssertionError("array appended to a ring in: " + ", ".join(offenders))
    return "all 16 files clean"


# ==========================================================================
# Cadence and step counting
# ==========================================================================
@test
def step_count_error_matches_what_the_file_admits():
    """The walk logger says the step count is about 5 % out at 100 Hz and 20 %
    at 400 Hz. That comes from the spectrum's frequency resolution."""
    n = 1024
    for rate, want in ((100, 2.44), (200, 4.88), (400, 9.77)):
        err = 100 * (rate / n) / 2 / 2.0     # half a bin, against 2 steps/s
        close(err, want, 0.05, f"cadence error at {rate} Hz")
    contains("walk-logger", "1024", "the cadence window length")
    contains("walk-logger", "2.5 percent", "the corrected error figure")
    return "2.4 % at 100 Hz, 9.8 % at 400 Hz"



@test
def peak_level_and_clipping_threshold_are_right():
    """The peak reading is 20*log10 of the largest sample, so full scale is
    0 dBFS and the clipping warning sits just below the rail. This chain was
    untested until a deliberate-breakage run walked straight past it."""
    p = path("sound-level-meter")
    sq = formula_for(p, "peakSq")
    to_db = formula_for(p, "peakRawHist")
    for amp, want in ((1.0, 0.0), (0.5, -6.0206), (0.1, -20.0), (0.01, -40.0)):
        db = evaluate(to_db, math.log(evaluate(sq, amp)))
        close(db, want, 0.001, f"peak level at amplitude {amp}")
    close(10 ** (-0.05 / 20), 0.99426, 1e-4, "-0.05 dBFS as an amplitude")
    contains("sound-level-meter", 'min="-0.05"', "the clipping threshold")
    close(evaluate(to_db, math.log(evaluate(sq, 0.0))), -120.0, 0.01, "silence floor")
    return "0 dBFS full scale, -6.02 at half, floor at -120"


@test
def tile_tap_percentage_is_a_true_relative_difference():
    """A tile ringing 30 % below the reference must report -30."""
    expr = formula_for(path("tile-tap"), "percent")
    ratio = formula_for(path("tile-tap"), "ratio")
    for ring, ref, want in ((350.0, 350.0, 0.0), (245.0, 350.0, -30.0),
                            (308.0, 350.0, -12.0), (420.0, 350.0, 20.0)):
        close(evaluate(expr, evaluate(ratio, ring, ref)), want, 1e-9,
              f"{ring} Hz against {ref} Hz")
    contains("tile-tap", 'max="-30"', "the 30 % verdict threshold")
    return "-30 % reported as -30, thresholds consistent"


@test
def ultrasonic_ratio_is_a_power_ratio_in_db():
    """The leak number is 10*log10 of a power ratio, so a band holding a tenth
    of the energy reads -10 dB. Using 20*log10 here would double every reading
    and quietly wreck the verdict bands."""
    p = path("ultrasonic-leak")
    ratio = formula_for(p, "ratio")
    to_db = formula_for(p, "ratioDb")
    for band, total, want in ((1.0, 10.0, -10.0), (1.0, 100.0, -20.0),
                              (1.0, 1.0, 0.0), (1.0, 2.0, -3.0103)):
        close(evaluate(to_db, math.log(evaluate(ratio, band, total))), want, 1e-3,
              f"band {band} of total {total}")
    return "a tenth of the energy reads -10 dB"



@test
def inclination_angle_is_reported_in_degrees():
    """Field along gravity is 0 degrees, across it 90, opposed 180. The
    radians-to-degrees constant was mutated and no test noticed, because
    orientation invariance holds whatever the scale factor is."""
    p = path("magnetic-fingerprint")
    cos_e = formula_for(p, "cosAng")
    ang_e = formula_for(p, "incAng")
    for cos_val, want in ((1.0, 0.0), (0.0, 90.0), (-1.0, 180.0), (0.5, 60.0)):
        close(evaluate(ang_e, cos_val), want, 1e-6, f"cos {cos_val}")
    # and end to end, from real vectors
    g = [0.0, 0.0, -9.81]
    for B, want in (([0.0, 0.0, -50.0], 0.0), ([50.0, 0.0, 0.0], 90.0),
                    ([0.0, 0.0, 50.0], 180.0)):
        bmag = evaluate(formula_for(p, "bMag"), *B)
        gmag = evaluate(formula_for(p, "gMag"), *g)
        dot = evaluate(formula_for(p, "dot"), B[0], B[1], B[2], g[0], g[1], g[2])
        close(evaluate(ang_e, evaluate(cos_e, dot, bmag, gmag)), want, 1e-6,
              f"field {B}")
    return "0, 60, 90 and 180 degrees all exact"


# --------------------------------------------------------------------------
if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    passed = failed = 0
    for fn in TESTS:
        if only and only not in fn.__name__:
            continue
        try:
            note = fn()
            passed += 1
            print(f"  pass  {fn.__name__}" + (f"  ({note})" if note else ""))
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}\n          {exc}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
