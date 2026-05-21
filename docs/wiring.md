# Wiring

**Board:** Seeed XIAO ESP32-C3.

## Pin assignments

| XIAO pin | GPIO | Role | Notes |
|----------|------|------|-------|
| D4 (SDA) | GPIO 6 | I²C SDA | Silkscreen-labeled SDA; clean GPIO (not strapping, not USB, not flash) |
| D5 (SCL) | GPIO 7 | I²C SCL | Silkscreen-labeled SCL |
| D1 | GPIO 3 | Push button | Active low, internal pull-up enabled in firmware |
| D2 | GPIO 4 | Battery ADC (optional) | Reads the midpoint of the BAT+/GND voltage divider; see [Battery monitoring](#battery-monitoring-optional) |
| 3V3 | — | Sensor power | Do NOT use the 5V pin — both sensors run fine at 3.3 V |
| GND | — | Common ground | |

Free for later use: D0 (GPIO 2, strapping — OK as output), D3 (GPIO 5), D6 (GPIO 21, UART TX), D7 (GPIO 20, UART RX), D8 (GPIO 8, strapping), D10 (GPIO 10). **Avoid** D9 (GPIO 9) — that's the BOOT strapping pin.

## Why these pins
- **SDA/SCL on D4/D5** — matches the XIAO silkscreen, keeps documentation honest, and both are clean GPIOs with no special-function conflicts.
- **Button on D1** — any "safe" GPIO works; D1 puts it adjacent to the GND pin on the header for a clean two-wire run.
- **Battery sense on D2** — must be an ADC-capable pin; the ESP32-C3's ADC1 channels are on GPIO 0–4, and D2/GPIO 4 is otherwise free.

## Sensor hookup

Both breakouts (Adafruit/SparkFun-style; verify your specific boards):

| SHT31-D pin | VL53L4CD pin | XIAO pin |
|-------------|--------------|----------|
| Vin / 3V    | Vin / VCC    | 3V3 |
| GND         | GND          | GND |
| SDA         | SDA          | D4 (GPIO 6) |
| SCL         | SCL          | D5 (GPIO 7) |

Sensor SDA lines share a single wire; sensor SCL lines share a single wire. The two breakouts have different I²C addresses (`0x44` and `0x29`) so they don't collide on the shared bus. Both breakouts include onboard 10 kΩ pull-ups — **don't add extras**; two in parallel already gives ~5 kΩ, which is on the strong side.

## Battery monitoring (optional)

The XIAO's ADC can't read the LiPo voltage directly — a charged cell sits above
the 3.3 V the ADC can measure, and there's no internal divider on the board. To
monitor the battery, add an external voltage divider: two equal resistors
between BAT+ and GND, with the midpoint feeding an ADC pin.

```
BAT+ ──┬── 100 kΩ ──┬── 100 kΩ ── GND
       │            │
   (battery)        └── to D2 (GPIO 4)
```

The midpoint sits at half the battery voltage — roughly 1.9 V at a 3.7 V cell,
2.1 V at a full 4.2 V — comfortably inside the ADC's range. The firmware doubles
the reading back to actual battery voltage and estimates a percentage from it.

Notes:
- **100 kΩ each** is the recommended value. The divider draws current
  continuously (battery voltage ÷ 200 kΩ ≈ 19 µA) — negligible. Much lower
  values waste battery; much higher values make the ADC reading noisy.
- The bottom resistor can connect to GND or directly to the LiPo's BAT−
  terminal — they're the same node.
- This is **optional**. Skip it and the firmware's battery sensors just report
  meaningless values, which is harmless — ignore or delete those entities.

## Breadboard layout

```
        XIAO ESP32-C3
        ┌─────────────┐
USB-C ─→│             │
        │  5V         │
        │  GND ───────┼──── breadboard GND rail
        │  3V3 ───────┼──── breadboard 3V3 rail
        │  D0/GPIO2   │
        │  D1/GPIO3 ──┼──── button ── GND
        │  D2/GPIO4 ──┼──── battery divider midpoint (optional)
        │  D3/GPIO5   │
        │  D4/GPIO6 ──┼──── SDA bus ──── SHT31-D SDA, VL53L4CD SDA
        │  D5/GPIO7 ──┼──── SCL bus ──── SHT31-D SCL, VL53L4CD SCL
        │  D6/GPIO21  │
        │  D7/GPIO20  │
        │  D8/GPIO8   │
        │  D9/GPIO9   │  ← avoid (BOOT strapping)
        │  D10/GPIO10 │
        └─────────────┘

SHT31-D:   Vin→3V3 rail, GND→GND rail, SDA→SDA bus, SCL→SCL bus
VL53L4CD:  Vin→3V3 rail, GND→GND rail, SDA→SDA bus, SCL→SCL bus
Button:    one leg → D1, other leg → GND   (firmware enables INPUT_PULLUP)
Battery:   BAT+ → 100kΩ → D2 → 100kΩ → GND   (optional; see Battery monitoring)
```

## Power notes

- USB-C from the XIAO powers the device and charges the LiPo.
- The LiPo solders to the BAT+ / BAT− pads on the XIAO's underside. The XIAO has onboard charge management — plug in USB to charge, run on battery when unplugged.
- Wi-Fi antenna is integrated. A U.FL connector is available for an external antenna if Wi-Fi signal is weak where the device lives.

## After wiring: the I²C scan

Before flashing the full firmware, flash the minimal `sourdough-scan.yaml` config (just the `i2c:` block with `scan: true`). The boot log should list two devices:

```
[I][i2c.idf:170]: Found i2c device at address 0x29   ← VL53L4CD
[I][i2c.idf:170]: Found i2c device at address 0x44   ← SHT31-D
```

If you see only one address, the most likely culprits, in order:
1. A loose wire on SDA or SCL to the missing sensor.
2. The missing sensor's Vin is not actually getting 3.3 V (check with a multimeter against GND).
3. SDA/SCL swapped at one of the breakouts.
4. (Rare) the breakout has a non-default ADDR jumper soldered, putting the sensor on `0x45` or `0x52` instead. Reflow if so.

Once both addresses scan cleanly, the wiring is verified — flash the full firmware (`sourdough.yaml`).
