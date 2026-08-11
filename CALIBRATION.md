# Calibrating the sound meter

## First: you probably don't need to

The meter works fine uncalibrated for most of what you'd actually use it for.

**Already correct, right now, with no calibration:**

- which aisle is louder, and by how much
- whether a rack got louder since last month
- where the noisy unit is
- what happens to the level when a CRAC kicks in
- which pitch a noise sits at

All of those are **differences**, and differences don't care about the offset —
it's added to both sides and cancels out.

**Needs calibration:**

- quoting one number with dB after it

**Don't do at all, calibrated or not:**

- hearing protection decisions, or anything with a legal limit

So if you're comparing and trending, stop reading. You're done.

---

## What calibration actually is

Your phone's microphone doesn't measure sound levels. It measures a signal. To
turn that signal into decibels you add a fixed number, and that number is
different for every phone model.

The meter starts at **120**, which is a plausible value for a typical phone and
nothing more. Calibrating means finding your phone's real number and typing it in.

That's the whole thing. One number, once per phone, forever.

---

## Where to get a reference — cheapest first

### 1. Borrow one from your safety people (free, best)

Any site with a data hall has someone doing hearing-conservation checks — EHS,
industrial hygiene, facilities. They own a Type 2 meter and it's calibrated
annually because it has to be.

This is the best option and the one people skip because it feels like imposing.
It isn't. It's ten minutes standing next to someone.

### 2. Use a noise survey that already exists (free)

Commissioning reports and acoustic assessments list dB(A) at specific locations.
Stand where the report says, match your reading to their number. Someone already
paid for that measurement.

### 3. Borrow from a contractor (free)

Acoustic consultants, HVAC commissioning engineers and AV people all carry meters.

### 4. An iPhone running NIOSH's app (free, if you can get an iPhone)

NIOSH — the US occupational health institute — publishes a Sound Level Meter app
for iOS. It's the one that was actually lab-tested rather than just claiming
accuracy, and on iPhone hardware it came out within about 2 dB of a proper meter.

It's iOS-only, and that's not an oversight. NIOSH tested Android and concluded
that verifying accuracy there "is not currently possible", because every
manufacturer uses different microphones, different audio chips and different
processing. Apple ships a handful of models and controls the whole chain.

Not a certified reference. Much better than a guess.

### 5. Buy a meter (about $30)

A class 2 sound level meter costs far less than people assume. If borrowing
falls through, this is the honest answer.

### 6. What to skip

**An acoustic calibrator.** They emit exactly 94 dB at 1 kHz and cost about the
same as a meter — but they're built to clamp onto a proper half-inch measurement
microphone with a sealed cavity. A phone held against one isn't a seal, and the
error that introduces is anyone's guess. Wrong tool for this shape of microphone.

---

## The procedure

1. **Go where the noise is.** 75–85 dB, in the hall. Not a quiet office — phone
   microphones misbehave at the extremes and you'd be calibrating the wrong end
   of the scale.
2. **Side by side.** Reference meter and phone at the same height, microphones
   pointing the same way.
3. **Take the case off**, or at least know where the phone's mic is — bottom
   edge, near the charge port. A case lip over it costs several dB, silently and
   consistently.
4. **Let both settle 30 seconds.** Use **Leq** from this meter, and the
   reference's averaged reading. Averaged against averaged — never one jumping
   number against another.
5. Type the reference reading into **Reference level**, press **Calibrate**.
6. **Write the resulting offset down.** It isn't saved between sessions. It is
   the entire product of the exercise.

Record it in the log at the bottom of this page.

---

## Calibrating a second phone off the first

Once one phone is calibrated, you don't need the reference meter again.

Put both phones side by side in steady noise. Read the calibrated one, type that
number into the uncalibrated one as its reference, press Calibrate. The error
you inherit is small compared with the model-to-model differences you're removing.

NoiseCapture — an open-source noise app from Université Gustave Eiffel — does
exactly this with a built-in Transmitter/Receiver pair, which is a good sign the
approach is sound. Borrow a meter once, calibrate the whole team's phones off it.

