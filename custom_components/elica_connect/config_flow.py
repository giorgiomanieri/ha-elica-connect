"""Config flow for the Elica Connect integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    FileSelector,
    FileSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import ElicaAuthError, ElicaClient, ElicaError
from .apk import InvalidApk, read_client_credential
from .const import (
    CONF_APP_UUID,
    CONF_CLIENT_CREDENTIAL,
    CONF_REFRESH_TOKEN,
    DEVICE_TYPE_HOOD,
    DOMAIN,
)

CONF_APK = "apk"

PASSWORD_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
APK_SCHEMA = vol.Schema(
    {vol.Required(CONF_APK): FileSelector(FileSelectorConfig(accept=".apk"))}
)
CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.EMAIL)
        ),
        vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR,
    }
)
REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD_SELECTOR})


def _read_uploaded_apk(hass: HomeAssistant, file_id: str) -> str:
    """Read the credential; Home Assistant deletes the upload afterwards."""
    with process_uploaded_file(hass, file_id) as path:
        return read_client_credential(path)


class ElicaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the setup of an Elica account."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._credential: str | None = None

    async def _async_try_login(
        self, email: str, password: str, credential: str, app_uuid: str
    ) -> tuple[str | None, str | None]:
        """Return the refresh token and the error key, one of them being None."""
        client = ElicaClient(async_get_clientsession(self.hass), credential, app_uuid)
        try:
            await client.async_login(email, password)
            devices = await client.async_get_devices()
        except ElicaAuthError:
            return None, "invalid_auth"
        except ElicaError:
            return None, "cannot_connect"
        if not any(device.get("type") == DEVICE_TYPE_HOOD for device in devices):
            return None, "no_hoods"
        return client.refresh_token, None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the APK, which provides the app's client credential."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                self._credential = await self.hass.async_add_executor_job(
                    _read_uploaded_apk, self.hass, user_input[CONF_APK]
                )
            except (InvalidApk, ValueError):
                errors["base"] = "invalid_apk"
            else:
                return await self.async_step_credentials()

        return self.async_show_form(
            step_id="user", data_schema=APK_SCHEMA, errors=errors
        )

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the account credentials."""
        errors: dict[str, str] = {}
        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            app_uuid = str(uuid4())
            token, error = await self._async_try_login(
                email, user_input[CONF_PASSWORD], self._credential, app_uuid
            )
            if error is None:
                return self.async_create_entry(
                    title=email,
                    data={
                        CONF_EMAIL: email,
                        CONF_CLIENT_CREDENTIAL: self._credential,
                        CONF_APP_UUID: app_uuid,
                        CONF_REFRESH_TOKEN: token,
                    },
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="credentials", data_schema=CREDENTIALS_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start a new login after the refresh token stopped working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the password again."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            token, error = await self._async_try_login(
                entry.data[CONF_EMAIL],
                user_input[CONF_PASSWORD],
                entry.data[CONF_CLIENT_CREDENTIAL],
                entry.data[CONF_APP_UUID],
            )
            if error is None:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_REFRESH_TOKEN: token}
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            description_placeholders={"email": entry.data[CONF_EMAIL]},
            errors=errors,
        )
