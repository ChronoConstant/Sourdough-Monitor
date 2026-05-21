# Sourdough Monitor

A small battery-powered device that watches a sourdough starter rise after
feeding and reports to Home Assistant. It measures the height of the starter
with a time-of-flight sensor, tracks temperature and humidity, and lets you
mark feedings with a button press — so you can see, from your phone or a wall
dashboard, exactly how far along your starter is and when it peaked.

Built on a Seeed XIAO ESP32-C3 running [ESPHome](https://esphome.io/),
publishing over MQTT. Fair warning... I am dumb, Claude built most of this. So please take everything with a grain of LLM flavored salt. 

<!-- Add a photo of your build here, e.g.:
![Sourdough Monitor](docs/images/prototype.jpg)
-->

## What it does

- **Measures starter height** with a VL53L4CD time-of-flight sensor aimed down
  into the jar from a lid-mounted enclosure.
- **Tracks the fermentation environment** — temperature and humidity from an
  SHT31-D.
- **Computes rise %** relative to the post-feed baseline, and tracks the
  maximum rise reached in the current cycle.
- **"Just Fed" button** — a press marks a new feed cycle: it archives the
  previous cycle's stats, resets tracking, and re-establishes the baseline.
  Mirrored as a Home Assistant button so you can also trigger it from a phone.
- **Runs for weeks on a battery** — deep sleep between readings gets roughly a
  month per charge on a 1200 mAh LiPo.
- **Home Assistant integration** — all values auto-discover over MQTT. Includes
  a ready-made dashboard card and a peak-detection sensor.

## How it works

```
[SHT31-D]  temp/humidity ──┐
                           ├── I²C ── [XIAO ESP32-C3] ── Wi-Fi ── MQTT ── [Home Assistant]
[VL53L4CD] distance ───────┤
[Push button] "Just Fed" ──┘
```

The ESP32-C3 wakes every ~15 minutes, takes a reading, publishes it over MQTT,
and goes back to deep sleep. A button press also wakes it. Home Assistant
receives the data via MQTT discovery — entities appear automatically, no manual
HA configuration of the sensors required.

**Rise tracking**: when you long press (because the button wakes the board it requires a 2 second or so press to allow time for the board to wake up and realized you're pressing the button) "Just Fed", the firmware discards the old
baseline. The next sensor reading becomes the new baseline; subsequent readings
update it downward if the starter settles further. Once the starter starts
rising, the baseline locks and rise % is measured against it. This adaptive
approach means there's no fixed "settling delay" to guess at — the baseline
naturally finds the low point of the cycle.

## Bill of materials

| Part | Notes |
|------|-------|
| **Seeed Studio XIAO ESP32-C3** | The MCU. Other ESP32-C3 boards can work but the pin map and the build guide assume the XIAO. |
| **VL53L4CD** time-of-flight sensor breakout | I²C. Measures the starter surface. A VL53L1X breakout also works — the driver supports both. |
| **SHT31-D** temperature/humidity breakout | I²C. Generic "SHT3x" breakouts work; see the troubleshooting doc re: the ADDR pin. |
| **Momentary push button** | Panel-mount, ~12 mm. The "Just Fed" input. |
| **LiPo battery, ~1200 mAh** | Single cell, 3.7 V, with a JST connector I snipped off to allow me to solder it to the board. The XIAO has onboard charging. |
| **2 × 100 kΩ resistors** | Optional — for the battery-voltage divider. Skip if you don't want battery monitoring. |
| **26–28 AWG wire** | Silicone-jacketed is easiest to work with. |
| **Tall straight-sided jar** | Weck / deli-quart style. Straight walls keep the rise math simple. |
| **3D-printed lid enclosure** | Holds everything; ToF aims down through a hole in the center. See [`enclosure/`](enclosure/). |

## Repository layout

```
.
├── README.md                  — this file
├── BUILD.md                   — step-by-step build & setup guide
├── LICENSE                    — GPLv3 (see "License" below)
├── firmware/
│   ├── sourdough.yaml          — the main ESPHome firmware
│   ├── sourdough-scan.yaml     — minimal I²C scanner for first bring-up
│   ├── secrets.yaml.example    — config template (copy to secrets.yaml)
│   └── components/vl53l1x/     — bundled ToF driver (third-party, see NOTICE)
├── homeassistant/
│   ├── lovelace-card.yaml      — dashboard card
│   └── peak-detection.yaml     — past-peak binary sensor + notification
├── enclosure/                  — 3D-printable lid STL files
└── docs/
    ├── wiring.md               — wiring guide
    └── troubleshooting.md      — common issues and fixes
```

## Quick start

Full instructions are in **[BUILD.md](BUILD.md)**. In short:

1. Wire the two I²C sensors and the button to the XIAO (see [`docs/wiring.md`](docs/wiring.md)).
2. Install [ESPHome](https://esphome.io/), copy `firmware/secrets.yaml.example`
   to `firmware/secrets.yaml`, and fill in your Wi-Fi and MQTT details.
3. Flash `firmware/sourdough.yaml` to the XIAO over USB.
4. The device's entities auto-appear in Home Assistant via MQTT discovery.
5. Calibrate the empty-jar distance, add the dashboard card, and you're done.

**Prerequisites**: Home Assistant with an MQTT broker (the Mosquitto add-on is
the usual choice).

## Home Assistant integration

Entities auto-discovered over MQTT include temperature, humidity, ToF distance,
starter height, rise %, max rise % this cycle, hours since feed, a battery
level, and the "Just Fed" button.

- [`homeassistant/lovelace-card.yaml`](homeassistant/lovelace-card.yaml) — a
  compact dashboard card (uses Mushroom + mini-graph-card from HACS).
- [`homeassistant/peak-detection.yaml`](homeassistant/peak-detection.yaml) — a
  template binary sensor that flips on when the starter has come off its peak,
  plus an example notification automation.

## Battery life

With deep sleep and a 15-minute wake interval, the device averages well under a
milliamp and runs roughly (hopefully?) **a month per charge** on a 1200 mAh LiPo. Charging is
over the XIAO's USB-C port. The optional resistor divider lets Home Assistant
display a battery percentage.

## Attribution

The VL53L4CD/VL53L1X driver in `firmware/components/vl53l1x/` is third-party
code from [Averyy/esphome-custom-components](https://github.com/Averyy/esphome-custom-components),
MIT licensed. It is bundled here (with a small i2c-API compatibility patch) so
the firmware builds reproducibly. See
[`firmware/components/vl53l1x/NOTICE`](firmware/components/vl53l1x/NOTICE) for
details of what was changed and why.

This project was developed with substantial help from Claude (Anthropic's AI
assistant) — firmware, and documentation.

## License

This project is licensed under the **GNU General Public License v3.0**. See the
`LICENSE` file. In short: you're free to use, modify, and distribute it, but
distributed derivatives must also be open-sourced under GPLv3.

The bundled `vl53l1x` component retains its original MIT license, which applies
to the files in that directory only. MIT is compatible with GPLv3.

## Contributing

Issues and pull requests welcome. If you build one, a photo and notes on what
you'd change are always appreciated.