---

## Two leads worth knowing about

Neither is settled. Both are written down so they don't get lost.

### Android's spec appears to fix the number at 130

The Android Compatibility Definition — the rules a phone must meet to ship with
Google services — states that on the "unprocessed" audio path, a 1 kHz tone at
94 dB SPL must produce an RMS of 520 on 16-bit samples. That's **−36 dBFS**,
which makes the calibration constant **130 dB** on any compliant phone.

**The catch:** that rule binds the unprocessed audio path, and it isn't
established that phyphox uses it — phyphox's own docs describe their audio
amplitude experiment as uncalibrated with an arbitrary offset. Also, the
requirement only binds devices that declare support for that path.

So this is a **prediction to test**, not a fact to ship. The default here stays
at 120. If you do calibrate and come out near 130, that's evidence the spec
carries through, and it's worth writing down.

### Your phone may be able to state its own sensitivity

Android 9 added an API where the phone reports its microphone sensitivity,
defined as — literally — the dBFS produced by a 1 kHz tone at 94 dB SPL. That is
the calibration number, from the manufacturer.

**Two catches:** phyphox can't read it (a `.phyphox` file only gets sensor
streams — it'd need a small separate app or an ADB command), and manufacturers
are permitted to return "unknown", which many do.

---

## The idea that didn't work, and why

The plan was to mine NoiseCapture's open database into a lookup table: your phone
model, your offset, no meter needed. Their documentation lists
`device_manufacturer`, `device_model` and `gain_calibration` among the fields.

**The published dumps don't contain the device fields.** Checked across Andorra,
Luxembourg, Malta, Iceland and Estonia — every track carries `gain_calibration`,
none carries a manufacturer or model. Almost certainly deliberate: a phone model
attached to a GPS track identifies a person. The documentation describes their
internal schema, not the export.

`tools/noise_offsets.py` still runs, and will show you that itself rather than
asking you to take this on trust. What it *can* answer is how large the offsets
people enter actually are, which bounds how much the phone model can matter.

**And even with model data it wouldn't have transferred.** NoiseCapture's gain is
relative to NoiseCapture's own audio pipeline. phyphox's is different. The table
would have given relative differences between models, not phyphox's absolute
offset — you'd still have needed one real calibration to anchor it.

**What survives:** research on Android sound apps found devices process levels
identically apart from **a fixed offset of 0–15 dB depending on model**. That's
the useful finding, and it's what makes phone-to-phone transfer legitimate: it's
one number per model, not a different response curve.

---

## Calibration log

Fill this in. A calibration number nobody can trace back to a source is just a
different guess.

| Date | Phone (model + Android/iOS version) | Reference used | Where | Level there | Offset found |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |

**Why the OS version column:** the audio processing is part of the chain, and it
changes with system updates. If a phone's readings shift after an update, this
column is how you'll know why.

---

**Sources**

- [Smartphone sound measurement across Android devices (MDPI Sensors, 2022)](https://www.mdpi.com/1424-8220/22/1/170) — the 0–15 dB per-model offset
- [NoiseCapture crowd-sourced database](https://pmc.ncbi.nlm.nih.gov/articles/PMC8345695/) · [data dumps](https://data.noise-planet.org/dump/) · [calibration, incl. phone-to-phone](https://noise-planet.org/noisecapture_calibration.html)
- [Android CDD 5.4 — unprocessed audio source](https://android.googlesource.com/platform/compatibility/cdd/+/refs/tags/platform-tools-31.0.0/5_multimedia/5_4_audio-recording.md)
- [`MicrophoneInfo.getSensitivity()`](https://developer.android.com/reference/android/media/MicrophoneInfo)
- [NIOSH on smartphone sound apps, and why there's no Android version](https://www.cdc.gov/niosh/bulletin/2014/sound-app.html)
- [phyphox Audio Amplitude — "uncalibrated, arbitrary offset"](https://phyphox.org/wiki/index.php/Experiment:_Audio_Amplitude)
