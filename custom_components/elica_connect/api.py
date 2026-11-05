"""Client for the Elica Connect cloud API."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import aiohttp

BASE_URL = "https://cloudprod.elica.com/eiot-api/v1/"
COMMAND_TIMEOUT_MS = 30000
REQUEST_TIMEOUT_SECONDS = 30
AUTH_ERROR_STATUSES = (400, 401, 403)


class ElicaError(Exception):
    """The Elica cloud could not complete a request."""


class ElicaAuthError(ElicaError):
    """The Elica cloud rejected the credentials or the refresh token."""


class ElicaClient:
    """Talk to the Elica cloud on behalf of one account."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        client_credential: str,
        app_uuid: str,
        refresh_token: str | None = None,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._client_credential = client_credential
        self._app_uuid = app_uuid
        self._refresh_token = refresh_token
        self._access_token: str | None = None
        self._refresh_lock = asyncio.Lock()

    @property
    def refresh_token(self) -> str | None:
        """Return the current refresh token, which the cloud may rotate."""
        return self._refresh_token

    async def async_login(self, email: str, password: str) -> None:
        """Log in with the account credentials."""
        await self._async_token_request(
            {
                "scope": "default",
                "grant_type": "password",
                "username": email,
                "password": password,
                "app_uuid": self._app_uuid,
            }
        )

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return the devices of the account."""
        devices = await self._async_api_request("GET", "devices")
        if not isinstance(devices, list):
            raise ElicaError("Unexpected devices reply")
        return devices

    async def async_send_command(
        self, device: dict[str, Any], capabilities: dict[str, int]
    ) -> None:
        """Send attribute values to a device."""
        await self._async_api_request(
            "POST",
            f"devices/{device['id']}/commands",
            {
                "async": True,
                "capabilities": capabilities,
                "name": "capabilities",
                "type": device["type"],
                "timeout": COMMAND_TIMEOUT_MS,
            },
        )

    async def async_reset_filter(self, device_id: str, filter_id: int) -> None:
        """Mark a filter as clean or new."""
        await self._async_api_request(
            "POST", f"devices/{device_id}/resetFilter?filterId={filter_id}"
        )

    async def _async_refresh(self, rejected_token: str | None) -> None:
        """Get a new access token, once for all callers that saw it rejected."""
        async with self._refresh_lock:
            if self._access_token != rejected_token:
                return
            if self._refresh_token is None:
                raise ElicaAuthError("No refresh token")
            await self._async_token_request(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                    "app_uuid": self._app_uuid,
                }
            )

    async def _async_token_request(self, form: dict[str, str]) -> None:
        status, reply = await self._async_request(
            "POST",
            "oauth/token",
            {"Authorization": self._client_credential},
            data=form,
        )
        if status in AUTH_ERROR_STATUSES:
            raise ElicaAuthError(f"Token request rejected with status {status}")
        if status >= 300 or not isinstance(reply, dict) or "access_token" not in reply:
            raise ElicaError(f"Token request failed with status {status}")
        self._access_token = reply["access_token"]
        self._refresh_token = reply.get("refresh_token", self._refresh_token)

    async def _async_api_request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> Any:
        if self._access_token is None:
            await self._async_refresh(None)

        for retry_allowed in (True, False):
            token = self._access_token
            headers = {"Authorization": f"Bearer {token}"}
            if method == "POST":
                headers["Content-Type"] = "application/json"
            status, reply = await self._async_request(
                method, path, headers, json_body=body
            )
            if status != 401:
                break
            if not retry_allowed:
                raise ElicaAuthError("Access token rejected")
            await self._async_refresh(token)

        if status >= 300:
            raise ElicaError(f"{method} {path} failed with status {status}")
        return reply

    async def _async_request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        data: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        try:
            async with self._session.request(
                method,
                f"{BASE_URL}{path}",
                headers={"Accept": "application/json", **headers},
                data=data,
                json=json_body,
                timeout=timeout,
            ) as response:
                text = await response.text()
                status = response.status
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ElicaError(f"Cannot reach the Elica cloud: {err}") from err

        if not text.strip():
            return status, None
        try:
            return status, json.loads(text)
        except ValueError:
            # Error pages are not JSON; the status decides what happens next.
            if status >= 300:
                return status, None
            raise ElicaError(f"{path} reply is not JSON") from None
