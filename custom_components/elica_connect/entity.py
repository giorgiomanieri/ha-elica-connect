"""Base entity for the Elica Connect integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ElicaCoordinator


class ElicaEntity(CoordinatorEntity[ElicaCoordinator]):
    """An entity that belongs to one hood."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ElicaCoordinator, device_id: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        device = coordinator.data[device_id]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Elica",
            model=device.get("prf"),
            name=device.get("name"),
        )

    @property
    def device(self) -> dict[str, Any]:
        """Return the latest data of the hood."""
        return self.coordinator.data[self._device_id]

    @property
    def data_model(self) -> dict[str, Any]:
        """Return the latest attribute values of the hood."""
        return self.device.get("dataModel") or {}

    @property
    def available(self) -> bool:
        """Return whether the hood is online."""
        return (
            super().available
            and self._device_id in self.coordinator.data
            and bool(self.device.get("connected"))
        )
