import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor, i2c
from esphome.const import (
    CONF_DISTANCE,
    UNIT_EMPTY,
    DEVICE_CLASS_DISTANCE,
    DEVICE_CLASS_EMPTY,
    STATE_CLASS_MEASUREMENT,
)

from . import VL53L1XComponent, CONF_VL53L1X_ID 

DEPENDENCIES = ["vl53l1x"]

CONF_RANGE_STATUS = "range_status"
UNIT_MILLIMETER ="mm"

CONFIG_SCHEMA = cv.All(
    cv.Schema (  
        {
            cv.GenerateID(CONF_VL53L1X_ID): cv.use_id(VL53L1XComponent),
            cv.Required(CONF_DISTANCE): sensor.sensor_schema(
                unit_of_measurement=UNIT_MILLIMETER,
                accuracy_decimals=0,
                device_class=DEVICE_CLASS_DISTANCE,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
            cv.Optional(CONF_RANGE_STATUS): sensor.sensor_schema(
                unit_of_measurement=UNIT_EMPTY,
                accuracy_decimals=0,
                device_class=DEVICE_CLASS_EMPTY,
                state_class=STATE_CLASS_MEASUREMENT,
            ),
        }
    ).extend(i2c.i2c_device_schema(0x29))
)

async def to_code(config):
    hub = await cg.get_variable(config[CONF_VL53L1X_ID])
    await i2c.register_i2c_device(hub, config)

    sens = await sensor.new_sensor(config[CONF_DISTANCE])    
    cg.add(hub.set_distance_sensor(sens))

    if range_config := config.get(CONF_RANGE_STATUS):
        sens = await sensor.new_sensor(range_config)    
        cg.add(hub.set_range_status_sensor(sens))

    
                

    