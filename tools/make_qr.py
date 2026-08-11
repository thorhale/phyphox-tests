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
import zipfile

try:
    import segno
except ImportError:
    sys.exit("needs segno:  pip install segno")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Every experiment in one archive, so a single QR installs the lot. phyphox
# lists every .phyphox file it finds inside a zip and asks which to add - so
# this is one scan instead of sixteen. The files must sit flat in the zip; put
# them in folders and phyphox will not find them.
#
# The other reason to do it this way: the QR points at the zip, not at any
# individual experiment. Update the zip and everyone who already has the code
# gets the new versions. The printed code never goes stale.
BUNDLES = {"all-tests.zip": "experiments", "probes.zip": "probes"}

# Fixed timestamp so rebuilding an unchanged bundle produces an identical file.
# Otherwise every run rewrites the zip and git sees a change that isn't one.
ZIP_EPOCH = (2026, 1, 1, 0, 0, 0)


def build_bundles(out_dir):
    made = []
    for zipname, folder in BUNDLES.items():
        src = sorted(glob.glob(os.path.join(ROOT, folder, "*.phyphox")))
        if not src:
            continue
        path = os.path.join(out_dir, zipname)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for p in src:
                info = zipfile.ZipInfo(os.path.basename(p), date_time=ZIP_EPOCH)
                info.compress_type = zipfile.ZIP_DEFLATED
                with open(p, "rb") as fh:
                    z.writestr(info, fh.read())
        made.append((zipname, folder, len(src), os.path.getsize(path)))
    return made


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
    out_dir = os.path.dirname(args.out) or ROOT
    bundles = build_bundles(out_dir)

    def qr_for(url, scale=6):
        return segno.make(url, error="m").svg_inline(scale=scale, dark="#111")

    bundle_url = f"{base}/all-tests.zip"
    bundle_svg = qr_for(bundle_url, scale=7)
    bundle_n = next((n for z, _, n, _ in bundles if z == "all-tests.zip"), 0)

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
 .all {{ display: flex; gap: 1.5rem; align-items: flex-start; border: 2px solid #e8871a;
         border-radius: 10px; padding: 1.2rem; margin: 1.5rem 0; max-width: 46rem;
         background: #fffaf4; }}
 .all .qr {{ flex: 0 0 auto; }}
 .alltext p {{ line-height: 1.5; margin: .5rem 0; }}
 @media print {{ .card {{ break-inside: avoid; }} }}
</style>

<h1>Install these phyphox experiments</h1>
<p class="lead">In phyphox, press <b>+</b> then <b>Add experiment from QR code</b>,
and point the phone at one of these. Scanning from a screen works fine.</p>

<div class="all">
  <div class="qr">{bundle_svg}</div>
  <div class="alltext">
    <h2 style="margin-top:0;border:0">Scan this one to get all {bundle_n} at once</h2>
    <p>This code points at a zip holding every experiment. phyphox opens it,
    lists what's inside, and lets you add them in one go &mdash; one scan
    instead of {bundle_n}.</p>
    <p><b>It also never goes out of date.</b> The code points at the zip rather
    than at any single experiment, so when the zip is updated this same code
    hands out the new versions. Print it once and it keeps working.</p>
    <p class="url">{bundle_url}</p>
  </div>
</div>

<p class="lead">The individual codes below are only needed if you want one
specific test, or if the bundle fails to download.</p>

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

    # A page of tappable phyphox:// links, for installing from the phone alone.
    # Typing a phyphox:// address into Chrome makes it SEARCH for the text
    # instead of opening it - the scheme only works when a link is tapped.
    rows = []
    for folder, name, title, _url, _svg in cards:
        raw = f"{base}/{folder}/{name}.phyphox"
        deep = raw.replace("https://", "phyphox://").replace("http://", "phyphox://")
        rows.append(f'''<a class="btn" href="{deep}">{title}
  <span class="sub">{name}.phyphox</span></a>''')

    links_html = f'''<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Install phyphox experiments</title>
<style>
 body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1rem;
        background: #111; color: #eee; }}
 h1 {{ font-size: 1.3rem; }}
 h2 {{ font-size: 1rem; color: #e8871a; margin-top: 1.8rem;
       border-bottom: 1px solid #333; padding-bottom: .4rem; }}
 p {{ line-height: 1.5; color: #bbb; font-size: .9rem; }}
 .btn {{ display: block; background: #1e1e1e; border: 1px solid #444;
         border-radius: 10px; padding: 1rem; margin: .6rem 0; color: #fff;
         text-decoration: none; font-size: 1rem; }}
 .btn:active {{ background: #2a2a2a; }}
 .sub {{ display: block; font-size: .72rem; color: #888; margin-top: .25rem;
         font-family: ui-monospace, monospace; }}
 .big {{ background: #e8871a; border-color: #e8871a; color: #111; font-weight: 700;
         font-size: 1.15rem; }}
 .big .sub {{ color: #4a2c00; font-family: inherit; font-weight: 400; }}
</style>
<h1>Tap to install</h1>
<p>Each button hands the experiment straight to phyphox. If nothing happens when
you tap, phyphox is not registered for these links on your phone — use the QR
sheet instead.</p>

<a class="btn big" href="{bundle_url.replace('https://', 'phyphox://')}">Install all {bundle_n} experiments
  <span class="sub">one tap — phyphox lists them and you add the lot</span></a>
<p style="font-size:.8rem">That points at a zip of everything. If your phone
refuses to open a zip through the <code>phyphox://</code> link, use the plain
download below and open it with phyphox, or scan the bundle QR code instead.</p>
<a class="btn" href="{bundle_url}">Download the bundle as a normal file
  <span class="sub">all-tests.zip</span></a>

<h2>Or one at a time</h2>
{"".join(rows[len(probes):])}

<h2>Probes — diagnostics, only if something breaks</h2>
<p>You do not need these to use the tests. Install them in order only when
something is not working; the first that fails names the problem.</p>
{"".join(rows[:len(probes)])}
'''
    links_path = os.path.join(os.path.dirname(args.out), "open.html")
    with open(links_path, "w") as fh:
        fh.write(links_html)
    print(f"tappable links -> {links_path}")

    for zipname, folder, n, size in bundles:
        print(f"bundle -> {zipname}  ({n} from {folder}/, {size / 1024:.0f} kB)")
    print(f"{len(cards)} codes -> {args.out}")
    print(f"base URL: {base}")
    print("COMMIT all-tests.zip - the bundle QR is useless until it is online.")
    print("Open that file and scan from the screen. If phyphox reports an error,")
    print("check the URL loads in a browser with no login - that is the usual cause.")


if __name__ == "__main__":
    main()
