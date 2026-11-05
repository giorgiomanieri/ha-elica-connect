"""Conversions between Elica values and Home Assistant values."""

MAX_FAN_SPEED = 3
MAX_INTENSITY = 100
MAX_BRIGHTNESS = 255


def speed_to_percentage(speed: int) -> int:
    """Convert a manual fan speed to a percentage."""
    return round(min(speed, MAX_FAN_SPEED) * 100 / MAX_FAN_SPEED)


def percentage_to_speed(percentage: int) -> int:
    """Convert a percentage to a manual fan speed; only 0 turns the fan off."""
    if percentage <= 0:
        return 0
    return min(MAX_FAN_SPEED, max(1, round(percentage * MAX_FAN_SPEED / 100)))


def intensity_to_brightness(intensity: int) -> int:
    """Convert a light intensity (0-100) to a brightness (0-255)."""
    return round(intensity * MAX_BRIGHTNESS / MAX_INTENSITY)


def brightness_to_intensity(brightness: int) -> int:
    """Convert a brightness to an intensity, keeping any brightness above 0 on."""
    if brightness <= 0:
        return 0
    return min(MAX_INTENSITY, max(1, round(brightness * MAX_INTENSITY / MAX_BRIGHTNESS)))
