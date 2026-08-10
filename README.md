# phyphox-tests

Custom experiments for the [phyphox](https://phyphox.org) phone app, for
measuring things in a data hall with the phone you already have.

**None of these have been tried on a real phone yet.** They're checked by a
script and the maths is verified, but that's not the same as working.

## Start here

**Run `device-check` first on any new phone.** It opens every sensor, sees what
actually answers, measures the real sample rates, and tells you plainly which of
these tests that phone can run. Phones differ a lot and it is better to find out
in the office than halfway down an aisle.

## The experiments

Tier 0 means it runs on anything — a cheap A-series Android *and* an iPhone.
Nothing in Tier 0 needs a barometer, a gyroscope, the light sensor, Bluetooth or
any extra hardware.

| File | What it does | Tier |
|---|---|---|
| `device-check` | What this phone has, its real sample rates and noise floors | 0 |
| `sound-level-meter` | How loud it is, in proper dB(A) | 0 |
| `emi-survey` | Finds live power cables, so you can route network cable away | 0 |
| `busway-load` | Which power feed is working harder, without touching anything | 0 |
| `magnetic-fingerprint` | Find an exact spot again, using the building's steel as the map | 0 |
| `fan-tacho` | Fan speed, and whether a bearing is starting to fail | 0 |
| `vibration-census` | Which machines are actually running, from one floor recording | 0 |
| `strobe-tacho` | Fan speed read by eye with the torch — the honest check on `fan-tacho` | 0 |
| `tile-tap` | Finds loose or unsupported floor tiles by the note they ring at | 0 |
| `acoustic-fingerprint` | Recognise a place by its echoes; how live the room is | 0 |
| `rack-signature` | Find the odd one out in a row of identical machines | 0 |
| `ultrasonic-leak` | Hunt compressed-air and valve leaks by high-frequency hiss | 0 |
| `dimension-survey` | Distances, air temperature from sound speed, floor level | 0 |
| `walk-logger` | Records everything at once while you walk around | 0 |
| `wifi-walk` | Marks your spots so WiFi readings can be matched to them later | 0 |
| `hall-survey` | Logs air pressure; you type in temperature and humidity | 1 |

**Fifteen of the sixteen run on any phone** — a cheap A-series Android or an
iPhone. `capabilities.json` says what each one needs. `tools/check_tiers.py` opens every
file and fails if that claim is not true — so the table above cannot quietly stop
matching the files, which is the usual way a compatibility list becomes a lie.

```sh
python3 tools/check_tiers.py
```

## How to install one

1. Email the `.phyphox` file to yourself
2. Open it on your phone
3. phyphox asks if you want to add it — say yes

It then sits in your experiment list like any built-in one.

## What to know before trusting a number

**The sound meter needs calibrating.** Out of the box it guesses. The dB number
will be in the right ballpark but it is a guess until you calibrate it against a
real meter. Comparing two places is reliable straight away; the absolute number
is not.

**Don't use it for safety decisions.** Not for hearing protection, not for
anything with a legal limit. Phones clip around 100-110 dB and the microphone
is not a measuring instrument.

**The tilt/level readings are the most accurate thing here** — good to a
hundredth of a degree, but only when the phone is completely still.

**Anything magnetic is comparative.** It finds live cables and shows which feed
is busier. It is not an ammeter.

**The sonar thermometer is fussy.** It works out air temperature from how fast
sound travels. But if the distance you type in is off by 1%, the temperature is
off by 6 °C. Measure the span with a tape, use a long one, take a few readings.

## WiFi

**phyphox cannot read WiFi at all.** No signal strength, nothing. It only has
access to the phone's sensors and WiFi isn't one of them.

So `wifi-walk` does the half it can: it marks where you were and when. You get
the signal strength from a separate app (WiFiAnalyzer works), and the two are
matched up afterwards by time.

**Do this first, or the whole thing is pointless:** Android only allows about 4
WiFi scans every 2 minutes. That's one reading every 30 seconds — useless if
you're walking. Turn it off in Settings → Developer options → Wi-Fi scan
throttling. If that toggle isn't there, Shizuku can do it:

```
settings put global wifi_scan_throttle_enabled 0
```

WiFiAnalyzer shows at the top of its screen whether throttling is on. Check
there before you start.

### Two ways to get the WiFi data in

**Simple way — join them up afterwards.** Walk around pressing *Log waypoint* in
phyphox, and hit Export in WiFiAnalyzer at the same spots. Then:

```sh
python3 tools/wifi_merge.py waypoints.csv scan*.txt -o survey.csv
```

That matches every access point to the waypoint you were standing on.

There's a nasty trap it handles for you: phyphox records time in UTC, and
WiFiAnalyzer records local time without saying so. Join them naively and
everything is shifted by a few hours — and the result still looks fine, which is
the dangerous part. So the script works the shift out by testing every whole-hour
offset and picking the one that fits, and it tells you which it used. If nothing
lines up it stops and says so rather than handing you a wrong file.

**Automatic way — feed it in live.** phyphox can accept values over the network
while it's running. `wifi_push.py` scans and pushes the signal strength straight
in, so you only have to press *Log waypoint*:

```sh
python3 tools/wifi_push.py --host 192.168.0.14:8080 --bssid 1c:49:7b:66:ee:17
```

Turn on *Allow remote access* in the phyphox menu first, and use the address it
shows you.

**Catch:** signal strength belongs to whatever radio measured it. If you're
walking around with the phone, the scan has to come from the phone too — which
means Termux or a Shizuku shell on the phone, not a laptop. A laptop only works
if it's sitting next to the phone and neither of you moves.

**If you want it properly automatic:** a $5 ESP32 board can scan WiFi and send
the results to phyphox over Bluetooth. That walks with you and needs no shell.
Not built yet.

## Checking a file before you install it

```sh
python3 tools/lint.py experiments/*.phyphox
```

This catches the mistakes that make phyphox refuse a file, or worse, quietly
produce wrong numbers. Three that bit me while writing these:

1. An XML comment can't contain `--`, so a `<!-- ---- section ---- -->` divider
   makes the file unopenable.
2. Buffers are fixed-size rings. Write 4095 values into a 4096 slot without
   clearing and one stale value stays at the front, shifting everything after it.
   In a spectrum that puts every frequency reading one bin out — silently. I did
   this in eight files before catching it.
3. Reading a buffer consumes it. If one step totals an array and a later step
   counts the same array, the count is zero and any average built on it is wrong
   by a factor of the square root of the array length. This one cost the room-echo
   and rack-signature tests a factor of 35 and 64 respectively.

The checker is verified in both directions: it passes phyphox's own official
experiment files clean, and deliberately reintroducing each of the three bugs
above makes it complain. A checker that has never caught anything is just a
green light with no bulb behind it.

## Checking the physics

```sh
python3 run_checks.py
```

Runs everything: file structure, the capability claims, 28 physics tests, and a
mutation test. No dependencies, so it works in Pydroid on the phone too.

The physics tests read the **actual formula out of the `.phyphox` file** and
evaluate it. They don't re-implement the maths in Python and compare — that
would only prove I can type the same thing twice. Editing a file in a way that
breaks a documented claim fails the tests.

What's pinned:

- **A- and C-weighting** against the IEC 61672 table at 34 frequencies, worst
  case 0.274 dB
- **The level chain** — a full-scale sine must read −3.010 dBFS, and stay linear
  across 40 dB. That one number proves the window power, the half-spectrum
  doubling and the 1/N² are all right *together*
- **Noise dose** — 8 hours at the criterion level, halving for every doubling of
  energy
- **Speed of sound** — round trip, absolute values from 0–40 °C, and the
  sensitivity warning (1 % distance error = 5.97 °C)
- **Magnetic signature** — unchanged across 200 random phone orientations
- **Every magic number** in every file, checked against what it should be

And `tests/test_mutations.py` breaks one constant at a time — rounding 331.3 to
340, swapping the power and amplitude decibel constants, mistyping eight hours —
and requires each to be caught. All 10 are. **A test suite that has never failed
proves nothing**, and writing that mutation test found two real gaps: nothing
was testing the peak/clipping chain, and the speed-of-sound round trip passed
happily with absolute zero rounded to 273, because both directions changed
together.

It also caught two places where my *documentation* was wrong rather than the
code: the step-count error was quoted at twice its real value, and I'd asserted
a round 3 dB halves the allowed exposure time when the true figure is 3.0103 dB.

## Editing them

They're XML. The [file format docs](https://phyphox.org/wiki/index.php/Phyphox_file_format)
explain the structure: buffers, sensor inputs, a chain of small maths steps, the
screens, and what gets exported.

There's also a [visual editor](https://phyphox.org/editor/) if you'd rather not
hand-write XML.

## Getting data out

Export as CSV in phyphox. Each section becomes its own file inside a zip. The
column names are fixed by the file, so they're safe to rely on.

Everything that logs writes a Unix timestamp, which is what lets separate
recordings be lined up later. If two devices are involved, clap once in front of
both at the start — then you can check the alignment rather than hope.
