"""Data coordinator for the Elica Connect integration."""

from __future__ import annotations

from collections.abc import Coroutine
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ElicaAuthError, ElicaClient, ElicaError
from .const import CONF_REFRESH_TOKEN, DEVICE_TYPE_HOOD, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type ElicaConfigEntry = ConfigEntry[ElicaCoordinator]


class ElicaCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Keep the state of the account's hoods, keyed by device id."""

    config_entry: ElicaConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ElicaConfigEntry, client: ElicaClient
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            devices = await self.client.async_get_devices()
        except ElicaAuthError as err:
            raise ConfigEntryAuthFailed("Elica login expired") from err
        except ElicaError as err:
            raise UpdateFailed(str(err)) from err
        finally:
            self._async_store_refresh_token()

        return {
            device["id"]: device
            for device in devices
            if device.get("type") == DEVICE_TYPE_HOOD
        }

    async def async_send_command(
        self, device_id: str, capabilities: dict[str, int]
    ) -> None:
        """Send a command and show its values until the next poll confirms them."""
        device = self.data[device_id]
        await self._async_run(self.client.async_send_command(device, capabilities))
        updated_device = {
            **device,
            "dataModel": {**device.get("dataModel", {}), **capabilities},
        }
        self.async_set_updated_data({**self.data, device_id: updated_device})

    async def async_reset_filter(self, device_id: str, filter_id: int) -> None:
        """Mark a filter as clean or new, then read its new state."""
        await self._async_run(self.client.async_reset_filter(device_id, filter_id))
        await self.async_request_refresh()

    async def _async_run(self, request: Coroutine[Any, Any, None]) -> None:
        """Run a user action, turning cloud errors into Home Assistant errors."""
        try:
            await request
        except ElicaAuthError as err:
            self.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError("Elica login expired") from err
        except ElicaError as err:
            raise HomeAssistantError(f"Elica request failed: {err}") from err
        finally:
            self._async_store_refresh_token()

    def _async_store_refresh_token(self) -> None:
        token = self.client.refresh_token
        if token != self.config_entry.data.get(CONF_REFRESH_TOKEN):
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, CONF_REFRESH_TOKEN: token},
            )
