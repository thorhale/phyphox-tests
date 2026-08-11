#!/usr/bin/env python3
"""Paint a WiFi survey onto the floor: coverage, interference, and net quality.

This is the troubleshooting map. Feed it the survey (tools/wifi_merge.py output)
and a positions file that says where on the floor each waypoint was, and it draws
a cell for every spot you measured:

  * COVERAGE  - how strong one access point is (find dead zones)
  * INTERFERENCE - how much competing signal sits on overlapping channels
  * QUALITY   - coverage minus interference: where WiFi will actually struggle,
                which is not always where the signal is weakest

and, for each measured spot, it NAMES the single loudest competing network - so
you know exactly which access point to go move to another channel.

    python3 tools/wifi_map.py survey.csv positions.csv -o map.html

NOTHING ON THIS MAP IS GUESSED. Every coloured cell is a real reading taken at
that spot. The blank floor between cells was not measured and is left blank - it
is not interpolated, shaded, or filled in. Want more detail in a corner? Walk it
and mark more waypoints there. The only way to know the signal somewhere is to
measure it there.

The positions file is a tiny CSV, one row per waypoint:

    waypoint,x,y
    1,0,0
    2,5,0
    3,10,0

x and y are in metres on a floor grid you choose. In a data hall the aisles ARE a
grid, so "aisle 2, third rack" is already a coordinate. Run with no positions file
and it prints a blank template listing your waypoints to fill in.

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
    (40/80 MHz bonding is not modelled)."""
    if ch_a is None or ch_b is None:
        return False
    if band == "2.4":
        return abs(ch_a - ch_b) <= 4
    return abs(ch_a - ch_b) < 2


def dbm_to_mw(d):
    return 10.0 ** (d / 10.0)


def mw_to_dbm(m):
    return 10.0 * math.log10(m) if m > 1e-12 else None


def colour(t):
    """t in 0..1 -> red(0) .. yellow(.5) .. green(1)."""
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        r, g = 255, int(510 * t)
    else:
        r, g = int(255 * (2 - 2 * t)), 200
    return f"#{r:02x}{g:02x}40"


def esc(v):
    return html.escape("" if v is None else str(v))


def coverage_by_wp(rows, bssid):
    out = {}
    for r in rows:
        if (r.get("bssid") or "").lower() != bssid:
            continue
        w = (r.get("waypoint") or "").strip()
        s = fnum(r.get("rssi_dbm"))
        if w and s is not None and (w not in out or s > out[w]):
            out[w] = s
    return out


def target_ap(rows):
    """The access point seen at the most waypoints - usually the one you own."""
    seen = {}
    for r in rows:
        b = (r.get("bssid") or "").lower()
        w = (r.get("waypoint") or "").strip()
        if b and w:
            seen.setdefault(b, set()).add(w)
    if not seen:
        sys.exit("no access points with a bssid in the survey")
    b = max(seen, key=lambda k: len(seen[k]))
    row = next(r for r in rows if (r.get("bssid") or "").lower() == b)
    chan = fnum(row.get("channel"))
    return b, row.get("ssid") or b, chan, band_of(row.get("freq_mhz"), chan)


def interferers_by_wp(rows, target_b, band, chan):
    """waypoint -> (total interference dBm, [(ssid, channel, rssi), ...] worst first)
    from OTHER access points on overlapping channels. Pure measurement."""
    per = {}
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
        rc = fnum(r.get("channel"))
        if not overlaps(band, chan, rc):
            continue
        # keep the strongest reading per interfering BSSID at this waypoint
        d = per.setdefault(w, {})
        if b not in d or s > d[b][2]:
            d[b] = (r.get("ssid") or "(hidden)", rc, s)
    out = {}
    for w, d in per.items():
        contributors = sorted(d.values(), key=lambda t: -t[2])
        total = mw_to_dbm(sum(dbm_to_mw(s) for _, _, s in contributors))
        out[w] = (total, contributors)
    return out


