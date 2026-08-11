# phyphox-tests

Custom experiments for the [phyphox](https://phyphox.org) phone app. They turn a
phone you already own into a set of measuring tools for a data hall (the big room
full of computer racks that a data centre is built around).

phyphox is a free app that lets you build your own experiments out of the phone's
sensors. These files are those experiments.

**Status on a real phone (Galaxy, Aug 2026):** there are six small check-up files
in the `probes/` folder. Numbers 0 to 4 passed; number 5 needs a version of
phyphox that isn't out yet. The `device-check` experiment runs and reports
correctly. The other 14 experiments have been checked by a script and the maths
has been proven, but they haven't each been tried in a real hall yet.

## Read this first

**[GUIDE.md](GUIDE.md)** — every test in plain English: what it does, why you'd
care, how to run it, and an honest verdict on whether it's worth your time. Not
all sixteen are equally good, and that page says so. It also has a **"Words this
uses"** section that explains every term one time — read that if any word here
stops you.

**[CALIBRATION.md](CALIBRATION.md)** — how to make the sound meter's single
number trustworthy, and why you probably don't need to bother.

The same plain-English explanations are now inside each experiment too. phyphox
shows the description when you open a test, and every test has a **Notes** tab.

## Start here

**Run `device-check` first on any new phone.** It switches on every sensor, sees
which ones actually answer, measures how fast each one really reports, and tells
you in plain words which of these tests that phone can run. Phones vary a lot, and
it's better to find out at your desk than halfway down an aisle.

### What one real phone reported

Here's what the first `device-check` run showed, as an example of what the
verdicts look like and why they matter. **"Hz" just means times per second.**

| Sensor | Result | What it means for these tests |
|---|---|---|
| Accelerometer (senses shaking) | 470.6 Hz | Can see shaking up to 235 times a second. Good — covers fan blades and the hum from mains power |
| Gyroscope (senses turning) | 470.6 Hz | Fine |
| Magnetometer (senses magnetic field) | 100.0 Hz | Only sees up to 50 times a second. Mains hum sits right at that edge — see the note below |
| Barometer (senses air pressure) | 12.5 Hz | Fine for `hall-survey` |
| Light, proximity | fitted, event-driven | These only report when the reading *changes*, so a low number is normal, not a fault |
| Ambient temperature | **not fitted** | Expected. Almost no phone has one. `hall-survey` lets you type it in |
| Humidity | **not fitted** | Same |
| Microphone | 48000 Hz | Everything that uses sound works |

The magnetometer line is the one worth reading twice. At 100 snapshots a second it
can't honestly measure the 50-or-60-times-a-second flip of mains power. So
`emi-survey` and `busway-load` can only *compare* — "this cable is busier than
that one" — not give you a real frequency. That limit was written into those files
before the phone confirmed it.

## The experiments

The **Tier** column says how fussy each test is about hardware. **Tier 0** runs on
anything, even a cheap phone or an iPhone — it needs only the sensors every phone
has. Higher tiers need extra hardware.

| File | What it does | Tier |
|---|---|---|
| `device-check` | What this phone has, how fast each sensor is, and how steady | 0 |
| `sound-level-meter` | How loud it is, in proper dB(A) — the standard loudness number | 0 |
| `emi-survey` | Finds live power cables, so you can keep network cable away from them | 0 |
| `busway-load` | Which power feed is working harder, without touching anything | 0 |
| `magnetic-fingerprint` | Find an exact spot again, using the building's steel as a map | 0 |
| `fan-tacho` | Fan speed, and whether a bearing is starting to fail | 0 |
| `vibration-census` | Which machines are actually running, from one floor recording | 0 |
| `strobe-tacho` | Fan speed read by eye with the torch — an honest check on `fan-tacho` | 3 |
| `tile-tap` | Finds loose floor tiles by the note they ring at | 0 |
| `acoustic-fingerprint` | Recognise a place by its echoes; how echoey the room is | 0 |
| `rack-signature` | Find the odd one out in a row of identical machines | 0 |
| `ultrasonic-leak` | Hunt air leaks by the high-pitched hiss they make | 0 |
| `dimension-survey` | Distances, air temperature from sound, and whether a floor is level | 0 |
| `walk-logger` | Records everything at once while you walk around | 0 |
| `wifi-walk` | Marks your spots so WiFi readings can be matched to them later | 0 |
| `hall-survey` | Logs air pressure; you type in temperature and humidity | 1 |

**Fourteen of the sixteen run on any phone** — a cheap Android or an iPhone.
`hall-survey` needs a barometer (an air-pressure sensor, which cheaper phones skip).
`strobe-tacho` needs to control the torch, which only works in phyphox 1.2.1 — a
test version that isn't public yet — so it's Tier 3 for now. Nothing is blocked by
that: `fan-tacho` already reads fan speed two other ways.

A file called `capabilities.json` lists what each test needs. A script,
`tools/check_tiers.py`, opens every experiment and fails if the list doesn't match
what the file actually uses — so the table above can't quietly drift out of date,
which is the usual way a compatibility list turns into a lie.

```sh
python3 tools/check_tiers.py
```

## How to install

**All of them at once — one scan.** phyphox can read a zip file (a bundle of
files squashed into one). Point it at `all-tests.zip`, and it lists everything
inside and lets you add them together. That's the big QR code at the top of
`install.html`, and the big button at the top of `open.html`. A QR code is the
square barcode you scan with a camera.

That code also never goes out of date: it points at the zip, not at any one
experiment, so when the zip is updated everyone who already scanned the code gets
the new versions. Print it once.

**One at a time.** Open `open.html` on the phone and tap the test you want. Each
button hands the file straight to phyphox, which asks whether to add it.

```sh
python3 tools/make_qr.py --base https://raw.githubusercontent.com/thorhale/phyphox-tests/main
```

That command rebuilds `open.html` (tap-to-install links, for setting up straight
from the phone) and `install.html` (QR codes, for scanning off a computer screen).

Two things that waste an afternoon if nobody warns you:

- **The files have to be public on the web.** phyphox downloads each one from a
  web address with no login. If the folder is private, the phone just gets a
  "not found" error and the link looks broken.
- **Don't type a `phyphox://` address into the browser.** The browser will search
  the web for the words instead of opening the link. These special links only work
  when you *tap* them — which is exactly what `open.html` is for.

Emailing the file to yourself and tapping it works sometimes and not others.
Android decides what a file is by an internal label, not by its name, and a
`.phyphox` file has no label it recognises. Use the links instead.

## What to know before trusting a number

**The sound meter needs setting up (calibrating).** Out of the box it guesses. The
loudness number will be in the right ballpark, but it's a guess until you check it
against a real meter once. *Comparing* two places is reliable straight away; the
lone number is not.

**Don't use it for safety calls.** Not for hearing protection, not for anything
with a legal limit. Phones distort above about 100–110 dB, and a phone microphone
is not a real instrument.

**The tilt / level readings are the most accurate thing here** — good to about a
hundredth of a degree — but only when the phone is completely still.

**Anything magnetic only compares.** It finds live cables and shows which feed is
busier. It can't tell you the actual current in amps.

**The sound-based thermometer is fussy.** It works out air temperature from how
fast sound travels. But if the distance you type in is 1% off, the temperature is
about 6 °C off. Measure the gap with a tape, use a long one, and take a few
readings.

## WiFi

**phyphox can't read WiFi at all.** No signal strength, nothing. It only gets the
phone's sensors, and the WiFi radio isn't one of them.

So `wifi-walk` does the half it can: it marks where you were and when. You get the
signal strength from a separate app (WiFiAnalyzer works), and the two are matched
up afterwards by their clock times.

**Do this first, or the whole thing is pointless:** Android normally allows only
about 4 WiFi scans every 2 minutes — one reading every 30 seconds, which is
useless if you're walking. Turn that limit off in Settings → Developer options →
Wi-Fi scan throttling. If that switch isn't there, an app called Shizuku can do it
with this command:

```
settings put global wifi_scan_throttle_enabled 0
```

WiFiAnalyzer shows at the top of its screen whether the limit is on. Check there
before you start.

### Two ways to get the WiFi data in

**Simple way — join them up afterwards.** Walk around pressing *Log waypoint* in
phyphox, and press Export in WiFiAnalyzer at the same spots. Then:

```sh
python3 tools/wifi_merge.py waypoints.csv scan*.txt -o survey.csv
```

That matches every WiFi access point (the box that broadcasts the WiFi) to the
waypoint you were standing on.

There's a nasty trap it handles for you. phyphox records time in UTC (a single
world clock), and WiFiAnalyzer records local time without saying so. Join them the
naive way and everything is shifted by a few hours — and the result still *looks*
fine, which is the dangerous part. So the script works out the shift by trying
every whole-hour offset and keeping the one that lines up, and it tells you which
it used. If nothing lines up, it stops and says so instead of handing you a wrong
file.

