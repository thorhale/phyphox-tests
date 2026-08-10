# If it doesn't work on your phone

Sixteen experiments have never run on a phone. This is what to do when
something doesn't work, in the order that finds the problem fastest.

## Step 0: getting them onto the phone at all

phyphox's **+** menu offers three ways in: QR code, Bluetooth device, or a
simple built-in experiment. **There is no "open a file" option.**

Emailing yourself the `.phyphox` file and tapping it *sometimes* works, and
phyphox's own documentation explains why it is unreliable: on Android the file is
identified by MIME type rather than extension, and a `.phyphox` file reports as an
unknown type. Some mail apps and file managers hand it over, others do not.

**The route that works is the QR code**, and it needs the files reachable without
a login — phyphox downloads them from the address in the code, so a private
repository just gives the phone a 404.

```sh
python3 tools/make_qr.py --base https://raw.githubusercontent.com/USER/REPO/main
```

That writes `install.html`: open it on a computer and scan from the screen with
phyphox's own scanner. If a code fails, paste its URL into a browser first — if
that needs a login, so does the phone.

There is also an offline QR format that embeds the whole experiment, needing no
hosting. It is a partial ZIP behind a 13-byte header, and I have deliberately not
implemented it: it cannot be tested from here, and shipping an untested encoder
would just add another thing that can silently fail.

## Step 1: run the probes

`probes/` holds six tiny diagnostic files. Install them in order. **The first
one that fails names the problem.**

| Probe | Tests | If it fails |
|---|---|---|
| `00-loads` | phyphox accepts a hand-written file at all | Nothing else will work. Open the file, change `version="1.14"` near the top to `1.7`, and try again — an older app may reject a newer version number |
| `01-analysis` | the analysis chain runs | Every experiment is affected. Report it — this would be surprising |
| `02-formula` | `sqrt`, `cos`, `acos`, `max`, `min`, `round`, `abs` | Most experiments use these. Says which function names your version accepts |
| `03-fft` | Fourier transform, ramps, buffer slicing | Takes out the sound meter, fan tacho, vibration census, tile tap, rack signature, leak sweep |
| `04-speaker` | playing a tone | Only affects Dimension Survey and Room Echo |
| `05-flashlight` | strobing the torch | Only affects Strobe Tacho |

Each probe shows a number that should be around 9.8 when the phone is still, so
"nothing showing" and "wrong number" are easy to tell apart.

Probes 0–3 are the ones that matter. If those four pass, the machinery every
experiment depends on works and any remaining problem is in one specific file.

## Step 2: if the probes pass but an experiment misbehaves

Send me the export. Every experiment writes its working out — sample rates,
intermediate values, the full spectrum — precisely so a bad reading can be
diagnosed without the phone in hand.

Run `device-check` first and send that too. It reports the real sample rates and
noise floors, which explain most surprising readings on their own.

## Step 3: the fallback that needs none of this

**The physics does not have to run on the phone.**

phyphox's own built-in experiments already record raw data and export CSV. The
analyser does the same maths on a computer:

```sh
python3 tools/analyse_export.py sound     "Raw data.csv"
python3 tools/analyse_export.py tone      "Raw data.csv" --from 50 --to 2000
python3 tools/analyse_export.py magnetic  "Magnetometer.csv" --accel "Accelerometer.csv"
python3 tools/analyse_export.py vibration "Accelerometer.csv"
```

Record with these built-ins:

| What you want | Record with | Then run |
|---|---|---|
| Sound level in dB(A), Leq, C−A | **Audio Scope** (exports the waveform) | `sound` |
| Fan RPM, tile ring, disk spindle | **Audio Scope** | `tone` |
| Magnetic landmark signature | **Magnetometer** + **Acceleration with g** | `magnetic` |
| Machine census, crest factor | **Acceleration with g** | `vibration` |

Not **Audio Amplitude** for the sound modes — it exports a level, having already
thrown the waveform away.

This is not a second implementation. The weighting curves, decibel conversions
and signature formulas are **read out of the `.phyphox` files and evaluated**,
so both routes compute identical arithmetic, and the same regression tests cover
both. It runs in Pydroid on the phone as well, with no dependencies.

Its own tests feed it recordings with exactly known answers:

```sh
python3 tests/test_analyser.py
```

A 1 kHz sine at amplitude 0.1 must read −23.01 dBFS on all three weightings; a
125 Hz tone must sit 16.1 dB below a 1 kHz one; a pure sine must have a crest
factor of exactly √2. If those pass, the backup route is sound whatever the
phone does.

## Step 4: what genuinely cannot be worked around

- **phyphox cannot read WiFi.** See the README. Needs a separate app or an ESP32.
- **No phone has a hygrometer.** Humidity is typed in, never measured.
- **The microphone is uncalibrated.** Absolute dB is a guess until you calibrate
  against a real meter. Differences and spectra are trustworthy immediately.
- **The accelerometer stops at 50–250 Hz.** Bearing defect frequencies live in
  the kilohertz and no phone reaches them. That is why the fan test uses crest
  factor, which senses the impacts in time instead.
