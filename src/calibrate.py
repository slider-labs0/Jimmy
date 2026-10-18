"""
Measure a plate's working range.

Samples 60-second windows and prints the spread and spike count for each, plus a
running min-max. Run it for five to ten minutes with the electrodes in a live
plate to find the real range, then set the mood thresholds in mushroom_llm.py from
what you see. The signal is episodic, so catch both quiet stretches and bursts.

Ctrl-C to stop.
"""
import time
import statistics
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

ads = ADS1115(busio.I2C(board.SCL, board.SDA))
ads.gain = 1
chan = AnalogIn(ads, 0)
ARTIFACT_MV = 80

def sample(seconds, hz=20):
    xs, end = [], time.time() + seconds
    while time.time() < end:
        try:
            xs.append(chan.voltage * 1000.0)
        except OSError:
            pass
        time.sleep(1.0 / hz)
    return xs

print("Sampling 60s windows - Ctrl-C to stop. Watch spread & spikes.")
spreads, spike_counts = [], []
while True:
    xs = sample(60)
    m = statistics.mean(xs)
    dev = [abs(v - m) for v in xs if abs(v - m) < ARTIFACT_MV]
    spread = statistics.pstdev(dev) if len(dev) > 1 else 0
    spikes = sum(1 for d in dev if d > 7)
    spreads.append(spread)
    spike_counts.append(spikes)
    print(f"spread={spread:5.1f}mV   spikes={spikes:3d}   "
          f"(spread range {min(spreads):.1f}-{max(spreads):.1f}, "
          f"spikes {min(spike_counts)}-{max(spike_counts)})")
