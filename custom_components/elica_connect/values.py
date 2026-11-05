"""Conversions between Elica values and Home Assistant values."""

from .const import (
    ATTR_FAN_MODE,
    ATTR_FAN_SPEED,
    FAN_MODE_BOOST_BIT,
    FAN_MODE_MANUAL,
)

BOOST_SPEED = 4
BOOST_FAN_SPEED = 3
MAX_INTENSITY = 100
MAX_BRIGHTNESS = 255
BOOST_MODE = 4
BOOST_MODE_WITH_MANUAL = 5
DATA_MODELS_WITH_MANUAL_BOOST = (9, 10)


def boost_mode(data_model_index: int | None) -> int:
    """Return the fan mode that starts the boost on a data model."""
    if data_model_index in DATA_MODELS_WITH_MANUAL_BOOST:
        return BOOST_MODE_WITH_MANUAL
    return BOOST_MODE


def fan_capabilities(speed: int, data_model_index: int | None) -> dict[str, int]:
    """Return the attribute values for a fan speed, where the top one is the boost."""
    if speed == BOOST_SPEED:
        return {
            ATTR_FAN_MODE: boost_mode(data_model_index),
            ATTR_FAN_SPEED: BOOST_FAN_SPEED,
        }
    return {ATTR_FAN_MODE: FAN_MODE_MANUAL, ATTR_FAN_SPEED: speed}


def current_speed(data_model: dict[str, int | None]) -> int | None:
    """Return the fan speed, where the top one is the boost."""
    if (data_model.get(ATTR_FAN_MODE) or 0) & FAN_MODE_BOOST_BIT:
        return BOOST_SPEED
    speed = data_model.get(ATTR_FAN_SPEED)
    return None if speed is None else min(speed, BOOST_SPEED)


def speed_to_percentage(speed: int) -> int:
    """Convert a fan speed to a percentage."""
    return round(min(speed, BOOST_SPEED) * 100 / BOOST_SPEED)


def percentage_to_speed(percentage: int) -> int:
    """Convert a percentage to a fan speed; only 0 turns the fan off."""
    if percentage <= 0:
        return 0
    return min(BOOST_SPEED, max(1, round(percentage * BOOST_SPEED / 100)))


def intensity_to_brightness(intensity: int) -> int:
    """Convert a light intensity (0-100) to a brightness (0-255)."""
    return round(intensity * MAX_BRIGHTNESS / MAX_INTENSITY)


def brightness_to_intensity(brightness: int) -> int:
    """Convert a brightness to an intensity, keeping any brightness above 0 on."""
    if brightness <= 0:
        return 0
    return min(MAX_INTENSITY, max(1, round(brightness * MAX_INTENSITY / MAX_BRIGHTNESS)))
