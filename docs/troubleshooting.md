# Troubleshooting

Every issue here was hit during the development of this project. If you run
into something, there's a decent chance the answer is below.

---

## Sensors and wiring

### Only one I2C sensor shows up

The I²C scan finds one address but not the other (you want both `0x29` for the
VL53L4CD and `0x44` for the SHT31-D).

Check, in order:

1. **A loose wire** to the missing sensor — SDA, SCL, VIN, or GND. With the
   device powered, measure each pin on the missing sensor's breakout against
   GND: VIN should read ~3.3 V, SDA and SCL should idle near 3.3 V.
2. **SDA/SCL swapped** at the missing breakout.
3. **The chip is simply dead.** Cheap sensor breakouts have a high failure
   rate. Also sometimes you might get a counterfeit off amazon. If power, ground, and both bus lines measure correct at the breakout
   and it still doesn't answer at any address, replace it. (This happened to
   me — the first SHT31-D was dead on arrival despite perfect wiring.)

---

## ESPHome and flashing

### `vl53l4cd` / `vl53l1x` platform not found

The VL53L4CD is **not in ESPHome core**. This project bundles a working driver
in `firmware/components/vl53l1x/` and the firmware references it via a local
`external_components` entry — so a normal build just works.

If you ever swap in the upstream component fresh from
[Averyy/esphome-custom-components](https://github.com/Averyy/esphome-custom-components)
and the build fails with errors like *"candidate expects 3 arguments, 4
provided"* on `write_register16` / `read_register16` — that's an ESPHome i2c
API change the upstream hasn't caught up with. The fix is the patch already
applied to the bundled copy: remove the 4th argument (a `true`/`false`) from
those five calls. See `firmware/components/vl53l1x/NOTICE`.

### ESPHome installs an old version

If `esphome version` reports an old release (2025.x or earlier), your Python is
too old. ESPHome needs **Python 3.10+**; older Python silently pins ESPHome to
its last compatible release. Check `python3 --version`. On macOS the system
Python is often 3.9 — install a newer one (e.g. `brew install python@3.12`) and
reinstall ESPHome.

### Build fails on whitespace in path

Error: *"Detected a whitespace character in project paths."* ESP-IDF's build
system cannot handle spaces anywhere in the path to the project. Rename the
project folder (and any parent folders) to use underscores or dashes instead
of spaces, then rebuild.

### Flashing fails to connect over USB

Symptom: `Failed to connect to ESP32-C3: Wrong boot mode detected` or the
upload just times out. macOS especially struggles to auto-reset the XIAO into
download mode.

Fix — put the chip into download mode manually:

1. Hold down the **B** (Boot) button on the XIAO.
2. While holding B, tap the **R** (Reset) button and release it.
3. Release B.
4. Immediately re-run the flash command.

The chip is now in the ROM bootloader and esptool can connect reliably.

---

## Firmware behavior

### Rise % reads 0 for a while after a feed

Expected. After a "Just Fed" press the baseline is discarded; the next sensor
reading (up to one ~15-minute wake cycle away) establishes the new baseline.
Until then Rise % reads 0 — there is no baseline to measure against yet. Once
the new baseline is set, it starts climbing normally.

### Battery Voltage / Battery Level show nonsense

Those entities only mean something if you wired the optional voltage divider
(two 100 kΩ resistors, BAT+ → divider → GPIO 4 → GND). Without it, GPIO 4
floats and the readings are garbage. Either wire the divider or delete the
`adc` and battery `template` sensors from `sourdough.yaml`.

---

## Home Assistant

### Distance shows in inches instead of mm

Home Assistant auto-converts the display units of any sensor with a
`device_class` of `distance`, based on your account's unit system. This
firmware sets `device_class: ""` on the distance-type sensors specifically to
suppress that conversion. If you see inches anyway, confirm those `device_class:
""` lines are present, or switch your HA unit system to metric.

### Entities don't appear in Home Assistant

- Confirm the device actually connected to Wi-Fi and MQTT — check
  `esphome logs sourdough.yaml`.
- Confirm Home Assistant's MQTT integration is set up and pointed at the same
  broker.
- The MQTT discovery prefix must match (`homeassistant`, the default on both
  sides).

### Device shows "unavailable" in HA between readings

By default this firmware disables MQTT birth/will messages (see the `mqtt:`
block), specifically so HA does *not* mark everything unavailable each time the
chip sleeps. If you re-enable them, HA will flip every entity to "unavailable"
for the ~15 minutes between wakes. That's the trade-off — the device genuinely
is offline while asleep.

---

## Networking

### Device won't connect to Wi-Fi

- The ESP32-C3 is **2.4 GHz only**. It cannot see a 5 GHz network, even if your
  router shares one name across both bands (it'll just use the 2.4 GHz one — but
  confirm 2.4 GHz is enabled).
- The SSID is **case-sensitive**. `MyNetwork` and `mynetwork` are different
  networks. Copy it exactly.

### MQTT won't connect — "Couldn't resolve IP address"

The `mqtt_broker` value in `secrets.yaml` must be the address **only** — no
port. `192.168.1.10`, not `192.168.1.10:1883`. The port is configured
separately (and defaults to 1883).

### MQTT won't connect — "Connection refused, error 0x5"

That's MQTT's "Not Authorized" code — the broker rejected the login. The Home
Assistant Mosquitto add-on does **not** allow anonymous connections by default.
Create a Home Assistant user for the device and put those credentials in
`secrets.yaml` as `mqtt_username` / `mqtt_password`.

### Router shows the device connected for ~5 minutes after it sleeps

Cosmetic, not a real problem. When the ESP32-C3 enters deep sleep it powers the
Wi-Fi radio off without sending a clean disassociation frame, so the router
doesn't notice immediately and prunes the device on its own inactivity timeout
(often ~5 minutes). The device really is asleep and saving power — the router's
connected-devices list is just stale. Ground truth is the deep-sleep log line
and the battery drain rate.
