#!/usr/bin/env python3
"""Paint a WiFi survey onto the floor: coverage, interference, and net quality.

This is the troubleshooting map. Feed it the survey (tools/wifi_merge.py output)
and a positions file that says where on the floor each waypoint was, and it draws:

  * COVERAGE  - how strong one access point is across the floor (find dead zones)
  * INTERFERENCE - how much competing signal sits on overlapping channels
                   (find where the air is crowded)
  * QUALITY   - coverage minus interference: the map that actually says where WiFi
                will struggle, which is not always where the signal is weakest

    python3 tools/wifi_map.py survey.csv positions.csv -o map.html

The positions file is a tiny CSV you fill in - one row per waypoint:

    waypoint,x,y
    1,0,0
    2,5,0
    3,10,0

x and y are in metres (or any unit) on a floor grid you choose. In a data hall the
aisles ARE a grid, so "aisle 2, third rack" is already a coordinate. Run with no
positions file and it prints a blank template listing your waypoints to fill in.

HONEST LIMIT baked into the page: between your waypoints the map is INTERPOLATED -
an educated guess. A wall the survey walked past but not through will not show as
the sharp signal drop it really is. Denser waypoints = a truer map. Treat a dead
zone on the map as a place to go stand and confirm, not as gospel.

No dependencies; self-contained SVG in one HTML file; runs in Pydroid too.
"""
import argparse
import csv
import html
import math
import sys


def fnum(v):
    try:
        return float(str(v).strip())
    except (ValueError, AttributeError, TypeError):
        return None


def read_survey(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_positions(path):
    pos = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            w = (r.get("waypoint") or "").strip()
            x, y = fnum(r.get("x")), fnum(r.get("y"))
            if w and x is not None and y is not None:
                pos[w] = (x, y)
    return pos


def band_of(freq, channel):
    f = fnum(freq)
    if f and 2400 <= f <= 2500:
        return "2.4"
    if f and 4900 <= f <= 5895:
        return "5"
    c = fnum(channel)
    if c and c <= 14:
        return "2.4"
    return "5"


def overlaps(band, ch_a, ch_b):
    """Do two channels in the same band interfere? 2.4 GHz 20 MHz channels are
    ~5 apart and 20 MHz wide, so anything within 4 channels overlaps. 5 GHz
    channels are laid out non-overlapping, so only the same channel collides
    (ignoring 40/80 MHz bonding, which this does not try to model)."""
    if ch_a is None or ch_b is None:
        return False
    if band == "2.4":
        return abs(ch_a - ch_b) <= 4
    return abs(ch_a - ch_b) < 2


def dbm_to_mw(d):
    return 10.0 ** (d / 10.0)


def mw_to_dbm(m):
    return 10.0 * math.log10(m) if m > 1e-12 else -120.0


def idw(points, x, y, power=2.0):
    """Inverse-distance-weighted value at (x,y) from [(px,py,val), ...]."""
    num = den = 0.0
    for px, py, v in points:
        d2 = (px - x) ** 2 + (py - y) ** 2
        if d2 < 1e-9:
            return v
        w = 1.0 / d2 ** (power / 2.0)
        num += w * v
        den += w
    return num / den if den else None


def colour(t):
    """t in 0..1 -> red(0) .. yellow(0.5) .. green(1). Returns #rrggbb."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        r, g = 255, int(510 * t)
    else:
        r, g = int(255 * (2 - 2 * t)), 200
    return f"#{r:02x}{g:02x}40"


def heatmap_svg(points, positions, lo, hi, title, note, wp_labels=True):
    """One SVG heat panel. points = [(x,y,value)], value mapped lo..hi -> red..green."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if not xs:
        return f"<p>{esc(title)}: no positioned data</p>"
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    pad = max((maxx - minx), (maxy - miny), 1.0) * 0.15
    minx -= pad; maxx += pad; miny -= pad; maxy += pad
    W, H = 460, 340
    def sx(x): return (x - minx) / (maxx - minx) * W
    def sy(y): return H - (y - miny) / (maxy - miny) * H
    cell = 14
    cells = []
    for gy in range(0, H, cell):
        for gx in range(0, W, cell):
            wx = minx + (gx + cell / 2) / W * (maxx - minx)
            wy = miny + (H - (gy + cell / 2)) / H * (maxy - miny)
            v = idw(points, wx, wy)
            if v is None:
                continue
            t = (v - lo) / (hi - lo) if hi > lo else 0.5
            cells.append(f'<rect x="{gx}" y="{gy}" width="{cell}" height="{cell}" '
                         f'fill="{colour(t)}" opacity="0.85"/>')
    dots = []
    for w, (x, y) in positions.items():
        cx, cy = sx(x), sy(y)
        dots.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="4" fill="#0d1117" '
                    f'stroke="#fff" stroke-width="1.5"/>')
        if wp_labels:
            dots.append(f'<text x="{cx:.0f}" y="{cy - 7:.0f}" fill="#fff" '
                        f'font-size="11" text-anchor="middle">{esc(w)}</text>')
    return (f'<div class="panel"><h3>{esc(title)}</h3>'
            f'<p class="note">{esc(note)}</p>'
            f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px">'
            f'<rect width="{W}" height="{H}" fill="#161b22"/>'
            + "".join(cells) + "".join(dots) + "</svg></div>")


