#!/usr/bin/env python3
"""Turn a merged WiFi survey into a readable report - the detail WiFiAnalyzer
shows, but tied to the places you walked and saved as one page.

WiFiAnalyzer is live only: it shows you the room you are standing in and forgets
it the moment you move. This takes the survey.csv that tools/wifi_merge.py builds
(WiFiAnalyzer's per-access-point detail joined to your phyphox waypoints) and
writes a standalone HTML page:

  * every access point, with its vendor, band, channel, security, strongest
    signal and how many of your waypoints it reached
  * how crowded each channel is, and which are clearest - the Channel Rating view
  * per waypoint: what you could actually connect to there, strongest first

    python3 tools/wifi_report.py survey.csv -o survey.html

No dependencies, so it runs in Pydroid on the phone too. The page is
self-contained - open it in any browser, no internet needed.
"""
import argparse
import csv
import html
import sys


def read_survey(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit(f"{path}: no rows. Build it first with tools/wifi_merge.py")
    return rows


def fnum(v):
    try:
        return float(str(v).strip())
    except (ValueError, AttributeError):
        return None


def band_of(freq, channel):
    """2.4, 5 or 6 GHz from the frequency (falling back to the channel number)."""
    f = fnum(freq)
    if f:
        if 2400 <= f <= 2500:
            return "2.4 GHz"
        if 4900 <= f <= 5895:
            return "5 GHz"
        if 5925 <= f <= 7125:
            return "6 GHz"
    c = fnum(channel)
    if c:
        if c <= 14:
            return "2.4 GHz"
        if c <= 177:
            return "5 GHz"
        return "6 GHz"
    return "?"


def strongest(rows):
    """Best (least negative) rssi in a set of rows, and the row it came from."""
    best, r = None, None
    for row in rows:
        s = fnum(row.get("rssi_dbm"))
        if s is not None and (best is None or s > best):
            best, r = s, row
    return best, r


def bar(fraction, width=22, fill="#3fb950", back="#30363d"):
    """A text/CSS bar for the HTML - fraction 0..1."""
    pct = max(0.0, min(1.0, fraction)) * 100
    return (f'<span class="bar"><span class="fill" style="width:{pct:.0f}%;'
            f'background:{fill}"></span></span>')


def rssi_colour(s):
    if s is None:
        return "#8b949e"
    if s >= -60:
        return "#3fb950"      # strong
    if s >= -70:
        return "#d29922"      # ok
    if s >= -80:
        return "#db6d28"      # weak
    return "#f85149"          # barely there


def esc(v):
    return html.escape("" if v is None else str(v))


def build(rows, title):
    # ---- group by access point (BSSID) ----
    aps = {}
    for r in rows:
        b = (r.get("bssid") or "").strip().lower()
        if not b:
            continue
        aps.setdefault(b, []).append(r)

    ap_summ = []
    for b, rs in aps.items():
        best, br = strongest(rs)
        wps = sorted({r.get("waypoint") for r in rs if r.get("waypoint") not in (None, "")})
        ap_summ.append({
            "bssid": b,
            "ssid": (br or rs[0]).get("ssid") or "(hidden)",
            "vendor": (br or rs[0]).get("vendor") or "",
            "band": band_of((br or rs[0]).get("freq_mhz"), (br or rs[0]).get("channel")),
            "channel": (br or rs[0]).get("channel") or "?",
            "security": (br or rs[0]).get("security") or "",
            "best": best,
            "best_wp": (br or {}).get("waypoint"),
            "seen_wp": len(wps),
        })
    ap_summ.sort(key=lambda a: (a["best"] is None, -(a["best"] or -999)))

    # ---- channel occupancy (distinct APs per channel, per band) ----
    chan = {}
    for a in ap_summ:
        c = fnum(a["channel"])
        if c is None:
            continue
        chan.setdefault((a["band"], int(c)), set()).add(a["bssid"])
    occ = sorted(((band, c, len(s)) for (band, c), s in chan.items()),
                 key=lambda x: (x[0], x[1]))
    max_occ = max((n for _, _, n in occ), default=1)

    # ---- per waypoint ----
    by_wp = {}
    for r in rows:
        w = r.get("waypoint")
        if w in (None, ""):
            continue
        by_wp.setdefault(w, []).append(r)

    def wp_key(w):
        n = fnum(w)
        return (0, n) if n is not None else (1, str(w))

    # ================= HTML =================
    out = []
    out.append(f"<h1>{esc(title)}</h1>")
    bands = sorted({a["band"] for a in ap_summ})
    out.append('<div class="stats">')
    out.append(f'<div class="stat"><b>{len(ap_summ)}</b>access points</div>')
    out.append(f'<div class="stat"><b>{len(by_wp)}</b>waypoints</div>')
    out.append(f'<div class="stat"><b>{len(occ)}</b>channels in use</div>')
    out.append(f'<div class="stat"><b>{esc(", ".join(bands) or "?")}</b>bands</div>')
    out.append("</div>")

    # ---- channel occupancy ----
    out.append("<h2>Channel congestion</h2>")
    out.append('<p class="lead">How many access points sit on each channel. Fewer '
               "is better. On 2.4 GHz only 1, 6 and 11 truly avoid overlapping each "
               "other, so those are what matter most.</p>")
    for band in bands:
        band_occ = [(c, n) for bb, c, n in occ if bb == band]
        if not band_occ:
            continue
        out.append(f"<h3>{esc(band)}</h3><table class='chan'>")
        for c, n in band_occ:
            out.append(
                f"<tr><td class='r'>ch {c}</td><td>{bar(n / max_occ)}</td>"
                f"<td class='r'>{n} AP{'s' if n != 1 else ''}</td></tr>")
        out.append("</table>")
        if band == "2.4 GHz":
            best = sorted([(c, n) for c, n in band_occ if c in (1, 6, 11)],
                          key=lambda x: x[1])
            if best:
                names = ", ".join(f"ch {c} ({n})" for c, n in best)
                out.append(f"<p class='pick'>Clearest of the non-overlapping "
                           f"channels: <b>{esc(names)}</b></p>")

    # ---- access points ----
    out.append("<h2>Access points seen</h2>")
    out.append('<p class="lead">Every access point, strongest first. '
               '"Best signal" is the loudest it got anywhere on your walk; '
               '"waypoints" is how many of your marked spots it reached - a rough '
               "measure of how far its coverage spread.</p>")
    out.append("<table class='aps'><tr><th>Network</th><th>Vendor</th><th>Band</th>"
               "<th>Ch</th><th>Security</th><th>Best signal</th><th>At</th>"
               "<th>Waypoints</th></tr>")
    for a in ap_summ:
        col = rssi_colour(a["best"])
        sig = f"{a['best']:.0f} dBm" if a["best"] is not None else "-"
        out.append(
            f"<tr><td><b>{esc(a['ssid'])}</b><br><span class='mono'>{esc(a['bssid'])}</span></td>"
            f"<td>{esc(a['vendor'])}</td><td>{esc(a['band'])}</td>"
            f"<td class='r'>{esc(a['channel'])}</td><td>{esc(a['security'])}</td>"
            f"<td class='r' style='color:{col};font-weight:600'>{sig}</td>"
            f"<td class='r'>{esc(a['best_wp'])}</td><td class='r'>{a['seen_wp']}</td></tr>")
    out.append("</table>")

    # ---- per waypoint ----
    out.append("<h2>What you can reach at each spot</h2>")
    out.append('<p class="lead">At each waypoint, the access points in range, '
               "strongest first. This is the view WiFiAnalyzer cannot give you - "
               "it is tied to where you were standing.</p>")
    for w in sorted(by_wp, key=wp_key):
        seen = {}
        for r in by_wp[w]:
            b = (r.get("bssid") or "").lower()
            s = fnum(r.get("rssi_dbm"))
            if b and (b not in seen or (s is not None and s > (fnum(seen[b].get("rssi_dbm")) or -999))):
                seen[b] = r
        ranked = sorted(seen.values(),
                        key=lambda r: -(fnum(r.get("rssi_dbm")) or -999))
        out.append(f"<h3>Waypoint {esc(w)}</h3>")
        out.append("<table class='wp'><tr><th>Network</th><th>Band</th><th>Ch</th>"
                   "<th>Signal</th></tr>")
        for r in ranked:
            s = fnum(r.get("rssi_dbm"))
            col = rssi_colour(s)
            sig = f"{s:.0f} dBm" if s is not None else "-"
            out.append(
                f"<tr><td>{esc(r.get('ssid') or '(hidden)')}</td>"
                f"<td>{esc(band_of(r.get('freq_mhz'), r.get('channel')))}</td>"
                f"<td class='r'>{esc(r.get('channel'))}</td>"
                f"<td class='r' style='color:{col}'>{sig}</td></tr>")
        out.append("</table>")

    return "\n".join(out)


PAGE = """<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
 body{{font-family:system-ui,sans-serif;margin:0;padding:1.2rem;background:#0d1117;
      color:#e6edf3;max-width:60rem;margin:auto}}
 h1{{font-size:1.5rem}} h2{{margin-top:2rem;border-bottom:1px solid #30363d;
     padding-bottom:.3rem;font-size:1.2rem}} h3{{color:#58a6ff;font-size:1rem;margin:1rem 0 .3rem}}
 .lead{{color:#8b949e;line-height:1.5;font-size:.9rem}}
 .stats{{display:flex;flex-wrap:wrap;gap:.8rem;margin:1rem 0}}
 .stat{{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:.6rem 1rem;
        font-size:.8rem;color:#8b949e}} .stat b{{display:block;font-size:1.3rem;color:#e6edf3}}
 table{{border-collapse:collapse;width:100%;font-size:.85rem;margin:.4rem 0}}
 th{{text-align:left;color:#8b949e;font-weight:600;padding:.3rem .5rem;border-bottom:1px solid #30363d}}
 td{{padding:.35rem .5rem;border-bottom:1px solid #21262d;vertical-align:top}}
 .r{{text-align:right;white-space:nowrap}} .mono{{font-family:ui-monospace,monospace;
     font-size:.72rem;color:#8b949e}}
 .bar{{display:inline-block;width:12rem;height:.8rem;background:#30363d;border-radius:4px;
       overflow:hidden;vertical-align:middle}}
 .fill{{display:block;height:100%}}
 table.chan td{{border:0;padding:.15rem .5rem}}
 .pick{{color:#3fb950;font-size:.85rem;margin:.3rem 0 1rem}}
</style>
{body}
<p style="color:#484f58;font-size:.75rem;margin-top:2.5rem">Built by
tools/wifi_report.py from a phyphox + WiFiAnalyzer survey. Signal and distance are
from WiFiAnalyzer; the locations are your phyphox waypoints.</p>
"""


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("survey", help="survey.csv from tools/wifi_merge.py")
    p.add_argument("-o", "--out", default="survey.html")
    p.add_argument("--title", default="WiFi walk survey")
    args = p.parse_args()

    rows = read_survey(args.survey)
    body = build(rows, args.title)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(PAGE.format(title=html.escape(args.title), body=body))
    print(f"{len(rows)} readings -> {args.out}")
    print("Open it in any browser. It is self-contained.")


if __name__ == "__main__":
    main()
