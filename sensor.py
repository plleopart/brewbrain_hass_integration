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
        entities.append(BrewBrainTemperatureSensor(coordinator, float_id, float_name))
        entities.append(BrewBrainSGSensor(coordinator, float_id, float_name))
        entities.append(BrewBrainBatterySensor(coordinator, float_id, float_name))

    async_add_entities(entities)


class BrewBrainSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Brew Brain sensor."""

    def __init__(self, coordinator, float_id, float_name, sensor_type, unit_of_measurement, icon, device_class=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.float_id = float_id
        self.float_name = float_name
        self.sensor_type = sensor_type
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_name = f"{float_name} {sensor_type}"
        self._attr_unique_id = f"{float_id}_{sensor_type}"
        self._state = 0.0
        self._last_valid_value = 0.0
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_state_class = "measurement"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, float_id)},
            name=float_name,
            manufacturer="Brew Brain",
            model="Float",
        )

    def _parse_numeric_value(self, value):
        """Convert a raw coordinator value to a float or return None if invalid."""
        if value in (None, "", "None"):
            return None

        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None

        if parsed != parsed:
            return None

        return parsed

    @property
    def native_value(self):
        """Return the latest valid numeric reading, falling back to the last cached value."""
        data = self.coordinator.data.get(self.float_id) if self.coordinator.data else None
        raw_value = data.get(self.sensor_type) if data else None
        parsed_value = self._parse_numeric_value(raw_value)

        if parsed_value is not None:
            self._last_valid_value = parsed_value
            self._state = parsed_value
            _LOGGER.debug("Retrieved state for %s: %s", self.name, parsed_value)
            return parsed_value

        if self._last_valid_value is not None:
            self._state = self._last_valid_value
            _LOGGER.debug("Using cached state for %s: %s", self.name, self._last_valid_value)
            return self._last_valid_value

        self._state = 0.0
        _LOGGER.warning("No valid data found for float_id %s and sensor_type %s", self.float_id, self.sensor_type)
        return 0.0

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.native_value
    

class BrewBrainTemperatureSensor(BrewBrainSensor):
    """Representation of a Brew Brain Temperature sensor."""

    def __init__(self, coordinator, float_id, float_name):
        super().__init__(coordinator, float_id, float_name, "Temperature", "ºC", "mdi:thermometer", "temperature")


class BrewBrainSGSensor(BrewBrainSensor):
    """Representation of a Brew Brain Specific Gravity sensor."""

    def __init__(self, coordinator, float_id, float_name):
        super().__init__(coordinator, float_id, float_name, "SG", None, "mdi:scale", None)


class BrewBrainBatterySensor(BrewBrainSensor):
    """Representation of a Brew Brain Battery sensor."""

    def __init__(self, coordinator, float_id, float_name):
        super().__init__(coordinator, float_id, float_name, "Battery", "V", "mdi:battery", "voltage")
