#!/usr/bin/env python3
"""Generate QR codes that install these experiments.

Why this exists: phyphox's "+" menu offers only three ways in - QR code,
Bluetooth device, or a simple built-in experiment. There is no "open a file"
option. Sending yourself the .phyphox file and tapping it sometimes works and
sometimes does not, and phyphox's own documentation explains why: on Android the
file is identified by MIME type rather than by extension, and a .phyphox file
reports as an unknown type. So QR is the route that actually works.

The QR contains a URL. phyphox downloads the experiment from it, which means
THE FILES HAVE TO BE REACHABLE WITHOUT A LOGIN. A private GitHub repository will
not work - the phone gets a 404. Either make the repository public, or host the
experiments folder anywhere else that serves plain files.

    python3 tools/make_qr.py --base https://raw.githubusercontent.com/USER/REPO/main
    python3 tools/make_qr.py --base https://example.com/phyphox --out sheet.html

Produces a single self-contained HTML page: open it on a computer and scan the
codes from the screen with phyphox's own scanner.
"""
import argparse
import glob
import os
import sys

try:
    import segno
except ImportError:
    sys.exit("needs segno:  pip install segno")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def experiments():
    for folder in ("probes", "experiments"):
        d = os.path.join(ROOT, folder)
        if not os.path.isdir(d):
            continue
        for p in sorted(glob.glob(os.path.join(d, "*.phyphox"))):
            yield folder, os.path.basename(p)[:-8]


def title_of(folder, name):
    with open(os.path.join(ROOT, folder, name + ".phyphox")) as fh:
        for line in fh:
            if "<title>" in line:
                return line.split("<title>")[1].split("</title>")[0]
    return name


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True,
                    help="URL of the folder ABOVE experiments/ and probes/")
    ap.add_argument("--out", default=os.path.join(ROOT, "install.html"))
    ap.add_argument("--scheme", choices=("https", "phyphox"), default="https",
                    help="phyphox:// hands straight to the app; https lets the "
                         "scanner decide. Try https first.")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    cards = []
    for folder, name in experiments():
        url = f"{base}/{folder}/{name}.phyphox"
        if args.scheme == "phyphox":
            url = url.replace("https://", "phyphox://").replace("http://", "phyphox://")
        svg = segno.make(url, error="m").svg_inline(scale=4, dark="#111")
        cards.append((folder, name, title_of(folder, name), url, svg))

    probes = [c for c in cards if c[0] == "probes"]
    exps = [c for c in cards if c[0] == "experiments"]

    def block(items):
        out = []
        for _, name, title, url, svg in items:
            out.append(f'''<div class="card">
  <div class="qr">{svg}</div>
  <h3>{title}</h3>
  <p class="file">{name}.phyphox</p>
  <p class="url">{url}</p>
</div>''')
        return "\n".join(out)

    html = f'''<!doctype html>
<meta charset="utf-8">
<title>Install these phyphox experiments</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 60rem;
        background: #fff; color: #111; }}
 h1 {{ margin-bottom: .3rem; }}
 .lead {{ color: #444; max-width: 42rem; line-height: 1.5; }}
 .warn {{ background: #fff4e5; border-left: 4px solid #e8871a; padding: .8rem 1rem;
          margin: 1.2rem 0; max-width: 42rem; line-height: 1.5; }}
 h2 {{ margin-top: 2.5rem; border-bottom: 2px solid #eee; padding-bottom: .3rem; }}
 .grid {{ display: flex; flex-wrap: wrap; gap: 1.2rem; }}
 .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 1rem; width: 15rem;
          text-align: center; }}
 .card h3 {{ font-size: .95rem; margin: .6rem 0 .2rem; }}
 .file {{ font-family: ui-monospace, monospace; font-size: .75rem; color: #666;
          margin: 0; }}
 .url {{ font-size: .6rem; color: #999; word-break: break-all; margin: .4rem 0 0; }}
 @media print {{ .card {{ break-inside: avoid; }} }}
</style>

<h1>Install these phyphox experiments</h1>
<p class="lead">In phyphox, press <b>+</b> then <b>Add experiment from QR code</b>,
and point the phone at one of these. Scanning from a screen works fine.</p>

<div class="warn">
<b>These only work if the files are publicly reachable.</b> phyphox downloads the
experiment from the address in the code, with no login. If the repository is
private the phone just gets a 404 and the code appears broken. Make it public,
or host the files somewhere that serves them openly.
</div>

<h2>Start here: the probes</h2>
<p class="lead">Six diagnostics. Install them in order — the first that fails
names the problem. Probes 0 to 3 cover everything the rest depend on.</p>
<div class="grid">
{block(probes)}
</div>

<h2>The experiments</h2>
<p class="lead">Run <b>0. Device Check</b> first on any new phone: it reports
which of these that phone can actually run.</p>
<div class="grid">
{block(exps)}
</div>
'''
    with open(args.out, "w") as fh:
        fh.write(html)
    print(f"{len(cards)} codes -> {args.out}")
    print(f"base URL: {base}")
    print("Open that file and scan from the screen. If phyphox reports an error,")
    print("check the URL loads in a browser with no login - that is the usual cause.")


if __name__ == "__main__":
    main()
