"""
Route the mushroom signal into a local language model.

Every cycle: sample the plate over a window, extract the spread and spike count,
drop anything over 80 mV as a movement artifact, and map the result to the model
temperature and a mood word in the system prompt. An active plate pushes the text
looser. A calm one settles it.

The model supplies all of the words. The mushroom supplies a spike count and a
spread value that set two knobs. The thresholds below are tuned to one plate
(spikes 7-19, spread nearly flat near 2 mV). Run calibrate.py and retune to yours.

Needs Ollama running with the model pulled:
    ollama pull llama3.2:3b

Ctrl-C to stop.
"""
import time
import statistics
import requests
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

MODEL = "llama3.2:3b"
WINDOW_SEC = 60          # sample the plate this long before each generation
HZ = 20
ARTIFACT_MV = 80         # ignore excursions bigger than this
SPIKE_MV = 7             # deviation (mV) from window mean that counts as a spike

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)
ads.gain = 1
chan = AnalogIn(ads, 0)

def sample(seconds, hz):
    xs, end = [], time.time() + seconds
    while time.time() < end:
        try:
            xs.append(chan.voltage * 1000.0)       # mV
        except OSError:
            pass
        time.sleep(1.0 / hz)
    return xs

def features(xs):
    m = statistics.mean(xs)
    dev = [abs(v - m) for v in xs if abs(v - m) < ARTIFACT_MV]
    spread = statistics.pstdev(dev) if len(dev) > 1 else 0.0
    spikes = sum(1 for d in dev if d > SPIKE_MV)
    return spread, spikes

def mood(spikes):
    # tuned to one plate: spikes ~7-19
    if spikes >= 15:
        return "agitated and restless"
    if spikes <= 8:
        return "calm and dormant"
    return "quietly stirring"

def ask(state, temperature, seed):
    sys = (f"You speak as a living mycelium network that is currently {state}. "
           f"Respond in one or two short sentences, first person, in that mood.")
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": MODEL, "system": sys,
        "prompt": "Say what you sense right now.",
        "options": {"temperature": temperature, "seed": seed},
        "stream": False,
    }, timeout=120)
    return r.json()["response"].strip()

print("Mushroom -> LLM loop. Ctrl-C to stop.")
while True:
    xs = sample(WINDOW_SEC, HZ)
    if len(xs) < 5:
        print("...read glitch, retrying")
        continue
    spread, spikes = features(xs)
    state = mood(spikes)
    temp = min(1.4, 0.5 + (spikes - 7) * 0.06)        # 7 spikes -> 0.5, 19 -> ~1.2
    seed = int(abs(xs[-1]) * 1000) % (2**31)          # signal -> entropy
    print(f"\n[{state}]  spikes={spikes}  spread={spread:.1f}mV  temp={temp:.2f}")
    print("  " + ask(state, temp, seed))
