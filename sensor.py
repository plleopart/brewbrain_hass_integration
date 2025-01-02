"""Sensor platform for Brew Brain integration."""

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Brew Brain sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for float in coordinator.floats:
        float_id = float['id']
        float_name = float['name']
        entities.append(BrewBrainTemperatureSensor(coordinator, float_id, float_name, entry.entry_id))
        entities.append(BrewBrainSGSensor(coordinator, float_id, float_name, entry.entry_id))
        entities.append(BrewBrainVoltageSensor(coordinator, float_id, float_name, entry.entry_id))

    async_add_entities(entities)


class BrewBrainSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Brew Brain sensor."""

    def __init__(self, coordinator, float_id, float_name, entry_id, sensor_type, unit_of_measurement, icon, device_class=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.float_id = float_id
        self.float_name = float_name
        self.sensor_type = sensor_type
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_name = f"{float_name} {sensor_type}"
        self._attr_unique_id = f"{float_id}_{sensor_type}"
        self._state = None
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_state_class = "measurement"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, float_id)},
            name=float_name,
            manufacturer="Brew Brain",
            model="Float",
            via_device=(DOMAIN, entry_id),
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        data = self.coordinator.data.get(self.float_id)
        _LOGGER.debug("Retrieving state for %s", self.name)
        if data:
            self._state = data.get(self.sensor_type)
            _LOGGER.debug("Retrieved state for %s: %s", self.name, self._state)
        else:
            _LOGGER.warning("No data found for float_id %s and sensor_type %s", self.float_id, self.sensor_type)
        return self._state
    

class BrewBrainTemperatureSensor(BrewBrainSensor):
    """Representation of a Brew Brain Temperature sensor."""

    def __init__(self, coordinator, float_id, float_name, entry_id):
        super().__init__(coordinator, float_id, float_name, entry_id, "Temperature", "°C", "mdi:thermometer", "temperature")


class BrewBrainSGSensor(BrewBrainSensor):
    """Representation of a Brew Brain Specific Gravity sensor."""

    def __init__(self, coordinator, float_id, float_name, entry_id):
        super().__init__(coordinator, float_id, float_name, entry_id, "SG", None, "mdi:scale", None)


class BrewBrainVoltageSensor(BrewBrainSensor):
    """Representation of a Brew Brain Voltage sensor."""

    def __init__(self, coordinator, float_id, float_name, entry_id):
        super().__init__(coordinator, float_id, float_name, entry_id, "Voltage", "V", "mdi:flash", "voltage")
