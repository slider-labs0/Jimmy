# Tutorial

This walks the full build from growing the mushroom to driving the model and
adding stimulation. Read `troubleshooting.md` alongside it; several steps map
directly to bugs that were hit during the build.

## Signal chain

```
mycelium -> electrodes -> AD620 amp -> 10 kΩ -> ADS1115 ADC -> I2C -> Raspberry Pi 5 -> Ollama -> text
                                                                        ^
optional stimulation:  Pi -> MCP4725 DAC -> 5.1 kΩ -> stim electrode ---+ (returns through the GND electrode)
```

The dish, electrodes, and AD620 go inside a grounded metal box. The Pi, ADS1115,
and MCP4725 stay outside it. The Pi is a noise source and the box shields the weak
signal from it. Only three wires cross the box wall: Vout, 5 V, and GND. Add a
fourth (the stim line) only when running stimulation.

## Phase 1 — Grow the mycelium

1. Mix MEA powder with distilled water in a mason jar at the packet ratio.
2. Sterilize: 2-3 cm of water in the pressure cooker, jar on a rack above the
   water, lid loose or foil over the top, 15 psi for 15-20 min. Let it cool
   gradually in the cooker.
3. Pour a shallow layer into each dish inside the still-air box. Let it set, then
   store inverted (agar-side up) so condensation drips onto the lid.
4. Shake the liquid culture, flame-sterilize the needle, inject a few drops onto
   each plate, re-flame between plates. Seal each dish edge with paper tape.
5. Incubate warm and dark 1-2 weeks until a dense connected white mat covers the
   dish. Toss any plate with green, black, or slimy growth or an off smell.
6. Use fuller/deeper dishes. Shallow dishes give a thin mat that reads substrate
   more than organism.

Pour one extra uninoculated plate as a sterility control. If it stays clean, your
technique and media are good.

## Phase 2 — Electrode front end

1. Shielded cable at the amp: red core to +S (J1), white core to -S (J1), shield
   pigtail to GND (J1). Ground the shield at the amp end only.
2. At the dish: clip the two signal cores to two needles about 2 cm apart and the
   pigtail to a reference needle. Tin the wire tips so the clips bite solid metal.
3. Clip rather than solder at the dish end while you are still finding good
   electrode spots.
4. Dish and AD620 go inside the grounded box.

## Phase 3 — Set up the Pi

```bash
sudo apt update && sudo apt full-upgrade -y
sudo raspi-config          # Interface Options -> I2C -> Enable
sudo reboot
sudo apt install -y i2c-tools python3-pip
pip install --break-system-packages adafruit-circuitpython-ads1x15 \
    adafruit-circuitpython-mcp4725 numpy scipy requests
sudo i2cdetect -y 1        # expect 0x48 (ADS1115), and 0x60 if the MCP is wired
```

If the bus is flaky, lower the I2C speed. Edit `/boot/firmware/config.txt` and set:

```
dtparam=i2c_arm=on,i2c_arm_baudrate=10000
```

Then reboot. The mushroom signal is sub-Hz, so bus speed does not affect it.

## Phase 4 — Wire and bias the amplifier

Wiring (power off):

| From | To |
|---|---|
| ADS1115 VDD | Pi 3.3 V (pin 1), never 5 V |
| ADS1115 GND | common ground |
| ADS1115 SCL | Pi GPIO3 (pin 5) |
| ADS1115 SDA | Pi GPIO2 (pin 3) |
| ADS1115 A0 | AD620 Vout through the 10 kΩ |
| AD620 VIN | Pi 5 V (pin 2) |
| AD620 GND | its own wire to a separate Pi ground pin (see troubleshooting) |
| AD620 V- | nothing |

Set the operating point:

1. Short +S to -S together.
2. Run `read_test.py`.
3. Turn the W103 (offset) trimpot until the reading sits around 1.6 V. The signal
   needs room to swing both up and down. If it will not come off the top rail,
   confirm V- reads negative and that VIN reads a full 5 V.

## Phase 5 — Noise floor

With +S/-S still shorted, run:

```bash
python3 noise_floor.py
```

It records 5 minutes and prints std dev and peak-to-peak. Write those numbers
down. Every later event has to beat them. Recorded baseline for this build was
std dev 2.79 mV, peak-to-peak 33.5 mV.

## Phase 6 — Read a live plate and control it

1. Un-short +S/-S and clip the electrodes to a live colonized plate, agar-side
   down, lid off, inside the box.
2. Run `long_record.py` with `LABEL = "live"` for an hour. Leave it untouched the
   whole time. Repositioning mid-run injects large fake spikes.
3. Run it again with `LABEL = "wet"`, needles in a damp paper towel or dead plate,
   same spacing and duration.
4. Compare event counts and amplitudes. The live plate should produce more events
   in the tens-of-millivolts range than the dead control. Recorded result: live 60
   events, dead 0.

Run everything inside `tmux` so an SSH drop does not kill a long run:

```bash
tmux
python3 long_record.py
# detach with Ctrl-b then d, reattach with: tmux attach
```

## Phase 7 — Drive the model

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
ollama run llama3.2:3b "hello"
```

Calibrate to your plate first:

```bash
python3 calibrate.py       # watch the spread and spike range for a few minutes
```

Set the mood thresholds in `mushroom_llm.py` from the range you observe, then:

```bash
python3 mushroom_llm.py
```

Each cycle samples the plate, extracts spread and spike count, drops anything over
80 mV as a movement artifact, and maps the result to the model temperature and a
mood word in the prompt.

## Phase 8 — Stimulation (optional)

1. Reflow the MCP4725 header joints and wire it to the shared bus with short firm
   single wires. Confirm `i2cdetect -y 1` holds 0x48 and 0x60 across several runs.
2. Wire MCP OUT through a 5.1 kΩ resistor to a stim electrode placed away from the
   measurement pair. The return path is the existing GND electrode.
3. Bench-test the output before it touches the plate:

```bash
python3 stim_test.py       # meter on OUT to GND, confirm it swings 0 to ~0.82 V
```

4. Run the loop:

```bash
python3 stim_loop.py
```

5. Run it on a dead plate too. Only the difference between the live and dead
   response counts as a real reaction.

Keep stimulation at or below 1 V. The series resistor limits current and the
software caps the DAC value. More than that risks electrolysis at the electrodes
or cooking the tissue.
