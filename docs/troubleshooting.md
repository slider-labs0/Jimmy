# Troubleshooting

Every problem hit during the build, what caused it, and the fix. Ordered roughly
by how much time each one cost.

## I2C bus drops out intermittently

Symptom: `i2cdetect -y 1` sometimes shows the devices, sometimes shows nothing.
Scripts fail mid-read with `OSError: [Errno 121] Remote I/O error` even though
`i2cdetect` just passed.

Causes and fixes, in the order they were found:

1. **Bad breadboard.** A faulty board caused repeated dropouts. Direct-connecting
   the ADS1115 to the Pi worked every time. A breadboard adds a dozen spring
   contacts to the most timing-sensitive signals. Replace a suspect board, and
   direct-wire the four bus lines (VDD, GND, SDA, SCL) straight to the Pi header
   when in doubt.
2. **Long, chained jumper wires.** Two jumpers spliced together to make a 14-inch
   run put a mid-air junction on each I2C line. Use single short wires under
   ~20 cm, no chaining. This meant moving the Pi to a closer wall of the box.
3. **Bus speed too high for a marginal bus.** Set
   `dtparam=i2c_arm=on,i2c_arm_baudrate=10000` in `/boot/firmware/config.txt` and
   reboot. 10 kHz tolerates extra capacitance. The sub-Hz signal does not care.
4. **The diagnostic that isolates it:** direct-connect the ADS to the Pi with four
   M-F jumpers, no breadboard. If 0x48 appears, the fault is in the breadboard
   path. If not, it is the config or the board.

## Whole bus dies when the AD620 ground is connected

Symptom: bus is fine until the AD620 is fully powered, then both I2C devices
vanish. Rail-to-rail continuity checks are all open, so it is not a short.

Cause: the AD620 and its charge pump draw current in pulses. When its ground
return shared the same wire/rail the ADS used as its reference, those pulses
shifted the ADC's ground and knocked the bus over.

Fix: give the AD620 its own ground wire to a separate Pi ground pin (the Pi has
several: 6, 9, 14, 20, 25, 30, 34, 39). Star grounding, each board returning to
the Pi on its own path, stopped the disturbance.

## AD620 output railed at 3.3 V, trimpots do nothing

Symptom: `read_test.py` reads a flat ~3.3 V no matter how far the offset and gain
pots are turned.

Cause: the charge pump was not generating its negative rail, so the amplifier
could not swing its output down. Measured V- relative to GND and got ~0 V instead
of a negative voltage.

Root cause: VIN was only reaching 1 V instead of 5 V. A bad connection in the 5 V
path starved the board. The source (Pi 5 V pin) measured 5.13 V, so the loss was
in the wire between there and VIN.

Fix: run a single fresh wire from the Pi 5 V pin straight to VIN. VIN then read
5.13 V, V- swung to -4 V, and the output came off the rail. The offset pot then
moved the baseline normally. Keep VIN on a solid single wire, not a flaky
breadboard hop.

Note: "V- reads 0 V" with V- correctly open means check VIN first. The board was
not dead, it was underpowered.

## MCP4725 destabilizes the bus

Symptom: adding the MCP causes the same intermittent dropouts and I/O errors.

Likely causes:
1. Cold or cracked solder joint on an MCP header pin. Reflow all four.
2. Double pull-up resistors. Both the ADS and MCP carry pull-ups on SDA/SCL. Two
   in parallel can be too strong. Measure SDA-to-VCC resistance on each board; if
   both read low, remove one board's pull-ups or rely on the slow 10 kHz bus.

In this build, reflowing and firming the wiring was enough. After that the bus
held 0x48 and 0x60 across repeated `i2cdetect` runs.

## P0 import error

Symptom: `ImportError: cannot import name 'P0'` or
`AttributeError: type object 'ADS1115' has no attribute 'P0'`.

Cause: the channel constant moved between library versions.

Fix: use the raw channel number instead. `AnalogIn(ads, 0)` works regardless of
version. All scripts in this repo already use it.

## Signal looks real but matches the wet control

Symptom: electrodes in the live plate read much higher than the shorted noise
floor, but a damp paper towel reads almost the same.

Cause: wet electrodes in any ionic medium produce drift and junction potentials.
Most of the raw jump from dry-short to wet is "wet electrodes," not biology.

Fix: the control is the measurement. Compare the live plate to a dead-but-wet
control under identical conditions. Only the difference is biology. Use longer
runs and event counting rather than raw std dev, because fungal activity is slow
and bursty.

## Huge spikes after repositioning electrodes

Symptom: a burst of events, some hundreds of millivolts, right after moving a
needle mid-recording.

Cause: disturbing the electrode creates a large settling transient as the metal
re-equilibrates with the substrate. The 530 mV "events" in one run were this, not
the mushroom.

Fix: place electrodes, then leave them untouched for the whole run. Reject
anything above a sane biological amplitude (~80 mV) as an artifact. Real fungal
events are in the tens of millivolts.

## SSH drops kill a long run

Symptom: `client_loop: send disconnect: Connection reset` ends a recording.

Fix: run long jobs inside `tmux`. Start with `tmux`, run the script, detach with
Ctrl-b then d. Reattach with `tmux attach`. The job keeps running if the laptop
sleeps or the connection drops.

## Thermal throttling during inference

Check with `vcgencmd measure_temp` and `vcgencmd get_throttled` (0x0 means no
throttle). Heatsinks alone held up for the bursty read-then-generate workload. Add
an active cooler if `get_throttled` returns nonzero.
