"""Real-time status updates from the Elica MQTT broker."""

from __future__ import annotations

from collections.abc import Callable, Iterable
import json
import logging
import ssl
from typing import Any

import paho.mqtt.client as mqtt

_LOGGER = logging.getLogger(__name__)

HOST = "cloudprodmqtt.elica.com"
PORT = 8883
KEEPALIVE_SECONDS = 60
MIN_RECONNECT_SECONDS = 5
MAX_RECONNECT_SECONDS = 300
TOPIC_PREFIX = "v1/device/"
TOPIC_SUFFIX = "/statusjson"


def topic_for(cuid: str) -> str:
    """Return the status topic of a device."""
    return f"{TOPIC_PREFIX}{cuid}{TOPIC_SUFFIX}"


def cuid_from(topic: str) -> str | None:
    """Return the device of a status topic."""
    if topic.startswith(TOPIC_PREFIX) and topic.endswith(TOPIC_SUFFIX):
        return topic[len(TOPIC_PREFIX) : -len(TOPIC_SUFFIX)]
    return None


def parse_status(payload: bytes) -> dict[str, Any] | None:
    """Return the status in a message, which may be wrapped in a list."""
    try:
        data = json.loads(payload)
    except ValueError:
        return None
    if isinstance(data, list) and data:
        data = data[0]
    return data if isinstance(data, dict) else None


class ElicaMqttClient:
    """Listen to device status topics; paho runs its own network thread."""

    def __init__(
        self,
        tls_context: ssl.SSLContext,
        credentials: tuple[str, str],
        cuids: Iterable[str],
        on_status: Callable[[str, dict[str, Any]], None],
        on_connection: Callable[[bool], None],
    ) -> None:
        """Initialize the client; callbacks run in the network thread."""
        self._credentials = credentials
        self._topics = [(topic_for(cuid), 1) for cuid in cuids]
        self._on_status = on_status
        self._on_connection = on_connection
        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=credentials[0],
            protocol=mqtt.MQTTv311,
        )
        self._client.tls_set_context(tls_context)
        self._client.username_pw_set(*credentials)
        self._client.reconnect_delay_set(MIN_RECONNECT_SECONDS, MAX_RECONNECT_SECONDS)
        self._client.on_connect = self._handle_connect
        self._client.on_disconnect = self._handle_disconnect
        self._client.on_message = self._handle_message

    def start(self) -> None:
        """Connect in the background; paho reconnects on its own."""
        self._client.connect_async(HOST, PORT, keepalive=KEEPALIVE_SECONDS)
        self._client.loop_start()

    def stop(self) -> None:
        """Disconnect and stop the network thread."""
        self._client.disconnect()
        self._client.loop_stop()

    def update_credentials(self, credentials: tuple[str, str]) -> None:
        """Use new credentials from the next connection on."""
        if credentials != self._credentials:
            self._credentials = credentials
            self._client.username_pw_set(*credentials)

    def _handle_connect(
        self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any
    ) -> None:
        if reason_code.is_failure:
            _LOGGER.warning("Elica MQTT connection refused: %s", reason_code)
            self._on_connection(False)
            return
        client.subscribe(self._topics)
        self._on_connection(True)

    def _handle_disconnect(
        self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any
    ) -> None:
        _LOGGER.debug("Elica MQTT disconnected: %s", reason_code)
        self._on_connection(False)

    def _handle_message(self, client: Any, userdata: Any, message: Any) -> None:
        cuid = cuid_from(message.topic)
        status = parse_status(message.payload)
        if cuid is not None and status is not None:
            self._on_status(cuid, status)
