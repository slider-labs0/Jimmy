"""
Live single-channel read from the ADS1115 on A0.

Prints the amplifier output voltage about five times a second. Use it to bring up
the amplifier: short the AD620 inputs (+S to -S), run this, and turn the W103
offset trimpot until the reading sits near 1.6 V. The value moving when you turn
the pot proves the chain is alive end to end.

Ctrl-C to stop.
"""
import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
ads.gain = 1                      # 3.3 V supply -> +/-4.096 V range
chan = AnalogIn(ads, 0)           # single-ended read on A0

print("Reading A0 - Ctrl-C to stop")
while True:
    try:
        print(f"{chan.voltage:.4f} V   raw={chan.value}")
    except OSError:
        print("...read glitch, retrying")
    time.sleep(0.2)
