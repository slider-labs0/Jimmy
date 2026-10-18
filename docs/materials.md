# Bill of Materials

Prices are approximate. Items marked owned were already on hand during the build.

## Compute and power

| Part | Role | Notes |
|---|---|---|
| Raspberry Pi 5 | Runs everything | 64-bit Raspberry Pi OS |
| 27 W USB-C PSU | Pi power | Official supply |
| 128 GB microSD | Storage | Model is ~2 GB, loads to RAM |
| Heatsinks | Cooling | Passive held fine for bursty load; confirm with `vcgencmd get_throttled` |

## Biology

| Part | Role | Notes |
|---|---|---|
| Oyster liquid culture syringe | The wetware | Pleurotus, food-safe, BSL-1 |
| Petri dishes (plastic, sterile) | Grow vessels | Use fuller/deeper dishes; shallow ones give a thin mat and weak signal |
| Malt Extract Agar (MEA) powder | Growth medium | Pre-mixed, add distilled water |
| Distilled water | Media mixing | Tap minerals add noise and contamination risk |
| Pressure cooker + mason jar | Sterilize media | 15 psi, 15-20 min, water in the bottom, jar on a rack, lid loose |
| Still-air box | Clean workspace | A clear storage tote works |
| Paper / micropore surgical tape | Seal dishes | Breathable; cling wrap works in a pinch, micropore is better |
| Isopropyl alcohol | Sterilize surfaces and tools | 70% |
| Lighter | Flame-sterilize the syringe needle | Between plates |

## Analog front end

| Part | Role | Notes |
|---|---|---|
| AD620 instrumentation amplifier module (XY-FD) | Boost the microvolt signal | Charge-pump type with a V- pin. Confirm V- reads negative before trusting a board |
| ADS1115 ADC breakout (generic) | 16-bit I2C digitizer | No level shifting, so VDD runs at 3.3 V |
| MCP4725 DAC | Stimulation output | I2C, address 0x60 |
| Stainless steel needles | Electrodes | Acupuncture needles or 3D-printer nozzle cleaners, ~0.2-0.3 mm |
| Alligator clip leads | Electrode connections | Clip to needle handles; lets you reposition freely |
| Shielded 2-core cable | Electrode-to-amp leads only | Short as possible, under 15 cm; braid to GND at the amp end only |
| 10 kΩ resistor | ADC input protection | Inline on Vout to A0 |
| 5.1 kΩ resistor | Stimulation current limit | Inline on MCP OUT to the stim electrode |
| Full-size breadboard (830-point) | Shared I2C bus and power rails | Buy a decent one; a bad board caused hours of debugging |
| Jumper wires (M-M, M-F, F-F) | Board-to-board wiring | Single wires, no chaining on I2C lines |
| 2.54 mm male header pins | Solder onto the ADS1115 | 40-pin breakaway strip |

## Enclosure and grounding

| Part | Role | Notes |
|---|---|---|
| Metal ammo can or cookie tin | Faraday enclosure | Must be actual metal, grounded at one point |
| M6 bolt, nut, star washer, flat washer | Cage ground bond | Scratch to bare metal, star washer bites |
| Plain hookup wire | Cage ground wire | A jumper works; not shielded |
| Velcro / foam tape / standoffs | Mount boards off the metal | Keeps bare solder joints from shorting on the cage |

## Test gear

| Part | Role |
|---|---|
| Multimeter | Continuity, voltage, bring-up debugging. Non-negotiable |
| 9 V battery (optional) | Cleaner amp power if the Pi 5 V rail is noisy |

## Reused across the whole build

Faraday cage, grounding scheme, noise-floor discipline, and the dead-plate control
method all carry forward to later projects.

## AD620 XY-FD pinout

```
J1 (input side):  +S   -S   GND   VIN
J3 (output side): GND  Vout  GND   V-
Trimpots:         W103 = offset    W104 = gain
```

- +S / -S: electrode signal pair
- GND (J1): shield braid / reference electrode
- VIN: 5 V power
- Vout: through 10 kΩ to ADS1115 A0
- V-: leave connected to nothing. It is the charge-pump negative rail. Grounding
  it or wiring it to anything kills the board.
