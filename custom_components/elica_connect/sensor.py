"""Sensor platform for the Elica Connect integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE, EntityCategory
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
    """Add sensors for every known filter of every hood."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for device_id, device in coordinator.data.items():
        for item in device.get("filters") or []:
            filter_type = item.get("type")
            if filter_type in FILTER_TYPES:
                entities.append(ElicaFilterEfficiency(coordinator, device_id, filter_type))
                entities.append(ElicaFilterStatus(coordinator, device_id, filter_type))
    async_add_entities(entities)


class ElicaFilterSensor(ElicaEntity, SensorEntity):
    """A sensor that reads one filter of the hood."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _key_suffix: str

    def __init__(
        self, coordinator: ElicaCoordinator, device_id: str, filter_type: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device_id)
        self._filter_type = filter_type
        self._attr_translation_key = f"{filter_type}_filter_{self._key_suffix}"
        self._attr_unique_id = f"{device_id}_{filter_type}_filter_{self._key_suffix}"

    @property
    def filter_data(self) -> dict[str, Any]:
        """Return the latest data of the filter."""
        for item in self.device.get("filters") or []:
            if item.get("type") == self._filter_type:
                return item
        return {}


class ElicaFilterEfficiency(ElicaFilterSensor):
    """The remaining efficiency of a filter."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _key_suffix = "efficiency"

    @property
    def native_value(self) -> int | None:
        """Return the efficiency."""
        return self.filter_data.get("efficiency")


class ElicaFilterStatus(ElicaFilterSensor):
    """The status reported by the cloud for a filter."""

    _key_suffix = "status"

    @property
    def native_value(self) -> str | None:
        """Return the status."""
        return self.filter_data.get("status")
