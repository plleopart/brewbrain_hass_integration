"""Data update coordinator for BrewBrain."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    BrewBrainAuthenticationError,
    BrewBrainClient,
    BrewBrainError,
    BrewBrainFloatData,
)
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BrewBrainDataUpdateCoordinator(
    DataUpdateCoordinator[dict[str, BrewBrainFloatData]]
):
    """Coordinate BrewBrain account updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BrewBrainClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self._client = client

    async def _async_update_data(self) -> dict[str, BrewBrainFloatData]:
        """Fetch the latest data from BrewBrain."""
        try:
            return await self._client.async_get_all_data()
        except BrewBrainAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except BrewBrainError as err:
            raise UpdateFailed(str(err)) from err