def esc(v):
    return html.escape("" if v is None else str(v))


def best_rows_by_wp(rows, bssid=None):
    """waypoint -> best rssi (for one bssid, or the strongest AP overall)."""
    out = {}
    for r in rows:
        if bssid and (r.get("bssid") or "").lower() != bssid:
            continue
        w = (r.get("waypoint") or "").strip()
        s = fnum(r.get("rssi_dbm"))
        if not w or s is None:
            continue
        if w not in out or s > out[w]:
            out[w] = s
    return out


def target_ap(rows):
    """Pick the access point seen at the most waypoints (usually your own)."""
    seen = {}
    for r in rows:
        b = (r.get("bssid") or "").lower()
        w = (r.get("waypoint") or "").strip()
        if b and w:
            seen.setdefault(b, set()).add(w)
    if not seen:
        sys.exit("no access points with a bssid in the survey")
    b = max(seen, key=lambda k: len(seen[k]))
    ssid = next((r.get("ssid") for r in rows if (r.get("bssid") or "").lower() == b), b)
    chan = next((fnum(r.get("channel")) for r in rows
                 if (r.get("bssid") or "").lower() == b), None)
    freq = next((r.get("freq_mhz") for r in rows
                 if (r.get("bssid") or "").lower() == b), None)
    return b, ssid, chan, band_of(freq, chan)


def interference_by_wp(rows, target_b, band, chan):
    """waypoint -> total interfering power (dBm) from OTHER APs on overlapping
    channels."""
    out = {}
    for r in rows:
        b = (r.get("bssid") or "").lower()
        if b == target_b:
            continue
        w = (r.get("waypoint") or "").strip()
        s = fnum(r.get("rssi_dbm"))
        if not (b and w and s is not None):
            continue
        if band_of(r.get("freq_mhz"), r.get("channel")) != band:
            continue
        if not overlaps(band, chan, fnum(r.get("channel"))):
            continue
        out.setdefault(w, 0.0)
        out[w] += dbm_to_mw(s)
    return {w: mw_to_dbm(p) for w, p in out.items()}