**Automatic way — feed it in live.** phyphox can accept values over the network
while it's running. `wifi_push.py` scans and sends the signal strength straight
in, so you only have to press *Log waypoint*:

```sh
python3 tools/wifi_push.py --host 192.168.0.14:8080 --bssid 1c:49:7b:66:ee:17
```

Turn on *Allow remote access* in the phyphox menu first, and use the address it
shows you. (A BSSID is the unique ID of one WiFi box.)

**Catch:** signal strength belongs to whatever radio measured it. If you're
walking with the phone, the scan has to come from the phone too — which means
running the scan on the phone (through an app like Termux or a Shizuku shell), not
on a laptop. A laptop only works if it sits next to the phone and neither of you
moves.

**If you want it fully automatic:** a $5 ESP32 board (a tiny WiFi computer) can
scan WiFi and send the results to phyphox over Bluetooth. That walks with you and
needs no phone shell. Not built yet.

## Checking a file before you install it

```sh
python3 tools/lint.py experiments/*.phyphox
```

A "linter" is a script that reads a file and points out mistakes. This one catches
the errors that make phyphox refuse a file, or worse, quietly hand you wrong
numbers. Three that bit me while writing these:

1. An XML note (a `<!-- ... -->` comment) is not allowed to contain a double
   hyphen `--`. A divider line made of dashes makes the whole file refuse to open.
