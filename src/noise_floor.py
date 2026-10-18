"""
Noise floor measurement.

Records A0 for five minutes and reports the baseline. Run it with the AD620 inputs
shorted (+S to -S) and no mushroom connected. Whatever this reports is what
"nothing" looks like on the rig. Every later event has to beat it.

Recorded baseline for this build: std dev 2.79 mV, peak-to-peak 33.5 mV.

Writes noise_floor.csv as it goes, so a mid-run crash keeps the data.
"""
import time
import statistics
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
ads.gain = 1                      # 3.3 V supply -> +/-4.096 V range
chan = AnalogIn(ads, 0)           # single-ended read on A0

DURATION = 300                    # seconds
vals = []
t0 = time.time()

print("Recording noise floor for 5 minutes... (Ctrl-C to stop early)")
with open("noise_floor.csv", "w") as f:
    f.write("t,volts\n")
    try:
        while time.time() - t0 < DURATION:
            v = chan.voltage
            vals.append(v)
            f.write(f"{time.time() - t0:.3f},{v:.6f}\n")
            f.flush()
            time.sleep(0.02)      # ~50 Hz
    except KeyboardInterrupt:
        print("\nStopped early.")

if vals:
    mean = statistics.mean(vals)
    std = statistics.pstdev(vals)
    pk_pk = max(vals) - min(vals)
    print("\n--- NOISE FLOOR ---")
    print(f"samples : {len(vals)}")
    print(f"mean    : {mean:.6f} V")
    print(f"std dev : {std:.6f} V   <-- your noise floor")
    print(f"pk-pk   : {pk_pk:.6f} V   <-- events must beat this")
    print("saved to noise_floor.csv")
else:
    print("No samples collected.")
