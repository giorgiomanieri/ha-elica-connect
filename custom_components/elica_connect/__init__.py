"""The Elica Connect integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ElicaClient
from .const import CONF_APP_UUID, CONF_CLIENT_CREDENTIAL, CONF_REFRESH_TOKEN
from .coordinator import ElicaConfigEntry, ElicaCoordinator

PLATFORMS = [Platform.BUTTON, Platform.FAN, Platform.LIGHT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ElicaConfigEntry) -> bool:
    """Set up Elica Connect from a config entry."""
    client = ElicaClient(
        async_get_clientsession(hass),
        entry.data[CONF_CLIENT_CREDENTIAL],
        entry.data[CONF_APP_UUID],
        entry.data[CONF_REFRESH_TOKEN],
    )
    coordinator = ElicaCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ElicaConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
