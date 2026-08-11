#!/usr/bin/env python3
"""What NoiseCapture's open data can and cannot tell us about phone calibration.

THE PLAN THIS WAS WRITTEN FOR DID NOT SURVIVE CONTACT WITH THE DATA.

The idea was good: NoiseCapture is a crowd-sourced noise app whose database is
published openly, and its documentation lists device_manufacturer, device_model
and gain_calibration among the fields. Group by model, take the median gain, and
you would have a lookup table - your phone model, your calibration offset, no
reference meter needed.

The published dumps do not contain the device fields. Checked across Andorra,
Luxembourg, Malta, Iceland and Estonia: every track carries gain_calibration but
no manufacturer and no model. That is almost certainly deliberate - a device
model attached to a GPS track is identifying - and the documentation is
describing the internal schema rather than the export.

So a per-model table cannot be built from this source. Run this script and it
will show you that itself rather than asking you to take my word for it.

What the data DOES still answer, and the reason this script survives: how big are
the calibration offsets people actually enter? That bounds how much the phone
model can possibly matter, which is the question underneath the whole idea.

    python3 tools/noise_offsets.py                # default sample
    python3 tools/noise_offsets.py --countries Ireland Denmark
    python3 tools/noise_offsets.py --show-fields  # prove the model field is absent

Data: https://data.noise-planet.org/dump/  (ODbL licence)
Uses HTTP byte ranges to read one small file out of each zip - the dumps run to
a gigabyte and we need a few hundred kB of each.
"""
import argparse
import io
import json
import subprocess
import sys
import zipfile

BASE = "https://data.noise-planet.org/dump"

# Moderate-sized dumps with real usage. Deliberately not France or the US: those
# are hundreds of megabytes to a gigabyte, and the answer does not change.
DEFAULT = ["Luxembourg", "Estonia", "Iceland", "Malta", "Slovenia", "Croatia",
           "Lithuania", "Latvia"]

DEVICE_HINTS = ("device", "model", "manufact", "product", "brand")


def curl(args, tries=4):
    last = None
    for i in range(tries):
        r = subprocess.run(["curl", "-sS", "--fail", "--max-time", "300"] + args,
                           capture_output=True)
        if not r.returncode:
            return r.stdout
        last = r.stderr.decode(errors="replace")[:200]
    raise RuntimeError(last or "curl failed")


class HttpFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests."""

    def __init__(self, url):
        self.url = url
        head = curl(["-I", url]).decode(errors="replace")
        self.size = next((int(l.split(":", 1)[1]) for l in head.splitlines()
                          if l.lower().startswith("content-length:")), None)
        if self.size is None:
            raise RuntimeError(f"no content-length for {url}")
        if "accept-ranges: bytes" not in head.lower():
            raise RuntimeError(f"{url} will not serve byte ranges")
        self.pos = 0
        self.fetched = 0

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, off, whence=0):
        self.pos = (off if whence == 0 else
                    self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def read(self, n=-1):
        if n < 0 or self.pos + n > self.size:
            n = self.size - self.pos
        if n <= 0:
            return b""
        data = curl(["-r", f"{self.pos}-{self.pos + n - 1}", self.url])
        self.pos += len(data)
        self.fetched += len(data)
        return data


def tracks(country):
    """Yield the properties of every track in one country's dump."""
    f = HttpFile(f"{BASE}/{country.replace(' ', '%20')}.zip")
    z = zipfile.ZipFile(f)
    for name in z.namelist():
        if "tracks.geojson" not in name:
            continue
        for feat in json.loads(z.read(name)).get("features", []):
            yield feat.get("properties", {})
    return


def median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def percentile(xs, p):
    s = sorted(xs)
    if not s:
        return float("nan")
    k = (len(s) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--countries", nargs="+", default=DEFAULT)
    ap.add_argument("--show-fields", action="store_true",
                    help="list every field present, to check for device model")
    args = ap.parse_args()

    gains, fields, total, failed = [], set(), 0, []
    for c in args.countries:
        try:
            n = 0
            for p in tracks(c):
                fields.update(p.keys())
                n += 1
                g = p.get("gain_calibration")
                if isinstance(g, (int, float)):
                    gains.append(float(g))
            total += n
            print(f"  {c:14s} {n:6d} tracks", file=sys.stderr)
        except Exception as e:
            failed.append(c)
            print(f"  {c:14s} FAILED  {e}", file=sys.stderr)

    if not total:
        sys.exit("no data retrieved - check the network and try again")

    print(f"\n{total} tracks from {len(args.countries) - len(failed)} countries")
    if failed:
        print(f"(could not fetch: {', '.join(failed)})")

    device = sorted(f for f in fields
                    if any(h in f.lower() for h in DEVICE_HINTS))
    print("\n--- is the phone model in this data? ---")
    if device:
        print(f"YES - device fields present: {device}")
        print("A per-model table IS buildable. This script needs extending.")
    else:
        print("NO. Not one device or model field in any track.")
        print("A per-model calibration table cannot be built from this source,")
        print("whatever the documentation says the schema contains.")
    if args.show_fields:
        print(f"\nevery field seen: {sorted(fields)}")

    nonzero = [g for g in gains if abs(g) > 0.005]
    print("\n--- calibration offsets people actually entered ---")
    print(f"tracks with a gain value : {len(gains)}")
    print(f"left at zero (never calibrated): {len(gains) - len(nonzero)}"
          f"  ({100 * (len(gains) - len(nonzero)) / max(len(gains), 1):.0f}%)")
    if not nonzero:
        print("no calibrated tracks in this sample - widen --countries")
        return
    print(f"actually calibrated      : {len(nonzero)}")
    print(f"  median                 : {median(nonzero):+.1f} dB")
    print(f"  middle half (25-75%)   : {percentile(nonzero, 25):+.1f} "
          f"to {percentile(nonzero, 75):+.1f} dB")
    print(f"  5th - 95th percentile  : {percentile(nonzero, 5):+.1f} "
          f"to {percentile(nonzero, 95):+.1f} dB")
    print(f"  full range             : {min(nonzero):+.1f} to {max(nonzero):+.1f} dB")

    spread = percentile(nonzero, 95) - percentile(nonzero, 5)
    print(f"\nSpread across the middle 90%: {spread:.1f} dB.")
    print("That is an UPPER bound on how much the phone model matters - it also")
    print("contains differences in user technique, reference meter quality and")
    print("outright mistakes. The real per-model spread is smaller than this.")
    print("\nAnd it is NoiseCapture's offset, not phyphox's: the two apps have")
    print("different audio pipelines, so these numbers do not transfer into the")
    print("sound level meter here. They size the problem; they do not solve it.")


if __name__ == "__main__":
    main()
