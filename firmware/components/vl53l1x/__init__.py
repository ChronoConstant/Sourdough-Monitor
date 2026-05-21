import esphome.codegen as cg # type: ignore 
import esphome.config_validation as cv # type: ignore 
from esphome.components import i2c # type: ignore 
from esphome.const import CONF_ID # type: ignore 

CODEOWNERS = ["@mrtoy-me"]

CONF_VL53L1X_ID = "vl53l1x_id"
CONF_DISTANCE_MODE = "distance_mode"

vl53l1x_ns = cg.esphome_ns.namespace("vl53l1x")
DistanceMode = vl53l1x_ns.enum("DistanceMode")

DISTANCE_MODES = {
    "short": DistanceMode.SHORT,
    "long": DistanceMode.LONG, 
}

VL53L1XComponent = vl53l1x_ns.class_(
    "VL53L1XComponent", cg.PollingComponent, i2c.I2CDevice
)

CONFIG_SCHEMA = cv.All(
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(VL53L1XComponent),
            cv.Optional(CONF_DISTANCE_MODE, default="long"): cv.enum(
                DISTANCE_MODES, upper=False
            ),
        }
    ).extend(cv.polling_component_schema("60s"))
)

async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    cg.add(var.config_distance_mode(config[CONF_DISTANCE_MODE]))