# Setting up the sound meter (calibrating)

"Calibrating" just means teaching the meter what a real decibel is, once, so its
single loudness number can be trusted. Here's how — and why you probably don't
need to bother.

## First: you probably don't need to

The meter already works fine, un-set-up, for most of what you'd use it for.

**Already correct, right now, with no setup:**

- which aisle is louder, and by how much
- whether a rack got louder since last month
- where the noisy machine is
- what happens to the level when a CRAC (the big room air conditioner) kicks in
- which pitch a noise sits at

All of those are **comparisons**, and a comparison doesn't care about the setup
number. The meter adds the same fixed number to both readings, so it cancels out
when you compare them.

**Needs calibration:**

- quoting one loudness number on its own, with "dB" after it

**Don't do at all, set up or not:**

- hearing-protection decisions, or anything with a legal limit

So if you're comparing places or tracking one place over time, you're done — stop
reading.

---

## What calibrating actually is

Your phone's microphone doesn't measure loudness. It measures a raw electrical
signal. To turn that signal into decibels you add a fixed number — and that number
is different for every phone model.

The meter starts with **120** as a stand-in. That's a reasonable guess for a
typical phone and nothing more. Calibrating means finding your phone's real number
and typing it in.

That's the whole job. One number, once per phone, forever.

---

## Where to get a reference — cheapest first

A "reference" here means a proper sound meter you trust, to check your phone
against.

### 1. Borrow one from your safety people (free, best)

Any site with a data hall has someone who does hearing checks — the health-and-
safety or facilities team. They own a proper meter, and it gets re-checked every
year because it has to be. This is the best option, and the one people skip
because it feels like a bother. It isn't. It's ten minutes standing next to
someone.

### 2. Use a noise survey that already exists (free)

Building reports and noise assessments list loudness in dB(A) at specific spots.
Stand where the report says and match your reading to their number. Someone
already paid for that measurement.

### 3. Borrow from a contractor (free)

Sound consultants, air-conditioning engineers and AV people all carry meters.

### 4. An iPhone running NIOSH's app (free, if you can get an iPhone)

NIOSH — the US government's work-health institute — makes a free sound meter app
for iPhone. It's the one that was actually tested in a lab, and on iPhone hardware
it came within about 2 dB of a proper meter.

It's iPhone-only, and that's on purpose. NIOSH tested Android and decided you
can't reliably trust it, because every maker uses different microphones, different
chips and different sound processing. Apple makes only a handful of models and
controls the whole chain, so one app can be tuned to them.

Not a certified reference. But much better than a guess.

### 5. Buy a meter (about $30)

A basic "class 2" sound meter costs far less than people expect. If borrowing
falls through, this is the honest answer.

### 6. What to skip

**An acoustic calibrator.** This is a little device that makes an exact tone
(94 dB at 1000 times a second) for setting up meters. It costs about the same as a
meter — but it's built to clip tightly onto a proper measurement microphone with a
sealed seal. A phone held against one doesn't seal, and the error from that gap is
anyone's guess. Wrong tool for a phone.

---

## The steps

1. **Go where the noise is** — about 75 to 85 dB, in the hall. Not a quiet office.
   Phone microphones misbehave at the very quiet and very loud ends, so you'd be
   setting up the wrong part of the range.
2. **Side by side** — the reference meter and the phone at the same height, both
   microphones pointing the same way.
3. **Take the case off**, or at least know where the phone's microphone is —
   usually the bottom edge, near the charging port. A case lip over it quietly
   costs you several dB every time.
4. **Let both settle for 30 seconds.** Use **Leq** from this meter (the average
   loudness since you pressed play) and the reference's averaged reading. Average
   against average — never one jumping number against another.
5. Type the reference reading into **Reference level**, and press **Calibrate**.
6. **Write the resulting number down.** It isn't saved when you close the app. It
   is the whole point of the exercise.

Record it in the log at the bottom of this page.

---

## Setting up a second phone from the first

Once one phone is set up, you don't need the reference meter again.

Put both phones side by side in steady noise. Read the set-up one, type that
number into the other phone as its reference, and press Calibrate. The small error
you pass along is tiny next to the model-to-model differences you're removing.

