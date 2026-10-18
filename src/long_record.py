"""
Long recording with event detection.

Records A0 for a set duration and counts events: sustained deviations from a
rolling baseline, in a biologically plausible amplitude range. Run it on a live
plate and on a dead control (wet paper towel or dead agar) under identical
conditions. Only the difference between the two counts as biology.

Recorded result for this build (1 hour each, untouched):
  live plate: 60 events, biggest 18.3 mV, std dev 41.7 mV
  wet control: 0 events, std dev 7.2 mV

Rules learned the hard way:
  - Place the electrodes, then do not touch them. Repositioning injects large
    fake spikes.
  - Reject anything over ARTIFACT_MV as a movement artifact. Real fungal events
    are in the tens of millivolts.
  - Run inside tmux so an SSH drop does not kill the run.
"""
import time
import numpy as np
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

# ---- edit per run ----
LABEL = "live"          # "live" for the plate, "wet" for the control
DURATION = 3600         # seconds (3600 = 1 hr)
SAMPLE_HZ = 10
AVG = 4                 # average N quick reads per sample
SPIKE_THRESH = 0.007    # V deviation from rolling baseline to count an event
BASELINE_SEC = 300      # 5-min rolling baseline so slow drift counts
MIN_EVENT_SEC = 2       # must stay over threshold this long to count
ARTIFACT_V = 0.080      # reject deviations bigger than this (mechanical)
# ----------------------

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
ads.gain = 1
chan = AnalogIn(ads, 0)

def read_avg():
    vals = []
    for _ in range(AVG):
        try:
            vals.append(chan.voltage)
        except OSError:
            pass
        time.sleep(0.002)
    return sum(vals) / len(vals) if vals else float('nan')

period = 1.0 / SAMPLE_HZ
win = int(BASELINE_SEC * SAMPLE_HZ)
min_len = int(MIN_EVENT_SEC * SAMPLE_HZ)
buf, samples, events = [], [], []
run_len, cur_peak = 0, 0.0
t0, next_report = time.time(), 60
fname = f"session_{LABEL}.csv"

print(f"Recording '{LABEL}' for {DURATION/60:.0f} min. Ctrl-C to stop early.")
with open(fname, "w") as f:
    f.write("t,volts\n")
    try:
        while time.time() - t0 < DURATION:
            v = read_avg()
            if v == v:                            # not NaN
                samples.append(v)
                f.write(f"{time.time()-t0:.3f},{v:.6f}\n")
                f.flush()
                buf.append(v)
                if len(buf) > win:
                    buf.pop(0)
                base = sum(buf) / len(buf)
                dev = abs(v - base)
                if SPIKE_THRESH < dev < ARTIFACT_V:
                    run_len += 1
                    cur_peak = max(cur_peak, dev)
                else:
                    if run_len >= min_len:
                        events.append(cur_peak)
                    run_len, cur_peak = 0, 0.0
            el = time.time() - t0
            cur_min = int(el // 60)
            if cur_min >= next_report:
                print(f"  {cur_min} min... {len(samples)} samples, {len(events)} events")
                next_report = cur_min + 1
            time.sleep(period)
    except KeyboardInterrupt:
        print("\nStopped early.")
if run_len >= min_len:
    events.append(cur_peak)

a = np.array(samples)
print(f"\n--- {LABEL.upper()} ---")
print(f"samples : {len(a)}")
print(f"mean    : {a.mean():.6f} V")
print(f"std dev : {a.std():.6f} V")
print(f"pk-pk   : {a.max()-a.min():.6f} V")
print(f"events  : {len(events)}  (> {SPIKE_THRESH*1000:.0f} mV, held "
      f"{MIN_EVENT_SEC}s+, vs {BASELINE_SEC/60:.0f}-min baseline)")
if events:
    print(f"biggest : {max(events)*1000:.1f} mV")
print(f"saved to {fname}")
