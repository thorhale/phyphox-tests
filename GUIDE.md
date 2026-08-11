# What these tests actually do — in plain English

No jargon. If a word has to be technical, it gets explained the first time — and
every term that comes up more than once is defined in one place, in the
**[Words this uses](#words-this-uses)** section further down. If any word here
stops you, that's where to look.

Every test below answers the same six questions: **what** it measures, **why**
you'd care, **where** you stand, **when** you'd reach for it, **how** you run it,
and **whether it's honestly worth your time**.

That last one matters. Not all of these are equally good. I've said so plainly
per test, and there's a review at the bottom proposing which ones should be
merged or dropped. Read that before you install all sixteen.

---

## The 60-second version

| Test | In one line | Worth it? |
|---|---|---|
| **0. Device Check** | What your phone can and can't do | **Run it once, first** |
| **Sound Level Meter** | How loud it is | **Yes — the best one here** |
| **Fan Tacho** | How fast a fan is spinning, and is the bearing dying | **Yes** |
| **EMI Survey** | Where the live power cables are | **Yes** |
| **Vibration Census** | Which machines are actually running | **Yes** |
| **Floor Tile Tap** | Which raised-floor tiles are loose | **Yes — nothing else does this** |
| **Dimension Survey** | How far away is that, and is this floor level | Yes for the level. Sonar is fiddly |
| **Magnetic Landmark** | Find the exact same spot again | Yes, if you do repeat readings |
| **Busway Load** | Which power feed is working harder | Yes, but see the merge note |
| **Walk Logger** | Record everything at once while you walk | Yes, as a recorder |
| **Rack Signature** | Find the odd unit in a row of identical ones | Maybe |
| **Hall Survey** | Log air pressure and typed-in temperature | Maybe |
| **WiFi Walk** | Mark spots so WiFi readings match up later | Maybe |
| **Room Echo Signature** | Recognise a room by its echoes | **Weak — see review** |
| **Ultrasonic Leak** | Find hissing air leaks | **Weak — see review** |
| **Strobe Tacho** | Fan speed by eye with the torch | Can't run yet — needs a phyphox beta |

---

# Words this uses

Every test tries to explain its own words as it goes. But a handful come up again
and again, so here they are in one place, in plain language. Nothing here needs
maths.

## The words

**Hz** — "times per second." That's all it means. 50 Hz is fifty times a second.
A sound at 50 Hz wobbles the air fifty times a second; a fan spinning at 50 Hz
turns fifty times a second.

**RPM** — turns per minute. To go from Hz to RPM, multiply by 60. So 50 Hz is
3000 RPM.

**decibel (dB)** — how loud a sound is. It's a stretchy scale, not a normal one:
every 10 dB is **ten times** the sound energy, and sounds about **twice as loud**
to your ears. One odd result of that: two machines at 70 dB each add up to about
73 dB together, not 140.

**spectrum** — a list of which pitches a sound or a shake is made of. Like
splitting music into its low notes and high notes and seeing how much of each
there is. A "peak" in a spectrum is a pitch that's louder than the ones around it.

**magnetic field** — the invisible push a magnet or an electric wire makes in the
space around it. Measured in **microtesla (µT)**. For a size guide: the Earth
itself makes a steady field of about 25 to 65 µT everywhere, and that's the
background everything else sits on top of.

**mains** — the electricity in the wall sockets. It doesn't sit still — it flips
back and forth 50 or 60 times a second (50 in most of the world, 60 in North
America). That flipping is why a lot of things in a building hum.

**baseline** — a first reading you take on purpose, to compare everything else
against. "Set a baseline" means "record what normal looks like right here, right
now."

**reference** — the known-good thing you score everything else against. A healthy
machine, a solid floor tile, a spot you want to find again.

**calibrate / offset** — a phone sensor measures a raw signal, not a real-world
unit. To turn one into the other you add a fixed number, called the offset.
Finding that number is called calibrating. Most of these tests don't need it —
see the big idea below about differences.

**a.u.** — you'll see this on some graphs. It's short for "arbitrary units," which
means: this number only means something **compared with another number from the
same test**, on the same phone. Don't read it as a real measurement on its own.

## The one rule about fast things (and why some tests won't show a pitch)

A phone sensor doesn't watch all the time. It takes quick snapshots — a few times
a second for some sensors, thousands of times a second for the microphone.

There's a rule with no exceptions: **to catch something that repeats, you have to
take snapshots more than twice as fast as it repeats.** If you don't, you don't
just get a fuzzy answer — you get a confidently **wrong** one. The repeating thing
shows up as a slower wobble that isn't really there.

The everyday version: on film, a fast-spinning wagon wheel sometimes looks like
it's turning slowly backwards. The camera isn't snapping fast enough to keep up,
so it invents a slow motion that never happened. Phone sensors do exactly the same
thing when something is too fast for them.

That's why a few of these tests refuse to show you a pitch or a frequency for
something — because at that speed, any number they gave you would be made up.

## Two big ideas that run through everything

**1. Differences are trustworthy. Single numbers are usually guesses.**
Most phone sensors aren't calibrated, so a lone number with a unit after it is a
rough guess. But comparing two places, or the same place last month against this
month, cancels out whatever the guess got wrong — because the same error is in
both readings. So "this aisle is 6 dB louder than that one" is reliable even when
"it's 72 dB" is not.

**2. A held phone is a moving phone. Put it down.**
For anything that measures shaking, tilt, or a magnetic field, your hand wobbles
far more than the thing you're trying to measure. Set the phone on the floor or
against the surface and take your hand off it. This is the single most common way
to get a meaningless reading.

## Parts of a data hall (in case you're new to the room)

- **CRAC** — the big air-conditioning unit that keeps the room cold. (Stands for
  Computer Room Air Conditioner.)
- **rack** — the tall metal cabinet the computers are bolted into.
- **raised floor** — a second floor sitting on little legs above the real one, so
  cold air and cables can run underneath. The removable squares are **tiles**, the
  little legs are **pedestals**, and the rails they sit on are **stringers**.
- **plenum** — the gap under the raised floor that the cold air flows through.
- **cold aisle / hot aisle** — the lane in front of the racks where cold air comes
  out, and the lane behind where hot air comes off.
- **containment** — doors and panels that pen the cold air in so it doesn't mix
  with the hot.
- **busway / busbar** — a metal track running overhead that carries the power; the
  copper bars inside it are the busbars. A **tap-off** is where a feed branches off
  it to a rack.
- **conductor** — any wire or bar carrying electricity.

## Units you'll see on labels

| Unit | Plain meaning |
|---|---|
| Hz, kHz | times per second; kHz is thousands of times per second |
| dB, dB(A), dB(C) | loudness; the letter is just which "hearing filter" was used |
| dBFS | loudness compared to the loudest the phone can record — always a minus number |
| dBm | radio signal strength; less negative is stronger (−67 beats −85) |
| µT (microtesla) | magnetic field strength (Earth ≈ 25–65 µT) |
| RPM | turns per minute |
| m/s² | how hard something is shaking (acceleration) |
| mm/m | slope — millimetres of drop per metre across |
| hPa, Pa | air pressure (100 Pa = 1 hPa) |
| lx (lux) | how bright the light is |
| °C | temperature in Celsius |
| % | a share out of a hundred |

---

# The good ones

---

## 0. Device Check

**WHAT IT DOES** — Opens every sensor in your phone, sees which ones actually
answer, and measures how fast each one really reports.

**WHY YOU CARE** — Phones differ enormously and none of them tell you what's
inside. Cheap phones often have no barometer. Almost no phone has a real
thermometer. This finds out in the office instead of halfway down an aisle.

It also measures something no spec sheet gives you: how many readings per second
each sensor really produces. That number sets a hard ceiling on what the other
tests can see. A sensor that reports 100 times a second physically cannot detect
anything vibrating faster than 50 times a second. That's not a software limit,
it's arithmetic, and it can't be worked around.

**WHERE** — Anywhere. A desk is fine.

**WHEN** — Once per phone, ever. Do it before you trust anything else.

**HOW**
1. Put the phone **flat on a table and let go of it.** Don't hold it. A held
   phone is a moving phone and it ruins the noise readings.
2. Press play. Wait 30 seconds.
3. Read the **Sensors** tab — each line says fitted or not fitted, and how fast.
4. Read **What you can run** — a plain list of which tests this phone supports.

**WHAT YOU'LL SEE** — On a decent modern phone: accelerometer and gyroscope
around 400–500 readings a second, magnetometer around 100, microphone 48,000,
barometer around 12.

Ambient temperature and humidity will almost certainly say **not fitted**. That's
normal — hardly any phone has them. It's why the Hall Survey makes you type the
temperature in by hand.

Light and proximity will show a very low rate. **That's also normal, not a
fault.** Those two only speak up when the reading changes. Phone sitting still
under a steady light? Nothing to report. They're fine.

**VERDICT** — Not a test, a pre-flight check. Run it once and never again.

---

## Sound Level Meter

**WHAT IT DOES** — Measures how loud it is, in dB(A) — the standard way of
measuring noise, weighted to match what human ears actually find loud.

Three weightings are offered. **A** is the one everyone means by "decibels" and
the one on every regulation. **C** is flatter and keeps the deep rumble that A
throws away. **Z** is raw, no weighting at all.

The gap between C and A is a useful trick on its own: **a big gap means the noise
is mostly low-frequency rumble** — fans, transformers, structural hum. A small gap
means it's hiss and whine. That tells you what kind of problem you have before
you've done anything else.

**WHY YOU CARE** — Data halls are loud, and it's the number that shows up in
complaints, in commissioning documents, and in hearing-protection arguments. Also
because a hall getting louder over months is a machine going wrong.

**WHERE** — Anywhere. Hold it at head height, away from your body, mic pointing
into the room. Your chest reflects sound and will skew the reading.

**WHEN** — Any time you want a number for "it's loud in here."

**HOW**
1. Press play.
2. **Meter** tab shows the level now, plus **Leq** — the average since you
   started. Use Leq. The live number jumps around too much to quote.
3. Let it run at least 30 seconds before you write anything down.
4. **Spectrum** tab shows which pitches the noise is made of.
5. **Exposure** tab estimates how long you could safely stay. Treat as a rough
   guide only, not a safety decision.

**THE CATCH — read this** — Your phone's mic has no idea how loud a sound really
is. It measures a signal, and turning that into decibels needs a fixed number
added on. Mine starts at 120, which is a plausible guess and nothing more.

**What that means in practice:**

- **Comparing two places works right now.** "This aisle is 6 dB louder than that
  one" is correct out of the box, because the guess cancels out on both sides.
- **Tracking change over time works right now.** Same reason.
- **The absolute number is a guess** until you calibrate it. See
  [CALIBRATION.md](CALIBRATION.md).

**NEVER USE IT FOR** — Hearing protection decisions, or anything with a legal
limit. Phones distort above roughly 100–110 dB and a phone mic is not a
measuring instrument. If someone's hearing depends on the answer, get a real
meter.

**VERDICT** — The most useful thing in this repo, and it answers the question you
asked first: none of phyphox's built-in experiments measure decibels.

---

## Fan Tacho and Bearing Check

**WHAT IT DOES** — Two things at once.

**One: fan speed, from sound.** A fan with 7 blades spinning 20 times a second
pushes 140 puffs of air per second past any fixed point. That's a tone at 140 Hz.
Divide by the number of blades and you have the speed. Tell it how many blades,
it does the arithmetic and gives you RPM.

**Two: bearing health, from vibration.** A healthy bearing makes a smooth, even
buzz. A failing one makes sharp little cracks each time a ball rolls over a
damaged patch. The test measures **crest factor** — how spiky the vibration is
compared to its average. Smooth buzz, low number. Cracking, high number.

**WHY YOU CARE** — You get RPM without a tachometer or stopping the fan, and an
early warning on bearings. A bearing that's started cracking has months, not
years. Finding it during a walk beats finding it at 3am.

**WHERE** — Sound: within a metre or two of the fan, in its airflow if you can.
Vibration: phone flat against the fan housing or the frame, held firmly.

**WHEN** — Commissioning, or as a routine round. The bearing number is only
meaningful compared to itself over time — write it down.

**HOW**
1. **Blades on the impeller** — count them and type the number in. Get this wrong
   and the RPM is wrong by exactly that ratio.
2. **Search from / Search to** — the range of pitches to look in. Widen it if it
   locks onto the wrong thing.
3. **Fan speed (sound)** tab — hold the phone near the fan, read RPM.
4. **Vibration** tab — press the phone against the housing, read crest factor.

**WHAT GOOD LOOKS LIKE** — Crest factor around 3 to 4 is a healthy bearing.
Climbing past about 6 is worth watching. Past 10, get someone to look at it.
**The trend matters far more than the number** — a fan that's been 3.5 for a year
and is suddenly 5 is more interesting than one that's always read 6.

**WATCH OUT** — It can lock onto the wrong tone: a neighbouring fan, or a
harmonic (a whole-number multiple of the real tone — twice the pitch, three
times, and so on). If the RPM looks like exactly double or half what you expect,
that's what happened. Narrow the search range.

**VERDICT** — Genuinely useful, and does two unrelated jobs well.

---

## EMI Survey

**WHAT IT DOES** — Measures the magnetic field around you. Any wire with current
flowing makes one, and it gets weaker fast as you move away.

**WHY YOU CARE** — Running network cable alongside power cable is a classic
mistake. The power cable's field induces noise in the data cable and you get
errors that look like a bad cable, a bad port, or a bad switch — and you'll
replace all three before anyone suspects the tray. This finds the power runs so
you can route away from them, and it does it through walls, floors and ceilings.

Also finds live conductors where nothing is marked, which is more common than
anyone admits.

**WHERE** — Sweep slowly along walls, floors, cable trays, containment.

**WHEN** — Before pulling copper. When chasing errors that follow a route rather
than a device.

**HOW**
1. **EMI survey** tab. Walk slowly with the phone held flat.
2. Watch the number and the **peak hold** — the highest value it has seen, which
   stays on screen so you don't have to watch continuously while walking.
3. **Reset trace and peak hold** to start a fresh sweep.
4. **Axes** tab shows direction, which helps you tell where a cable runs.

**THE HONEST LIMIT** — Your phone's magnetometer reports about 100 times a
second. Mains power in a building alternates 50 or 60 times a second. There's a
hard rule that you need to sample **more than twice as fast** as the thing you're
measuring, and 100 is not more than twice 50 or 60. So this **cannot tell you
"that's mains hum" by frequency.** It sees the field is strong; it can't prove
what's making it.

That's fine for what you actually need — *this route is busier than that one* —
but it means the answer is comparative, not diagnostic.

**Also:** the building's steel is magnetic and so is the earth. There's a big
background field everywhere. Look at **changes** as you move, not absolute
values.

**VERDICT** — Useful, with a real limit stated honestly. Worth having on a phone.

---

## Vibration Census

**WHAT IT DOES** — Put the phone on the floor and it lists which pitches of
vibration are present. Every rotating machine puts its own signature into the
structure, so one recording tells you what's running.

**WHY YOU CARE** — Machines running that shouldn't be. A backup unit quietly
running alongside the duty unit for months, doubling energy for nothing, is a
real and common failure — and it's invisible on a walk-round because both units
look normal.

**WHERE** — Phone flat on the floor, screen up, hands off. On a raised floor,
directly over a pedestal if you can — the tiles themselves flex and blur it.

**WHEN** — A baseline once, then repeat monthly and compare. New peak that
wasn't there before = something new is running, or something old has changed.

**HOW**
1. **Set the phone down and leave it.** Any contact from your hand swamps
   everything. This is the single biggest cause of a useless reading.
2. **Census** tab lists the strongest pitches it found.
3. **Live spectrum** shows it as a graph, with **peak hold** so a brief event
   stays on screen.
4. **This phone's limits** tells you the highest pitch this phone can see.
5. **Clear the peak hold** to start again.

**READING IT** — Divide any peak by 60 to get RPM-ish numbers. 50 or 60 Hz is
mains. 100 or 120 Hz is usually a transformer or motor hum at twice mains.
Hard-disk shelves show up around 90 Hz (5400 rpm) or 120 Hz (7200 rpm).

**VERDICT** — Good, and gets better the more history you have. Useless as a
one-off; valuable as a monthly habit.

---

## Floor Tile Tap Test

**WHAT IT DOES** — Tap a raised-floor tile, listen to the note it rings at. A
properly supported tile rings high and dies fast. One that's lost a pedestal or
has a gap under it rings lower and rumbles on.

**WHY YOU CARE** — Loose tiles are a trip hazard, they leak air out of the
underfloor plenum, and they're a sign the grid is going. Finding them normally
means walking on every one and hoping you notice.

**WHERE** — Raised floor, obviously. Tap in the middle of a tile, same spot
every time, same knuckle or same tool. **Consistency matters more than technique.**

**WHEN** — Any floor survey. After work has been done under the floor.

**HOW**
1. Tap a tile you know is solid. Press **Set this tile as the reference**.
2. Walk the room. Tap each tile, press **Log this tile**.
3. **Next tile** advances the number so the log matches your floor plan.
4. Anything ringing well below the reference is worth a look.

**VERDICT** — Genuinely good. Nothing else in the toolkit finds this, it's fast,
and it's the sort of thing that saves an incident rather than producing a report.

---

## Dimension and Level Survey

**WHAT IT DOES** — Three things, and they're not equally good.

**Level and plumb — excellent.** Is this rack straight, is this floor flat, is
this rail true. Accurate to a hundredth of a degree.

**Distance by sonar — decent but fiddly.** Plays a chirp, listens for the echo,
times it. Works best on a big flat hard surface a few metres away.

**Air temperature from sound speed — a curiosity, not a tool.** Sound travels
faster in warm air, so timing it over a known distance gives temperature. See
below for why I'd ignore it.

**WHY YOU CARE** — Mostly the level. Racks out of plumb, floors out of flat, and
rails not true are real problems with real consequences, and the phone is
genuinely accurate at this.

**WHERE** — Level: phone flat against whatever you're checking. Sonar: point at a
big flat surface, stand still, keep the path clear.

**HOW**
1. **Level and plumb** — hold against the surface, keep still, read the angle.
2. **Distance** — point at a flat surface, press play, read.
3. **Waypoints** — **Record waypoint** saves a reading with a timestamp.

**WHY I'D SKIP THE THERMOMETER** — It needs you to type in a known distance, and
the sensitivity is brutal: **get the distance wrong by 1% and the temperature is
wrong by about 6 °C.** Over 10 metres, being 10 cm out ruins it. You'd need a
laser measure and great care to beat a $10 thermometer. It's real physics and it
works, but it isn't a useful instrument.

**VERDICT** — Keep it for the level, which is the most accurate thing in this
whole repo. Sonar is a bonus. The thermometer is a party trick.

---

## Magnetic Landmark

**WHAT IT DOES** — Every spot in a steel building has a slightly different
magnetic field, because of the steel around it. That makes an accidental
fingerprint for a location. Capture it at a spot, and later the test tells you
how close you are to that same spot.

The clever part: it uses two numbers that **don't change when you turn the phone
round** — the total strength of the field, and the angle between the field and
straight down. So it works regardless of which way you're facing, which is what
makes it usable while walking.

**WHY YOU CARE** — Repeat measurements are only comparable if they're taken in
the same place. "Third tile from the end, roughly" is not the same place. This
pins it down, needs no infrastructure, and costs nothing.

**WHERE** — Anywhere with steel, which is everywhere in a data hall.

**WHEN** — Whenever you'll want to come back to exactly this spot.

**HOW**
1. Stand where you want to remember. **Capture this spot.**
2. Later, walk around with the app running. The match score rises as you close in.
3. **Record a route** logs a series of numbered points along a path.

**WATCH OUT** — Anything ferrous that *moves* breaks it. A rack rolled in or out,
a new cabinet, a trolley left nearby — the fingerprint changes. It's a landmark,
not a survey monument.

**VERDICT** — Clever and useful if you do repeat readings. Pointless if you don't.

---

## Busway Load Indicator

**WHAT IT DOES** — Same measurement as the EMI Survey, presented for a different
job: hold the phone against a busway or feed and compare how hard each section is
working.

**WHY YOU CARE** — Spotting an unbalanced pair of feeds without opening anything
or clamping anything. In an A/B power setup they should be roughly even; if one
is much busier, someone has single-corded something they shouldn't have.

**WHERE** — Against the busway, same face, same distance, every time. **Distance
is everything** — the field drops off fast, so a few centimetres of difference
swamps a real difference in load.

**HOW**
1. **Set baseline here** at a reference point.
2. Walk the run, **Log section** at each tap-off.
3. **Capture as feed A** / **Capture as feed B** to compare two feeds directly.

**NOT AN AMMETER** — It cannot tell you amps. Ever. It tells you *this is busier
than that*, and only when you've held the phone identically both times.

**VERDICT** — Useful job, but it's the same instrument as the EMI Survey with a
different wrapper. See the review below — I think these two should be one app.

---

## Synchronised Walk Logger

**WHAT IT DOES** — Records everything the phone can sense, all at once, on one
clock, while you walk. Press a button to drop a marker at any point.

**WHY YOU CARE** — It's the recorder, not a test. Walk the hall once, get one
file with sound, vibration, magnetic field, pressure and light all lined up
against the same timestamps. Then work out what you wanted to know afterwards —
including things you didn't think to look for at the time.

**WHERE** — Everywhere. That's the point.

**HOW**
1. Press play at a known starting point.
2. Walk at a steady pace. **Waypoint** at each place worth marking.
3. Export as CSV at the end.

**HONEST ABOUT STEPS** — It counts your steps and can estimate distance, but step
length varies per person and per pace. Treat distance as approximate. The
waypoints are the reliable part.

**VERDICT** — Useful as a capture tool. Also the reason three other tests in this
repo are arguably redundant — see the review.

---

# The weaker ones

I'd rather tell you this than have you find out in an aisle.

---

## Rack Acoustic Signature

**WHAT IT DOES** — Record one healthy unit as a reference, then record each
identical unit in the row and score how different each sounds.

**WHY YOU CARE** — In a row of identical machines, the odd one out is usually the
one going wrong. A fan slowing, a different fan curve, a spinning disk that's
started whining.

**HOW** — **Set this unit as the reference**, then **Log this unit** down the row.

**WHY I'M LUKEWARM** — Three problems, all practical:
- A data hall is loud, and the noise from *everything else* is often bigger than
  the difference between two units.
- You have to hold the phone in exactly the same position at each unit or the
  comparison is meaningless, and "exactly" is hard while walking a row.
- The Vibration Census already finds most of what this finds, more robustly,
  because vibration through the frame doesn't have to compete with room noise.

**VERDICT** — Works in a quiet room. In a real hall, marginal. Try it, but don't
be surprised if the differences are noise.

---

## Hall Survey

**WHAT IT DOES** — Logs air pressure continuously and lets you type in
temperature and humidity at each point.

**WHY YOU CARE** — Pressure differences between hot aisle, cold aisle and plenum
are how you find air going where it shouldn't.

**THE PROBLEM** — Your phone's barometer is built to know roughly what floor
you're on. The pressure differences you care about in containment are far smaller
than what it can reliably see. It's also affected by doors opening and by weather.

And temperature and humidity are **typed in by hand**, because your phone almost
certainly has neither sensor — the Device Check will confirm that.

**VERDICT** — The pressure part is at the edge of what the hardware can do. The
typing-in part is a notebook with extra steps. It's the weakest of the "useful"
group, and the Walk Logger already records pressure.

---

## WiFi Walk Survey

**WHAT IT DOES** — Marks where you were and when, so WiFi signal readings from a
*different* app can be matched to locations afterwards.

**WHY IT'S ODD** — **phyphox cannot read WiFi at all.** Not signal strength, not
network names, nothing. It only gets the phone's sensors and WiFi isn't one.

So this does the half it can — the waypoints — and `tools/wifi_merge.py` joins
them to a WiFiAnalyzer export by time.

**BEFORE YOU BOTHER** — Android limits WiFi scans to about 4 every 2 minutes.
That's one reading every 30 seconds, which is useless if you're walking. Turn it
off in Settings → Developer options → Wi-Fi scan throttling, or the whole
exercise fails quietly.

**VERDICT** — The merging tool is good. But the phyphox half is just waypoints,
and the Walk Logger already does waypoints. See the review.

---

## Room Echo Signature

**WHAT IT DOES** — Plays a chirp, records the echoes, and uses the echo pattern
as a fingerprint for the room. Also estimates how "live" (echoey) the space is.

**WHY I'M SCEPTICAL** — This is the one I'd cut first.

- **As a way of finding a spot, it's worse than the magnetic version.** Echoes
  change when anything moves — a door, a trolley, a person. Steel doesn't.
- **As a reverberation measurement it isn't trustworthy.** Proper reverberation
  measurement needs a loud, controlled source and a calibrated mic. A phone
  speaker in a hall full of fan noise is neither.
- **A data hall is a bad room for it.** Constant broadband noise is exactly what
  drowns out an echo tail.

The maths in it is correct — it's the same proven chirp-and-correlate core as
the sonar. My doubt is about whether the measurement means anything in your
environment, which is a different and more important question.

**VERDICT** — Interesting, unconvincing here. Keep the Magnetic Landmark instead.

---

## Ultrasonic Leak Sweep

**WHAT IT DOES** — Listens for high-pitched hiss, above what most people hear.
Escaping gas through a small hole makes it.

**WHY I'M SCEPTICAL** — Two reasons, and the second is worse.

1. **Real leak detectors listen around 40 kHz. Phone mics stop around 20 kHz**
   and are already fading well before that. So this catches the very bottom edge
   of the signature at best. That's in the file already, honestly stated.
2. **A data hall may not have much compressed air.** Commercial ultrasonic
   detectors sell into compressed-air plants and industrial sites. Unless you
   have pneumatics, a compressor, or gas suppression pipework, there may be
   nothing here to find.

**WHERE IT MIGHT EARN ITS KEEP** — Gas suppression pipework, chiller plant,
anywhere with pneumatic actuators, and pressurised gas fittings generally.

**VERDICT** — Keep it only if you have compressed air on site. Otherwise it's a
test looking for a job.

---

## Strobe Tachometer — can't run yet

**WHAT IT WOULD DO** — Flashes the torch at a controlled rate. Speed the flashing
up or down until the fan blades appear to stop dead — a strobe effect. At that
point the flash rate equals the fan speed, and you've measured it **by eye**,
completely independently of any microphone.

**WHY IT MATTERS** — It's the honest check on the Fan Tacho. Two completely
different physical routes agreeing is real confidence; one method agreeing with
itself is not.

**WHY YOU CAN'T RUN IT** — Controlling the torch needs phyphox 1.2.1, which is
still a public beta. The current release is 1.2.0. The file is stamped for the
new version and will start working when the beta reaches you.

**IS ANYTHING BLOCKED?** — No. The Fan Tacho already cross-checks itself two ways
— blade tone from the mic, and imbalance from the accelerometer.

**WATCH OUT WHEN IT WORKS** — Blades also look frozen at half speed, a third,
a quarter and so on. Always confirm by checking the highest flash rate that
freezes them.

**Safety:** flashing light near moving machinery. Don't use it if anyone present
has photosensitive epilepsy, and remember a fan that *looks* stopped is spinning
at full speed. Never reach toward it.

---

# My honest review — what I'd change

You said you weren't convinced all of these are useful and that some should be
combined. You're right on both counts. Here's my assessment.

## Three sets that duplicate each other

**1. EMI Survey + Busway Load = one app.**
Identical measurement, identical gesture, identical sensor. The only difference is
the wording around it. One app with two tabs — *find the cable* and *compare the
feeds* — would be strictly better, and you'd stop having to remember which one to
open.

**2. Walk Logger + WiFi Walk + Hall Survey = one app.**
All three are "walk around, log readings, press a button at interesting spots."
The Walk Logger already records pressure and already has waypoints, which is
essentially all the other two contribute. Add a typed-in box for temperature,
humidity and WiFi signal and one app replaces three.

**3. Rack Signature + Room Echo Signature = one app, if kept at all.**
Both are: record a reference, record a candidate, score the difference. Same
machinery, different label. And I'm not convinced either survives a real hall.

## What I'd actually drop

- **Room Echo Signature** — the Magnetic Landmark does the same job better, and
  the reverberation figure isn't trustworthy in a noisy hall.
- **Ultrasonic Leak** — unless you have compressed air on site. Ask that question
  first; if the answer is no, delete it.
- **The sonar thermometer** inside the Dimension Survey — keep the distance and
  the level, bury the temperature.

## What that leaves

Sixteen becomes about ten, and every one of the ten earns its place:

Device Check · Sound Level Meter · Fan Tacho · Magnetic Survey *(EMI + busway)* ·
Vibration Census · Floor Tile Tap · Dimension & Level · Magnetic Landmark ·
Site Walk *(walk + WiFi + hall)* · Rack Signature *(on probation)*

## The one thing that argues against this

You asked, early on, for a guarantee that **a cheap A-series phone still gets at
least 12 working tests.** Merging takes the count to about ten, which breaks that
promise — not by removing capability, but by packing the same capability into
fewer icons.

So it's your call, and it's a real trade:

- **Keep 16** — hits the number you asked for, more things to learn, some overlap.
- **Merge to 10** — fewer, better, each one clearly worth opening. Nothing is
  lost except icons.

I'd merge. But you set that requirement for a reason, and I'm not going to
quietly drop it because I've changed my mind about it. Say the word either way.

---

# Two rules that apply to everything here

**1. Differences are trustworthy. Absolute numbers usually aren't.**
Almost every sensor in a phone is uncalibrated. Comparing two places, or the same
place over time, cancels out the unknown offset and is reliable. A single number
with a unit after it is a guess with a unit after it.

**2. A held phone is a moving phone.**
For anything measuring vibration, magnetism or angle, put it down. Your hand adds
far more movement than the thing you're trying to measure. This is the single
most common way to get a meaningless reading from any of these.