2. The phone stores readings in fixed-size boxes. If you write 4095 readings into
   a box that holds 4096 and don't clear it first, one old reading stays stuck at
   the front and shoves everything after it along by one. In a list of pitches
   that puts every pitch in the wrong slot — silently. I did this in eight files
   before I caught it.
3. Reading a box empties it. If one step adds up a list and a later step tries to
   count the same list, the count comes out zero, and any average built on it is
   wrong. This one made the room-echo and rack-signature tests wrong by 35 and 64
   times.

The checker is proven both ways: it passes phyphox's own official files cleanly,
and if you deliberately put any of the three bugs above back in, it complains. A
checker that has never caught anything is just a green light with no bulb behind
it.

## If something doesn't work

See **[BACKUP-PLAN.md](BACKUP-PLAN.md)**. Short version: run the six files in
`probes/` in order — the first one that fails tells you where the problem is. And
if phyphox turns out to be unusable, `tools/analyse_export.py` does the same maths
on a computer, from a plain data file exported by any built-in phyphox experiment,
using the exact formulas out of these files.

## Checking the maths

```sh
python3 run_checks.py
```

This runs everything: the file check, the hardware-claims check, 28 physics tests,
and a "did we break anything" test. It needs no extra software, so it even runs in
Pydroid (a Python app) on the phone.

The physics tests read the **actual formula out of each `.phyphox` file** and work
it through. They don't rewrite the maths in Python and compare the two — that would
only prove I can type the same thing twice. If you edit a file in a way that breaks
a claim the docs make, a test fails.

What's locked down:

- **A- and C-weighting** (the two standard "hearing filters" for loudness) checked
  against the official reference table at 34 different pitches, worst case 0.274 dB
  off.
- **The loudness chain** — a full-strength tone has to read −3.010 dBFS and stay
  even across a 40 dB range. That one number proves several separate steps are all
  correct together.
- **Noise dose** (how much loud-noise exposure adds up over a work day) — 8 hours
  at the limit level, and the exposure time halves each time the energy doubles.
- **Speed of sound** — the calculation run forwards and backwards, checked from
  0 to 40 °C, plus the warning that a 1% distance error means a 5.97 °C error.
- **Magnetic landmark** — the number it reports stays the same across 200 random
  phone angles (that's the whole point of it).
- **Every fixed number** in every file, checked against what it should be.

And `tests/test_mutations.py` deliberately breaks one number at a time — rounding
331.3 to 340, swapping two loudness constants, mistyping eight hours — and demands
that each break gets caught. All 10 are. **A test that has never failed proves
nothing.** Writing that test found two real gaps: nothing was checking the
peak/clipping path, and the speed-of-sound round trip was passing even with a
rounded constant, because both directions changed together and hid it.

It also caught two places where my *writing* was wrong, not the code: I'd stated
the step-count error at twice its real size, and claimed a round 3 dB halves the
allowed time when the true figure is 3.0103 dB.

## Editing them

They're written in XML (a plain-text format of labelled brackets). The
[file format docs](https://phyphox.org/wiki/index.php/Phyphox_file_format) explain
the pieces: storage boxes, sensor inputs, a chain of small maths steps, the
screens, and what gets saved out.

There's also a [visual editor](https://phyphox.org/editor/) if you'd rather not
type XML by hand.

## Getting data out

Export as CSV in phyphox (a plain spreadsheet file). Each screen becomes its own
file inside a zip. The column names are fixed by the experiment, so they're safe
to rely on.

Everything that logs also writes the exact clock time on every row, which is what
lets two separate recordings be lined up later. If two phones are involved, clap
once in front of both at the start — then you can *check* they line up instead of
hoping.
