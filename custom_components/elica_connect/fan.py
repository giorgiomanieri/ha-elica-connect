"""Fan platform for the Elica Connect integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ATTR_FAN_MODE, ATTR_FAN_SPEED, FAN_MODE_BOOST_BIT, FAN_MODE_MANUAL
from .coordinator import ElicaConfigEntry, ElicaCoordinator
from .entity import ElicaEntity
from .values import MAX_FAN_SPEED, percentage_to_speed, speed_to_percentage


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElicaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a fan for every hood that has one."""
    coordinator = entry.runtime_data
    async_add_entities(
        ElicaFan(coordinator, device_id)
        for device_id, device in coordinator.data.items()
        if ATTR_FAN_SPEED in (device.get("dataModel") or {})
    )


class ElicaFan(ElicaEntity, FanEntity):
    """The hood's fan, driven through its manual speeds."""

    _attr_name = None
    _attr_speed_count = MAX_FAN_SPEED
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: ElicaCoordinator, device_id: str) -> None:
        """Initialize the fan."""
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}_fan"

    @property
    def percentage(self) -> int | None:
        """Return the fan speed as a percentage."""
        if (self.data_model.get(ATTR_FAN_MODE) or 0) & FAN_MODE_BOOST_BIT:
            return 100
        speed = self.data_model.get(ATTR_FAN_SPEED)
        return None if speed is None else speed_to_percentage(speed)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed."""
        await self.coordinator.async_send_command(
            self._device_id,
            {
                ATTR_FAN_MODE: FAN_MODE_MANUAL,
                ATTR_FAN_SPEED: percentage_to_speed(percentage),
            },
        )

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the fan on, at the lowest speed unless one is given."""
        await self.async_set_percentage(
            speed_to_percentage(1) if percentage is None else percentage
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self.async_set_percentage(0)