def measured_map(values, positions, lo, hi, title, note, unit=""):
    """A cell for each MEASURED waypoint, coloured by its real value. No fill
    between cells - unmeasured floor stays blank."""
    pts = [(positions[w][0], positions[w][1], w, values[w])
           for w in values if w in positions and values[w] is not None]
    if not pts:
        return f'<div class="panel"><h3>{esc(title)}</h3><p class="note">no positioned readings</p></div>'
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    # cell side = median nearest-neighbour spacing, so a grid tiles and gaps show
    nn = []
    for i, (x, y, _, _) in enumerate(pts):
        others = [math.hypot(x - px, y - py) for j, (px, py, _, _) in enumerate(pts) if j != i]
        nn.append(min(others) if others else 1.0)
    side = sorted(nn)[len(nn) // 2] if nn else 1.0
    minx, maxx = min(xs) - side, max(xs) + side
    miny, maxy = min(ys) - side, max(ys) + side
    W, H = 460, 330
    def sx(x): return (x - minx) / (maxx - minx) * W
    def sy(y): return H - (y - miny) / (maxy - miny) * H
    cw = side / (maxx - minx) * W
    ch = side / (maxy - miny) * H
    parts = [f'<rect width="{W}" height="{H}" fill="#161b22"/>']
    for x, y, w, v in pts:
        t = (v - lo) / (hi - lo) if hi > lo else 0.5
        cx, cy = sx(x), sy(y)
        parts.append(f'<rect x="{cx - cw / 2:.0f}" y="{cy - ch / 2:.0f}" width="{cw:.0f}" '
                     f'height="{ch:.0f}" fill="{colour(t)}" stroke="#0d1117" stroke-width="1"/>')
        parts.append(f'<text x="{cx:.0f}" y="{cy + 4:.0f}" text-anchor="middle" '
                     f'font-size="12" font-weight="700" fill="#0d1117">{v:.0f}</text>')
        parts.append(f'<text x="{cx:.0f}" y="{cy - ch / 2 + 11:.0f}" text-anchor="middle" '
                     f'font-size="8" fill="#0d1117">wp {esc(w)}</text>')
    return (f'<div class="panel"><h3>{esc(title)}</h3><p class="note">{esc(note)}</p>'
            f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px">'
            + "".join(parts) + f'</svg><p class="unit">{esc(unit)}</p></div>')


PAGE = """<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
 body{{font-family:system-ui,sans-serif;margin:0;padding:1.2rem;background:#0d1117;
      color:#e6edf3;max-width:66rem;margin:auto}}
 h1{{font-size:1.5rem}} h2{{margin-top:1.5rem;font-size:1.15rem}}
 h3{{color:#58a6ff;font-size:1rem;margin:.2rem 0}}
 .lead,.note{{color:#8b949e;line-height:1.5;font-size:.88rem}}
 .note{{font-size:.8rem;margin:.2rem 0 .4rem}} .unit{{color:#8b949e;font-size:.72rem;margin:.2rem 0 0}}
 .grid{{display:flex;flex-wrap:wrap;gap:1.2rem}} .panel{{flex:1;min-width:300px}}
 .legend{{display:flex;gap:.4rem;align-items:center;font-size:.8rem;color:#8b949e;margin:.5rem 0}}
 .swatch{{height:.8rem;width:9rem;border-radius:3px;
          background:linear-gradient(90deg,#ff4040,#ffff40,#40c840)}}
 table{{border-collapse:collapse;width:100%;font-size:.85rem;margin:.5rem 0}}
 th{{text-align:left;color:#8b949e;padding:.35rem .5rem;border-bottom:1px solid #30363d}}
 td{{padding:.35rem .5rem;border-bottom:1px solid #21262d}} .r{{text-align:right;white-space:nowrap}}
 .honest{{background:#132019;border-left:3px solid #3fb950;padding:.6rem .9rem;
          border-radius:4px;font-size:.85rem;line-height:1.5;margin:1rem 0}}
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
              "pass it as the second argument:\n\nwaypoint,x,y")
        for w in wps:
            print(f"{w},,")
        return

    positions = read_positions(args.positions)
    if not positions:
        sys.exit(f"{args.positions}: no usable waypoint,x,y rows")

    if args.bssid:
        tb = args.bssid.lower()
        row = next((r for r in rows if (r.get("bssid") or "").lower() == tb), None)
        if not row:
            sys.exit(f"{args.bssid}: not in the survey")
        chan = fnum(row.get("channel"))
        ssid, band = row.get("ssid") or tb, band_of(row.get("freq_mhz"), chan)
    else:
        tb, ssid, chan, band = target_ap(rows)

    cov = coverage_by_wp(rows, tb)
    itf = interferers_by_wp(rows, tb, band, chan)
    itf_total = {w: itf.get(w, (None, []))[0] for w in cov}
    quality = {w: (cov[w] - itf_total[w]) if itf_total.get(w) is not None else None
               for w in cov}

    body = []
    body.append(f"<h1>{esc(args.title)}</h1>")
    body.append(f'<p class="lead">Mapping <b>{esc(ssid)}</b> '
                f'(channel {esc(int(chan)) if chan else "?"}, {esc(band)} GHz) across '
                f"{len(cov)} measured spots. Green is good, red is trouble. Every "
                "number is a real reading taken at that spot.</p>")
    body.append('<div class="legend"><span>worse</span><span class="swatch"></span>'
                "<span>better</span></div>")
    body.append('<div class="grid">')
    body.append(measured_map(cov, positions, -85, -50,
                "Coverage", "How strong this network is. Red = weak, dead zones.",
                "signal in dBm (higher / greener = stronger)"))
    body.append(measured_map({w: v for w, v in itf_total.items() if v is not None},
                positions, -55, -90,
                "Interference", "Competing signal on clashing channels. Red = crowded.",
                "combined interference in dBm (lower / greener = quieter)"))
    body.append(measured_map({w: v for w, v in quality.items() if v is not None},
                positions, 0, 35,
                "Quality (signal minus interference)",
                "The real story. Red = where WiFi will actually struggle.",
                "signal-to-interference in dB (higher / greener = better)"))
    body.append("</div>")

    # ---- the named culprits ----
    body.append("<h2>Who to go re-channel</h2>")
    body.append('<p class="lead">At each spot, the single loudest network fighting '
                "yours on an overlapping channel. This is the one to move.</p>")
    body.append("<table><tr><th>Waypoint</th><th>Your signal</th>"
                "<th>Worst interferer</th><th>Its channel</th><th>Its signal</th>"
                "<th>Quality</th></tr>")
    for w in sorted(cov, key=lambda w: (quality.get(w) is None, quality.get(w) or 0)):
        contributors = itf.get(w, (None, []))[1]
        worst = contributors[0] if contributors else None
        q = quality.get(w)
        if worst:
            name = esc(worst[0])
            wch = esc(int(worst[1])) if worst[1] else "-"
            wsig = f"{worst[2]:.0f} dBm"
        else:
            name, wch, wsig = "none on an overlapping channel", "-", "-"
        qcell = f"{q:.0f} dB" if q is not None else "-"
        body.append(
            f"<tr><td>wp {esc(w)}</td><td class='r'>{cov[w]:.0f} dBm</td>"
            f"<td>{name}</td><td class='r'>{wch}</td><td class='r'>{wsig}</td>"
            f"<td class='r'>{qcell}</td></tr>")
    body.append("</table>")

    body.append('<div class="honest"><b>Nothing here is guessed.</b> Every coloured '
                "cell is a real reading taken at that spot, and the blank floor "
                "between cells was not measured - it is left blank rather than "
                "filled in. To see a corner in more detail, walk it and mark more "
                "waypoints. The only way to know the signal somewhere is to measure "
                "it there.</div>")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(PAGE.format(title=esc(args.title), body="\n".join(body)))
    print(f"mapped {ssid} across {len(cov)} measured spots -> {args.out}")


if __name__ == "__main__":
    main()