NoiseCapture — a free, open noise app from a French university (Université Gustave
Eiffel) — has a built-in "copy the setting from one phone to another" feature,
which is a good sign this approach is sound. Borrow a meter once, then set up the
whole team's phones from that one.

---

## Two leads worth knowing about

Neither is settled. Both are written down so they don't get lost. A little jargon
first:

- **dBFS** — loudness compared to the loudest the phone can record, so it's always
  a minus number.
- **SPL** — sound pressure level, i.e. real-world loudness in the air.
- **RMS** — a kind of average size of a wobbly signal.

### Android's own rulebook seems to fix the number at 130

Android has an official rulebook that a phone must follow to ship with Google's
apps. It says that on the "raw, unprocessed" sound path, a standard tone
(94 dB SPL at 1000 times a second) must produce a signal of a set size. That size
works out to **−36 dBFS**, which would make the calibration number **130** on any
phone that follows the rule.

**The catch:** that rule is about the raw sound path, and it's not proven that
phyphox uses that path — phyphox's own docs say their sound measurement is
un-set-up with a made-up starting number. And the rule only binds phones that say
they support that raw path.

So this is a **hunch to test**, not a fact to ship. The starting number here stays
120. If you calibrate and land near 130, that's a hint the rule carries through —
worth writing down.

### Your phone might be able to tell you its own number

Android 9 added a way for a phone to report how sensitive its microphone is —
defined, word for word, as the dBFS from that same standard tone. That is the
calibration number, straight from the maker.

**Two catches:** phyphox can't read it (a phyphox experiment only gets sensor
data — reading this would need a small separate app, or a typed computer command
over USB), and makers are allowed to answer "don't know," which many do.

---

## The idea that didn't work, and why

The plan was to build a lookup table from NoiseCapture's public data: find your
phone model, read off its number, no meter needed. Their notes list phone maker,
phone model, and the calibration number as things they store.

**The public data files don't actually contain the phone maker or model.** Checked
across five countries' files (Andorra, Luxembourg, Malta, Iceland, Estonia) — every
record has the calibration number, none has a maker or model. Almost certainly on
purpose: a phone model stuck to a GPS track can identify a person. Their notes
describe their private database, not the public download.

A script, `tools/noise_offsets.py`, still runs, and shows you this itself instead
of asking you to take it on trust. What it *can* answer is how big the numbers
people actually enter are, which caps how much the phone model can possibly matter.

**And even with model data it wouldn't have transferred.** NoiseCapture's number
is measured against *its own* sound-handling. phyphox handles sound differently.
The table would have given differences *between models*, not phyphox's own starting
number — so you'd still have needed one real calibration to anchor it.

**What survives:** research on Android sound apps found that phones handle loudness
the same way apart from **a fixed gap of 0 to 15 dB depending on model**. That's
the useful finding, and it's what makes phone-to-phone copying fair — it's one
number per model, not a whole different behaviour.

---

## Calibration log

Fill this in. A calibration number nobody can trace back to a source is just a
different kind of guess.

| Date | Phone (model + Android/iOS version) | Reference used | Where | Level there | Number found |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

**Why the version column:** the phone's sound handling is part of the chain, and
it can change with a system update. If a phone's readings shift after an update,
this column is how you'll know why.

---

**Sources**

- [Smartphone sound measurement across Android devices (MDPI Sensors, 2022)](https://www.mdpi.com/1424-8220/22/1/170) — the 0–15 dB per-model gap
- [NoiseCapture crowd-sourced database](https://pmc.ncbi.nlm.nih.gov/articles/PMC8345695/) · [data dumps](https://data.noise-planet.org/dump/) · [calibration, incl. phone-to-phone](https://noise-planet.org/noisecapture_calibration.html)
- [Android CDD 5.4 — unprocessed audio source](https://android.googlesource.com/platform/compatibility/cdd/+/refs/tags/platform-tools-31.0.0/5_multimedia/5_4_audio-recording.md)
- [`MicrophoneInfo.getSensitivity()`](https://developer.android.com/reference/android/media/MicrophoneInfo)
- [NIOSH on smartphone sound apps, and why there's no Android version](https://www.cdc.gov/niosh/bulletin/2014/sound-app.html)
- [phyphox Audio Amplitude — "uncalibrated, arbitrary offset"](https://phyphox.org/wiki/index.php/Experiment:_Audio_Amplitude)
