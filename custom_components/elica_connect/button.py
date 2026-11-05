"""Button platform for the Elica Connect integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ElicaConfigEntry, ElicaCoordinator
from .entity import ElicaEntity

FILTER_TYPES = ("grease", "charcoal")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ElicaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a reset button for every filter the cloud allows to reset."""
    coordinator = entry.runtime_data
    async_add_entities(
        ElicaFilterResetButton(coordinator, device_id, item["type"], item["id"])
        for device_id, device in coordinator.data.items()
        for item in device.get("filters") or []
        if item.get("type") in FILTER_TYPES and item.get("isResettable")
    )


class ElicaFilterResetButton(ElicaEntity, ButtonEntity):
    """Mark a filter as clean."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: ElicaCoordinator,
        device_id: str,
        filter_type: str,
        filter_id: int,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, device_id)
        self._filter_id = filter_id
        self._attr_translation_key = f"{filter_type}_filter_reset"
        self._attr_unique_id = f"{device_id}_{filter_type}_filter_reset"

    async def async_press(self) -> None:
        """Reset the filter."""
        await self.coordinator.async_reset_filter(self._device_id, self._filter_id)
