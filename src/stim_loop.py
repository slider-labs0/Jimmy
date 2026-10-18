"""
Stimulate, read the response, drive the model.

Each cycle: read a baseline, send a ~0.82 V pulse through the MCP4725 into the stim
electrode, wait for the network to react, read the response window, and compare.
The change in spike count maps to a reaction state and the model temperature.

Run it on a live plate and on a dead plate. Only the difference between the two
counts as a real reaction. In this build the live plate showed large early spike
increases (+12, +16, +38, +49) that faded with repeated pulses, while the dead
control stayed flat and never cleared +2.

Watch the baseline. Repeated DC pulses polarize the electrodes and can ramp the
baseline on their own. Space pulses out and keep sessions short. Keep voltage at
or below 1 V: the 5.1 kOhm series resistor limits current and STIM_V caps the DAC.

Ctrl-C to stop.
"""
import time
import statistics
import requests
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_mcp4725

MODEL = "llama3.2:3b"
STIM_V = 0.25          # normalized -> ~0.82 V at 3.3 V VCC
STIM_SEC = 3           # pulse duration
SETTLE_SEC = 5         # wait after the pulse before reading
READ_SEC = 30          # response read window
HZ = 20
ARTIFACT_MV = 80
SPIKE_MV = 7

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
ads.gain = 1
chan = AnalogIn(ads, 0)
dac = adafruit_mcp4725.MCP4725(i2c, address=0x60)

def set_dac(v):
    try:
        dac.normalized_value = v
        return True
    except OSError:
        print("...dac glitch")
        return False

def sample(seconds):
    xs, end = [], time.time() + seconds
    while time.time() < end:
        try:
            xs.append(chan.voltage * 1000.0)
        except OSError:
            pass
        time.sleep(1.0 / HZ)
    return xs

def features(xs):
    m = statistics.mean(xs)
    dev = [abs(v - m) for v in xs if abs(v - m) < ARTIFACT_MV]
    spread = statistics.pstdev(dev) if len(dev) > 1 else 0.0
    spikes = sum(1 for d in dev if d > SPIKE_MV)
    return spread, spikes

def ask(state, temp, seed):
    sys = (f"You speak as a living mycelium network that was just stimulated and "
           f"is now {state}. Respond in one or two short sentences, first person, "
           f"in that mood.")
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": MODEL, "system": sys,
        "prompt": "You were just touched. Say what you feel.",
        "options": {"temperature": temp, "seed": seed}, "stream": False,
    }, timeout=120)
    return r.json()["response"].strip()

print("STIMULATE -> READ -> LLM loop. Ctrl-C to stop.")
while True:
    print("\n>>> baseline read")
    base_spread, base_spikes = features(sample(READ_SEC))
    print(f"    baseline: spikes={base_spikes} spread={base_spread:.1f}mV")

    print(">>> stimulating ~0.82V for 3s")
    set_dac(STIM_V)
    time.sleep(STIM_SEC)
    set_dac(0.0)
    time.sleep(SETTLE_SEC)

    print(">>> response read")
    resp_spread, resp_spikes = features(sample(READ_SEC))
    d_spikes = resp_spikes - base_spikes
    print(f"    response: spikes={resp_spikes} spread={resp_spread:.1f}mV  "
          f"(change: {d_spikes:+d} spikes)")

    if d_spikes > 3:
        state = "jolted and reactive"
    elif d_spikes <= 0:
        state = "unmoved"
    else:
        state = "faintly stirred"
    temp = min(1.4, 0.6 + max(0, d_spikes) * 0.05)
    print(f"[{state}]  " + ask(state, temp, int(time.time()) % (2**31)))
