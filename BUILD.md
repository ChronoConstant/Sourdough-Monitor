# Build Guide

Step-by-step instructions to build and set up a Sourdough Monitor. Plan on an
afternoon for the electronics and first flash, plus printing time for the
enclosure.

If something goes wrong, check [`docs/troubleshooting.md`](docs/troubleshooting.md)
first — most of the common snags are documented there with fixes.

---

## Before you start

You'll need:

- The parts in the [bill of materials](README.md#bill-of-materials).
- A **Home Assistant** instance with an **MQTT broker**. The
  [Mosquitto add-on](https://www.home-assistant.io/integrations/mqtt/) is the
  standard choice. If you don't have MQTT set up yet, do that first — the
  device has nowhere to publish to without it.
- A computer to run **ESPHome** (Windows, macOS, or Linux). The build guide
  uses the ESPHome command line.
- A **USB-C data cable** (not a charge-only cable) for the first flash.
- Basic soldering tools.

A note on skill level: this is an intermediate project. You don't need to be an
electronics expert, but you should be comfortable soldering small wires and
editing a YAML text file.

---

## Step 1 — Wiring

Full pin-by-pin detail is in [`docs/wiring.md`](docs/wiring.md). Summary:

| Connection | XIAO ESP32-C3 pin |
|------------|-------------------|
| Both sensors: VIN | `3V3` |
| Both sensors: GND | `GND` |
| Both sensors: SDA | `D4` (GPIO 6) |
| Both sensors: SCL | `D5` (GPIO 7) |
| Push button (one leg) | `D1` (GPIO 3) |
| Push button (other leg) | `GND` |
| LiPo battery | `BAT+` / `BAT−` pads (underside) |

Both I²C sensors share the same SDA and SCL wires — they have different
addresses (`0x44` and `0x29`) so they coexist on one bus. Most sensor breakouts
include their own pull-up resistors; don't add more.

For the **optional battery monitor**, wire a voltage divider — two 100 kΩ
resistors in series between `BAT+` and `GND`, with the midpoint going to
`D2` (GPIO 4). See Step 9.

**Tip**: before committing to soldered connections, build it on a breadboard
and confirm both sensors respond (Step 4). It's much easier to fix a wiring
mistake before everything is soldered into an enclosure.

---

## Step 2 — Install ESPHome

ESPHome needs **Python 3.10 or newer**. Check with `python3 --version`.

Install ESPHome (pipx keeps it cleanly isolated):

```bash
pip install pipx       # if you don't have pipx
pipx install esphome
```

Or with plain pip: `pip install esphome`.

Confirm it works: `esphome version`. You want a current release — if it
installs something old (2025.x or earlier), your Python is probably too old;
see [troubleshooting](docs/troubleshooting.md#esphome-installs-an-old-version).

---

## Step 3 — Configure your secrets

The firmware reads Wi-Fi and MQTT settings from a `secrets.yaml` file that you
create from the template.

```bash
cd firmware
cp secrets.yaml.example secrets.yaml
```

Open `secrets.yaml` and fill in your values. The file is commented with what
each one means. At minimum you need `wifi_ssid`, `wifi_password`,
`mqtt_broker`, and `ota_password`. Notes:

- The ESP32-C3 only does **2.4 GHz Wi-Fi** — it cannot see a 5 GHz network.
- The Wi-Fi SSID is **case-sensitive**.
- `mqtt_broker` is just the IP/hostname — **no `:1883` port suffix**.
- If your broker requires a login, set `mqtt_username` / `mqtt_password`. If
  it's anonymous, set them to empty strings (`""`).

### Optional: static IP

By default the device uses DHCP, which works on any network with zero extra
configuration — you can skip this entirely.

If you'd like a small battery-life improvement, you can give the device a
static IP. It saves the ~1–2 seconds of DHCP negotiation on every deep-sleep
wake. To enable it:

1. In `firmware/sourdough.yaml`, find the `wifi:` block and **uncomment the
   `manual_ip:` block** (remove the leading `#` from those five lines).
2. In `secrets.yaml`, **uncomment and fill in** the `static_ip`, `gateway`,
   `subnet`, and `dns1` values.
3. For `static_ip`, pick an address that's **outside your router's DHCP pool**
   (check the router's DHCP range), or reserve the address in your router by
   the device's MAC. This avoids the static IP colliding with an address the
   router might hand out to something else.
4. `gateway` is your router's IP, `subnet` is almost always `255.255.255.0`,
   and `dns1` is usually your router's IP.

Do this before flashing (Step 5). If you set it up later, just re-flash. And if
the device ever fails to connect after enabling it, the values almost certainly
don't match your network — comment the `manual_ip:` block back out to fall back
to DHCP.

---

## Step 4 — Verify the sensors (I²C scan)

Before flashing the full firmware, flash the minimal scanner config. This just
brings up the I²C bus and prints what it finds — a quick sanity check that your
wiring is correct.

```bash
esphome run sourdough-scan.yaml
```

For the **first flash you must use USB** (there's no firmware on the chip yet
for an over-the-air update). When prompted, choose the USB/serial device.

**macOS / Windows users**: if the upload fails to connect, you need to put the
XIAO into download mode manually — hold the **B** (Boot) button, tap **R**
(Reset), release **B**, then immediately retry. See
[troubleshooting](docs/troubleshooting.md#flashing-fails-to-connect-over-usb).

In the log output, you're looking for **both** sensor addresses:

```
Found i2c device at address 0x29   ← VL53L4CD
Found i2c device at address 0x44   ← SHT31-D
```

If only one shows up, fix the wiring before going further — the
[troubleshooting doc](docs/troubleshooting.md#only-one-i2c-sensor-shows-up) has
a checklist.

---

## Step 5 — Flash the firmware

Once both sensors scan cleanly, flash the real firmware:

```bash
esphome run sourdough.yaml
```

Same as before — USB for this first flash, BOOT/RESET dance if it won't
connect. The compile takes a few minutes the first time (it downloads
toolchains and builds the bundled component).

After this first USB flash, **future updates can be done wirelessly** — run the
same command and pick the network/OTA option.

> **Path gotcha**: ESP-IDF cannot build from a path containing spaces. If your
> project folder has spaces in its name, the build fails with "Detected a
> whitespace character in project paths." Rename the folder to use underscores
> or dashes. (See [troubleshooting](docs/troubleshooting.md#build-fails-on-whitespace-in-path).)

---

## Step 6 — Confirm entities in Home Assistant

The firmware publishes over MQTT with discovery enabled, so Home Assistant
picks up the device automatically. Within a minute or two of the device's first
boot, go to **Settings → Devices & Services → MQTT** and you should see a
"Sourdough Monitor" device with entities: Temperature, Humidity, ToF Distance,
Starter Height, Rise %, Max Rise % This Cycle, Hours Since Feed, Battery
Voltage / Level, and a "Just Fed" button.

If nothing appears, check the device log (`esphome logs sourdough.yaml`) for
the Wi-Fi and MQTT connection lines.

---

## Step 7 — Calibrate the empty-jar distance

The firmware needs to know the distance from the sensor down to the bottom of
the empty jar (`d_empty`) to compute starter height.

1. Put a small piece of **white paper** flat in the bottom of the **empty**
   jar. (Glass and clear plastic can be partly transparent to the sensor's
   infrared — the paper gives it a clean surface to range against.)
2. Put the lid/enclosure on the jar in its normal position.
3. Watch the **ToF Distance** entity in Home Assistant. Let it report a few
   readings and note the stable value (in mm).
4. In Home Assistant, find the **Empty Jar Distance (mm)** number entity and
   set it to that value.

That's it. The starter-height and rise-% math now have their reference point.
If you ever change how the lid sits on the jar or use a new jar, redo this.

---

## Step 8 — Add the dashboard card

[`homeassistant/lovelace-card.yaml`](homeassistant/lovelace-card.yaml) is a
compact card for a Home Assistant dashboard. It uses two cards from
[HACS](https://hacs.xyz/): **Mushroom** and **mini-graph-card** — install those
first.

Then, on a dashboard: **Edit → Add Card → Manual**, and paste in the contents
of `lovelace-card.yaml`. If your device entities have different IDs than the
defaults, adjust the entity names in the card (they're all near the top of each
section).

---

## Step 9 — Battery monitoring (optional)

If you wired the voltage divider (Step 1), the **Battery Voltage** and
**Battery Level** entities will show real values. If you didn't, those entities
just report nonsense — harmless, ignore them or remove the `adc` and battery
`template` sensors from `sourdough.yaml`.

To verify the divider: with the device powered, measure between `D2` (GPIO 4)
and `GND` — it should read about half the battery voltage.

---

## Step 10 — Peak detection (optional)

[`homeassistant/peak-detection.yaml`](homeassistant/peak-detection.yaml)
contains a Home Assistant template binary sensor that flips on when the starter
has come off its peak, plus an example notification automation. The file is
commented with where each piece goes in your HA config and what to tune. It's
optional — the monitor is fully usable without it.

---

## Using it day to day

**To mark a feeding**: Push the button before removing the lid to avoid a crazy reading when you set it aside. feed the starter, put the lid back on the jar, and
press the button. (If the device is asleep, hold the button for about a second or two
so the press registers as it wakes up.)

What happens: the previous cycle's stats get archived, rise tracking resets, and
"Rise %" shows 0 until the next sensor reading establishes the new
baseline — up to ~15 minutes later. After that, watch the rise climb.

**Charging**: plug a USB-C cable into the XIAO. With deep sleep the battery
lasts about a month, so this is infrequent.

---

## Updating the firmware later

After the first USB flash, the device accepts over-the-air updates. Edit
`sourdough.yaml`, then:

```bash
esphome run sourdough.yaml
```

Choose the network/OTA option when prompted.
