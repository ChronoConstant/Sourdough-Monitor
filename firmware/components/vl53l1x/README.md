# VL53L1X Component for ESPHome

This component provides integration with the VL53L1X/VL53L4CD Time-of-Flight (ToF) distance sensor for ESPHome using I2C. This implementation is an adaptation of existing open-source code that has been modified to enhance functionality and compatibility with ESPHome.

## Features

-   Supports both VL53L1X and VL53L4CD sensors
-   I2C communication
-   Configurable distance mode (short/long)
-   Configurable update interval
-   Range status reporting
-   Automatic sensor initialization and configuration

## Hardware Setup

Connect your VL53L1X/VL53L4CD sensor to your ESP32/ESP8266 using the following pins:

-   VL53L1X VCC → ESP32 3.3V
-   VL53L1X GND → ESP32 GND
-   VL53L1X SDA → ESP32 SDA (GPIO21 in example)
-   VL53L1X SCL → ESP32 SCL (GPIO22 in example)
-   VL53L1X XSHUT → ESP32 GPIO (GPIO23 in example, optional for power control)

## Configuration Variables

-   **distance_mode** (_Optional_, string, default: "long"): The distance mode of the sensor. Options are "short" or "long". Note that VL53L4CD sensors only support "short" mode and will be automatically configured as such.
-   **update_interval** (_Optional_, time, default: 0.5s): How often to update the sensor readings.
-   **i2c_id** (_Optional_, ID): The ID of the I2C bus if you have multiple I2C buses.

## Sensor Outputs

-   **distance**: Distance measurement in millimeters
-   **range_status**: Status of the range measurement (0 = valid, 1-4 = various error states), but I personally haven't gotten these to show up or be helpful

## Basic Configuration

```yaml
i2c:
    sda: GPIO21
    scl: GPIO22
    scan: true

# Optional XSHUT pin control
output:
    - platform: gpio
      pin: GPIO23
      id: xshut_pin

# Power on sequence
esphome:
    on_boot:
        then:
            - output.turn_on: xshut_pin
            - delay: 1s # Allow VL53L1X to boot (min 1.2ms required)
    on_shutdown:
        then:
            - output.turn_off: xshut_pin

vl53l1x:
    distance_mode: long
    update_interval: 0.5s

sensor:
    - platform: vl53l1x
      distance:
          name: "VL53L1X Distance"
          id: tof_distance
      range_status:
          name: "VL53L1X Range Status"
```

## Filtering Example

This example shows how to filter out invalid readings and apply a median filter to stabilize measurements:

```yaml
sensor:
    - platform: vl53l1x
      distance:
          name: "VL53L1X Distance"
          filters:
              - lambda: |-
                    if (x < 45 || x > 4200 || x == 0.0 || std::isnan(x)) {
                      return 0;
                    }
                    return x;
              - median:
                    window_size: 5
                    send_every: 5
                    send_first_at: 1
```

## Installation

There are two ways to install this component:

### Option 1: Direct from GitHub (Recommended)

Add the following to your ESPHome configuration:

```yaml
external_components:
    - source: github://Averyy/esphome-custom-components
      components: [vl53l1x]
```

**Note:** Using the GitHub repository version means you'll automatically get updates, but it could change at any moment. If stability is critical for your project, consider using the local installation method.

### Option 2: Local Installation

If you prefer a more stable setup or need to modify the component:

1. Create a `components` directory in your ESPHome configuration directory
2. Copy the `vl53l1x` directory into the `components` directory
3. Add the `external_components` section to your YAML configuration:

```yaml
external_components:
    - source: components
```

## Notes

-   The VL53L1X component automatically detects and configures the sensor on startup
-   The VL53L4CD sensor is automatically detected and forced to use "short" distance mode
-   The timing budget is set to 500ms for maximum accuracy
-   The sensor has a practical range of approximately 45mm to 4000mm
-   Readings outside this range or with invalid status should be filtered out
-   The sensor updates approximately every 90ms internally, regardless of the configured update interval
