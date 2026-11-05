"""Light platform for the Elica Connect integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ATTR_LIGHT_INTENSITY
from .coordinator import ElicaConfigEntry, ElicaCoordinator
from .entity import ElicaEntity
from .values import MAX_INTENSITY, brightness_to_intensity, intensity_to_brightness


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElicaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a light for every hood that has one."""
    coordinator = entry.runtime_data
    async_add_entities(
        ElicaLight(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if ATTR_LIGHT_INTENSITY in (device.get("dataModel") or {})
    )


class ElicaLight(ElicaEntity, LightEntity):
    """The hood's cooktop light."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_translation_key = "cooktop_light"

    def __init__(self, coordinator: ElicaCoordinator, device_id: str) -> None:
        """Initialize the light."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_cooktop_light"
        self._last_intensity = MAX_INTENSITY

    @property
    def _intensity(self) -> int | None:
        return self.data_model.get(ATTR_LIGHT_INTENSITY)

    @property
    def is_on(self) -> bool | None:
        """Return whether the light is on."""
        return None if self._intensity is None else self._intensity > 0

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        if self._intensity is None:
            return None
        return intensity_to_brightness(self._intensity)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, at its last intensity unless one is given."""
        intensity = self._last_intensity
        if ATTR_BRIGHTNESS in kwargs:
            intensity = brightness_to_intensity(kwargs[ATTR_BRIGHTNESS])
        await self.coordinator.async_send_command(
            self._device_id, {ATTR_LIGHT_INTENSITY: intensity}
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        if self._intensity:
            self._last_intensity = self._intensity
        await self.coordinator.async_send_command(
            self._device_id, {ATTR_LIGHT_INTENSITY: 0}
        )
