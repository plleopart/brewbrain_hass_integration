"""Sensors for BrewBrain Float devices."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricPotential, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import BrewBrainFloatData
from .const import (
    DOMAIN,
    MEASUREMENT_SPECIFIC_GRAVITY,
    MEASUREMENT_TEMPERATURE,
    MEASUREMENT_VOLTAGE,
)
from .coordinator import BrewBrainDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class BrewBrainSensorEntityDescription(SensorEntityDescription):
    """Describe a BrewBrain measurement sensor."""

    measurement_key: str


SENSORS: tuple[BrewBrainSensorEntityDescription, ...] = (
    BrewBrainSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        measurement_key=MEASUREMENT_TEMPERATURE,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrewBrainSensorEntityDescription(
        key="specific_gravity",
        translation_key="specific_gravity",
        measurement_key=MEASUREMENT_SPECIFIC_GRAVITY,
        icon="mdi:scale",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    BrewBrainSensorEntityDescription(
        key="voltage",
        translation_key="voltage",
        measurement_key=MEASUREMENT_VOLTAGE,
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BrewBrain sensors."""
    coordinator: BrewBrainDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BrewBrainSensor(coordinator, float_identifier, description)
        for float_identifier in coordinator.data
        for description in SENSORS
    )


class BrewBrainSensor(CoordinatorEntity[BrewBrainDataUpdateCoordinator], SensorEntity):
    """A measurement from a BrewBrain Float."""

    entity_description: BrewBrainSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BrewBrainDataUpdateCoordinator,
        float_identifier: str,
        description: BrewBrainSensorEntityDescription,
    ) -> None:
        """Initialize a BrewBrain sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._float_identifier = float_identifier
        data = coordinator.data[float_identifier]
        self._attr_unique_id = f"{float_identifier}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, float_identifier)},
            name=data.device.name,
            manufacturer="BrewBrain",
            model="Float",
            configuration_url="https://my.brewbrain.nl/float",
        )

    @property
    def native_value(self) -> float | None:
        """Return the latest measurement."""
        data = self._float_data
        if data is None:
            return None
        return data.measurements.get(self.entity_description.measurement_key)

    @property
    def available(self) -> bool:
        """Return whether this measurement is available."""
        return super().available and self.native_value is not None

    @property
    def _float_data(self) -> BrewBrainFloatData | None:
        data = self.coordinator.data or {}
        return data.get(self._float_identifier)
