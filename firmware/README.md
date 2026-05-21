# firmware/

ESPHome firmware for the Sourdough Monitor.

| File | Purpose |
|------|---------|
| `sourdough.yaml` | The main firmware — sensors, just-fed logic, deep sleep, MQTT. |
| `sourdough-scan.yaml` | Minimal I²C scanner. Flash first to verify sensor wiring. |
| `secrets.yaml.example` | Config template. Copy to `secrets.yaml` and fill in your values. |
| `components/vl53l1x/` | Bundled third-party ToF driver — see `components/vl53l1x/NOTICE`. |

**Full setup instructions — wiring, flashing, calibration, Home Assistant — are
in [`../BUILD.md`](../BUILD.md).**

Quick reference:

```bash
cp secrets.yaml.example secrets.yaml   # then edit secrets.yaml
esphome run sourdough-scan.yaml        # verify sensors respond on I²C
esphome run sourdough.yaml             # flash the real firmware
```

The first flash must be over USB; after that, `esphome run` updates over the
air. If the USB upload won't connect, put the XIAO in download mode: hold **B**,
tap **R**, release **B**, retry. More in
[`../docs/troubleshooting.md`](../docs/troubleshooting.md).
