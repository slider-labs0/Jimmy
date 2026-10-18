"""
Bench-test the DAC output before it touches the mushroom.

Pulses the MCP4725 output between 0 and a capped safe level. Put a multimeter on
OUT to GND and confirm it swings between 0 V and about 0.82 V. This is the safety
check: the thing on the other end of the wire is alive, so the voltage is proven
under 1 V before any pulse reaches tissue.

MCP4725 output spans 0..VCC across normalized_value 0..1. At 3.3 V VCC, 0.25 gives
about 0.82 V. Lower MAX_SAFE if your meter reads higher than expected.

Ctrl-C to stop.
"""
import time
import board
import busio
import adafruit_mcp4725

i2c = busio.I2C(board.SCL, board.SDA)
dac = adafruit_mcp4725.MCP4725(i2c, address=0x60)

MAX_SAFE = 0.25          # ~0.82 V at 3.3 V VCC, safely under 1 V

print("Pulsing OUT between 0 and MAX_SAFE. Measure OUT with a multimeter. "
      "Ctrl-C to stop.")
while True:
    try:
        dac.normalized_value = MAX_SAFE
        print(f"HIGH ~{MAX_SAFE*3.3:.2f} V")
        time.sleep(3)
        dac.normalized_value = 0.0
        print("LOW 0 V")
        time.sleep(3)
    except OSError:
        print("...dac write glitch")
        time.sleep(1)
