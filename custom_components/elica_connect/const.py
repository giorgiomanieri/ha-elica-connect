"""Constants for the Elica Connect integration."""

from datetime import timedelta

DOMAIN = "elica_connect"
UPDATE_INTERVAL = timedelta(seconds=30)

CONF_APP_UUID = "app_uuid"
CONF_CLIENT_CREDENTIAL = "client_credential"
CONF_REFRESH_TOKEN = "refresh_token"

DEVICE_TYPE_HOOD = "Hood"

ATTR_FAN_MODE = "64"
ATTR_LIGHT_INTENSITY = "96"
ATTR_FAN_SPEED = "110"

FAN_MODE_MANUAL = 1
FAN_MODE_BOOST_BIT = 4
