# Recorded Results

All values measured on the rig described in docs/materials.md. Raw per-sample CSVs
(noise_floor.csv, session_live.csv, session_wet.csv) are produced by the scripts
and are not committed here.

## Noise floor

Amplifier inputs shorted, no mushroom, 5 minutes.

```
samples : 6869
mean    : 1.610182 V
std dev : 0.002789 V   (2.79 mV)
pk-pk   : 0.033500 V   (33.5 mV)
```

## Passive signal, short runs (context)

Early 5-minute runs showed that wet substrate alone reads far above the dry noise
floor:

```
shorted floor      std dev 2.79 mV   pk-pk 33.5 mV
live mushroom       std dev 11.69 mV  pk-pk 68.4 mV
wet paper towel     std dev 9.99 mV   pk-pk 67.1 mV
```

The wet towel reading close to the live plate is why the long controlled runs
below were needed. Raw std dev over a few minutes does not separate biology from
wet electrodes.

## Passive signal, 1-hour untouched runs

Event = sustained deviation over a 5-minute rolling baseline, held 2 s or more, in
the 7-80 mV range.

```
                 events   std dev   pk-pk    biggest event
wet towel           0      7.2 mV   54 mV    n/a
live mushroom      60     41.7 mV  151 mV    18.3 mV
```

Zero events on the dead control, sixty on the live plate, all biologically
plausible in size, arriving in bursts with quiet gaps. This is the primary result.

## Stimulation

0.82 V pulses, 3 s, through a 5.1 kOhm resistor into a stim electrode spaced from
the measurement pair.

Live plate, early pulses showed large positive spike changes that faded over the
session:

```
+12, +16, +38, +49, then falling to -8, -16, -14, with a late +30
```

The rising baseline over the session is consistent with electrode polarization
from repeated DC pulses, so the early responses are the strongest evidence.

Dead control, same pulses: baseline stayed flat, spike change never cleared +2,
mostly negative. The living network responds to stimulation in a way dead wet
substrate does not.

## Reading of the results

The hardware cleanly measures real voltages. The living plate produces electrical
activity that a dead-but-wet control does not, both passively and in response to
stimulation. The language model's text is produced entirely by the model; the
mushroom contributes the numbers that set temperature and mood.
