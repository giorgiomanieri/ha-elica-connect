"""Read the app's client credential from a copy of the Elica Connect APK."""

from __future__ import annotations

from base64 import b64decode
import binascii
from pathlib import Path
import re
import zipfile

CREDENTIAL_PATTERN = re.compile(rb"Basic ([A-Za-z0-9+/]{16,}={0,2})")
DEX_FILE_PATTERN = re.compile(r"classes\d*\.dex")


class InvalidApk(Exception):
    """The file is not an APK with exactly one client credential."""


def read_client_credential(path: Path) -> str:
    """Return the 'Basic ...' header value found in the APK's code."""
    found: set[bytes] = set()
    try:
        with zipfile.ZipFile(path) as apk:
            for name in apk.namelist():
                if DEX_FILE_PATTERN.fullmatch(name):
                    found.update(CREDENTIAL_PATTERN.findall(apk.read(name)))
    except (OSError, zipfile.BadZipFile) as err:
        raise InvalidApk("Cannot read the file") from err

    credentials = [value for value in found if _is_client_credential(value)]
    if len(credentials) != 1:
        raise InvalidApk(f"Found {len(credentials)} client credentials")
    return f"Basic {credentials[0].decode('ascii')}"


def _is_client_credential(value: bytes) -> bool:
    try:
        return b":" in b64decode(value, validate=True)
    except binascii.Error:
        return False