PAGE = """<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
 body{{font-family:system-ui,sans-serif;margin:0;padding:1.2rem;background:#0d1117;
      color:#e6edf3;max-width:64rem;margin:auto}}
 h1{{font-size:1.5rem}} h2{{margin-top:1.5rem;font-size:1.15rem}}
 h3{{color:#58a6ff;font-size:1rem;margin:.2rem 0}}
 .lead,.note{{color:#8b949e;line-height:1.5;font-size:.88rem}} .note{{font-size:.8rem;margin:.2rem 0 .5rem}}
 .grid{{display:flex;flex-wrap:wrap;gap:1.2rem}} .panel{{flex:1;min-width:300px}}
 .legend{{display:flex;gap:.4rem;align-items:center;font-size:.8rem;color:#8b949e;margin:.5rem 0}}
 .swatch{{height:.8rem;width:9rem;border-radius:3px;
          background:linear-gradient(90deg,#ff4040,#ffff40,#40c840)}}
 .warn{{background:#231a10;border-left:3px solid #d29922;padding:.6rem .9rem;
        border-radius:4px;font-size:.85rem;line-height:1.5;color:#e6edf3;margin:1rem 0}}
</style>
{body}
"""


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("survey")
    p.add_argument("positions", nargs="?", help="CSV: waypoint,x,y (metres)")
    p.add_argument("-o", "--out", default="map.html")
    p.add_argument("--bssid", help="access point to map (default: the one seen most)")
    p.add_argument("--title", default="WiFi coverage and interference map")
    args = p.parse_args()

    rows = read_survey(args.survey)

    if not args.positions:
        wps = sorted({(r.get("waypoint") or "").strip() for r in rows if r.get("waypoint")},
                     key=lambda w: (fnum(w) is None, fnum(w) or 0, w))
        print("No positions file given. Fill in this template (x,y in metres) and\n"
              "pass it as the second argument:\n")
        print("waypoint,x,y")
        for w in wps:
            print(f"{w},,")
        return

    positions = read_positions(args.positions)
    if not positions:
        sys.exit(f"{args.positions}: no usable waypoint,x,y rows")

    tb = args.bssid.lower() if args.bssid else None
    if tb:
        ssid = next((r.get("ssid") for r in rows if (r.get("bssid") or "").lower() == tb), tb)
        chan = next((fnum(r.get("channel")) for r in rows
                     if (r.get("bssid") or "").lower() == tb), None)
        band = band_of(next((r.get("freq_mhz") for r in rows
                             if (r.get("bssid") or "").lower() == tb), None), chan)
    else:
        tb, ssid, chan, band = target_ap(rows)

    cov = best_rows_by_wp(rows, tb)
    itf = interference_by_wp(rows, tb, band, chan)

    def pts(d):
        return [(positions[w][0], positions[w][1], v)
                for w, v in d.items() if w in positions]

    cov_pts = pts(cov)
    itf_pts = pts({w: itf.get(w, -120.0) for w in cov})     # 0 interference -> very low dBm
    qual_pts = [(x, y, cov[w] - itf.get(w, -120.0))
                for w in cov if w in positions
                for (x, y) in [positions[w]]]

    body = []
    body.append(f"<h1>{esc(args.title)}</h1>")
    body.append(f'<p class="lead">Mapping <b>{esc(ssid)}</b> '
                f'(channel {esc(int(chan)) if chan else "?"}, {esc(band)} GHz) across '
                f"{len(positions)} waypoints. Green is good, red is trouble.</p>")
    body.append('<div class="legend"><span>worse</span><span class="swatch"></span>'
                "<span>better</span></div>")
    body.append('<div class="grid">')
    body.append(heatmap_svg(cov_pts, positions, -85, -50,
                "Coverage - signal strength",
                "How strong this access point is. Red = weak spots and dead zones."))
    body.append(heatmap_svg(
        [(x, y, -v) for (x, y, v) in itf_pts], positions, -(-55), -(-95),
        "Interference - crowding on overlapping channels",
        "Competing signal on channels that clash with this one. Red = crowded air."))
    body.append(heatmap_svg(qual_pts, positions, 0, 35,
                "Quality - signal minus interference",
                "The real story: high signal is no good if interference is just as high. "
                "Red = where WiFi will actually struggle."))
    body.append("</div>")
    body.append('<div class="warn"><b>Read the map honestly.</b> Between your '
                "waypoints the colours are interpolated - a guess drawn from the "
                "nearest points. A wall the survey walked past but not through will "
                "not show as the sharp drop it really is. The more waypoints you "
                "mark, the truer it gets. Treat a red zone as a place to go stand "
                "and confirm, not as proof.</div>")
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(PAGE.format(title=esc(args.title), body="\n".join(body)))
    print(f"mapped {ssid} across {len(positions)} waypoints -> {args.out}")


if __name__ == "__main__":
    main()
