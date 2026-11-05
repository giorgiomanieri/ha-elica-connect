#!/usr/bin/env python3
"""Probe for the Elica Connect cloud API.

Logs in, lists your devices and prints their attributes. It sends a command
only with --light (cooktop light) or --fan (manual fan speed).
The password is read from the terminal and is neither stored nor printed.
The app's OAuth client credential is read from your local copy of the APK.

Usage: python elica_probe.py [--apk PATH] [--email EMAIL] [--raw] [--light 0-100] [--fan 0-3]
"""

import argparse
import getpass
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from base64 import b64decode
from pathlib import Path
from urllib.parse import urlparse

BASE_URL = "https://cloudprod.elica.com/"
DEFAULT_APK = Path.home() / "Desktop" / "Elica+Connect_3.2.0_APKPure.apk"
UUID_FILE = Path(__file__).with_name(".elica_app_uuid")
TIMEOUT = 30
COMMAND_TIMEOUT_MS = 30000
LIGHT_ATTRIBUTE = 96
FAN_MODE_ATTRIBUTE = 64
FAN_SPEED_ATTRIBUTE = 110
FAN_MODE_MANUAL = 1
STATE_REFRESH_SECONDS = 4

ATTRIBUTES = {
    5: "fault_warnings_main",
    6: "fault_warnings_UI",
    11: "cooktop_type",
    45: "sensor_calibration",
    48: "motor_profile_level",
    53: "actuator_command_status",
    64: "fan_mode1",
    68: "fan_timeout1",
    69: "fan_timeout2",
    70: "light_mode",
    71: "remote_cmd",
    72: "remote_enabled",
    80: "ui_customization",
    96: "cooktop_light_intensity",
    97: "cooktop_light_color_temp",
    100: "ambient_light_intensity",
    110: "fan_speed",
    112: "virtual_airquality_index",
    128: "grease_filter_lev",
    129: "charcoal_filter_lev",
    131: "filter_enabler",
}
FAN_MODE_BITS = {
    0: "manual",
    2: "boost1",
    3: "boost2",
    4: "auto",
    5: "airmatic",
    6: "cleaning",
    7: "delay_off",
}
SENSITIVE_KEYS = {
    "cuid",
    "serialnumber",
    "id",
    "owner",
    "shares",
    "mac",
    "macaddress",
    "fullname",
    "email",
}


class ProbeError(Exception):
    """An error with a message that is safe to show."""


def read_client_credential(apk_path):
    """Return the app's 'Basic ...' header value found in the APK's DEX files."""
    pattern = re.compile(rb"Basic ([A-Za-z0-9+/]{16,}={0,2})")
    found = set()
    try:
        with zipfile.ZipFile(apk_path) as apk:
            for name in apk.namelist():
                if re.fullmatch(r"classes\d*\.dex", name):
                    found.update(pattern.findall(apk.read(name)))
    except (OSError, zipfile.BadZipFile) as err:
        raise ProbeError(f"Cannot read the APK at {apk_path}: {err}") from err

    valid = []
    for value in found:
        try:
            if b":" in b64decode(value, validate=True):
                valid.append(value.decode("ascii"))
        except ValueError:
            continue
    if len(valid) != 1:
        raise ProbeError(f"Expected one client credential in the APK, found {len(valid)}.")
    return f"Basic {valid[0]}"


def app_uuid():
    """Return a stable installation id, so repeat runs look like one client."""
    if UUID_FILE.exists():
        return UUID_FILE.read_text(encoding="ascii").strip()
    value = str(uuid.uuid4())
    UUID_FILE.write_text(value, encoding="ascii")
    return value


def request_json(url, headers, data=None):
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as err:
        # The body is not shown: an error reply could echo request details.
        raise ProbeError(f"HTTP {err.code} from {urlparse(url).path}") from None
    except urllib.error.URLError as err:
        raise ProbeError(f"Cannot reach {urlparse(url).netloc}: {err.reason}") from None
    except json.JSONDecodeError:
        raise ProbeError(f"Reply from {urlparse(url).path} is not JSON.") from None


def login(base_url, client_credential, email, password):
    body = urllib.parse.urlencode(
        {
            "scope": "default",
            "grant_type": "password",
            "username": email,
            "password": password,
            "app_uuid": app_uuid(),
        }
    ).encode("utf-8")
    headers = {
        "Authorization": client_credential,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    reply = request_json(f"{base_url}eiot-api/v1/oauth/token", headers, body)
    if "access_token" not in reply:
        raise ProbeError("The login reply has no access token.")
    return reply


def auth_headers(session):
    token_type = session.get("token_type") or "Bearer"
    return {
        "Authorization": f"{token_type.capitalize()} {session['access_token']}",
        "Accept": "application/json",
    }


def get_devices(base_url, session):
    devices = request_json(f"{base_url}eiot-api/v1/devices", auth_headers(session))
    if not isinstance(devices, list):
        raise ProbeError("The devices reply is not a list.")
    return devices


def send_command(base_url, session, device, capabilities):
    body = {
        "async": True,
        "capabilities": {str(code): value for code, value in capabilities.items()},
        "name": "capabilities",
        "type": device["type"],
        "timeout": COMMAND_TIMEOUT_MS,
    }
    headers = {**auth_headers(session), "Content-Type": "application/json"}
    url = f"{base_url}eiot-api/v1/devices/{device['id']}/commands"
    return request_json(url, headers, json.dumps(body).encode("utf-8"))


def set_light(base_url, session, device, intensity):
    """Set the cooktop light; 0 turns it off."""
    return send_command(base_url, session, device, {LIGHT_ATTRIBUTE: intensity})


def set_fan(base_url, session, device, speed):
    """Set a manual fan speed; 0 turns the fan off."""
    capabilities = {FAN_MODE_ATTRIBUTE: FAN_MODE_MANUAL, FAN_SPEED_ATTRIBUTE: speed}
    return send_command(base_url, session, device, capabilities)


def select_hood(devices):
    hoods = [device for device in devices if device.get("type") == "Hood"]
    if len(hoods) != 1:
        raise ProbeError(f"Expected one hood, found {len(hoods)}.")
    if not hoods[0].get("connected"):
        raise ProbeError("The hood is offline.")
    return hoods[0]


def light_intensity(text):
    value = int(text)
    if not 0 <= value <= 100:
        raise argparse.ArgumentTypeError("must be between 0 and 100")
    return value


def fan_speed(text):
    value = int(text)
    if not 0 <= value <= 3:
        raise argparse.ArgumentTypeError("must be between 0 and 3")
    return value


def describe_fan_mode(value):
    active = [name for bit, name in FAN_MODE_BITS.items() if value >> bit & 1]
    return "+".join(active) or "none"


def redact(value):
    """Mask personal identifiers, so the output can be shared safely."""
    if isinstance(value, dict):
        return {
            key: "<masked>" if key.lower() in SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def print_device(device):
    print(f"\n{device.get('name')} ({device.get('type')})")
    for key in ("prf", "code12nc", "dataModelIdx", "connected", "isLegacy", "installationType"):
        print(f"  {key}: {device.get(key)}")

    data_model = device.get("dataModel") or {}
    if not data_model:
        print("  dataModel: empty")
    else:
        print("  dataModel:")
    for code, value in sorted(data_model.items(), key=lambda item: int(item[0])):
        name = ATTRIBUTES.get(int(code), "unknown")
        suffix = f" ({describe_fan_mode(value)})" if int(code) == 64 else ""
        print(f"    {int(code):>3} {name}: {value}{suffix}")

    for item in device.get("filters") or []:
        print(f"  filter {item.get('type')}: efficiency {item.get('efficiency')}, {item.get('status')}")


def copy_to_clipboard(text):
    """Copy text with the Windows clipboard tool, so it is never displayed."""
    try:
        subprocess.run(["clip"], input=text.encode("utf-16-le"), check=True)
    except (OSError, subprocess.CalledProcessError) as err:
        raise ProbeError(f"Cannot use the clipboard: {err}") from err


def run(args):
    client_credential = read_client_credential(args.apk)
    if args.copy_client_credential:
        copy_to_clipboard(client_credential)
        print("Client credential copied to the clipboard.")
        return

    email = args.email or input("Elica email: ").strip()
    password = getpass.getpass("Elica password: ")

    session = login(BASE_URL, client_credential, email, password)
    print("Login OK.")
    print(f"MQTT credentials in the reply: {bool(session.get('mqtt_usr') and session.get('mqtt_psw'))}")

    devices = get_devices(BASE_URL, session)
    print(f"Devices found: {len(devices)}")
    for device in devices:
        print_device(device)
    if args.raw:
        print("\nRaw reply, with identifiers masked:")
        print(json.dumps(redact(devices), indent=2, ensure_ascii=False))

    if args.light is None and args.fan is None:
        return
    hood = select_hood(devices)
    if args.light is not None:
        reply = set_light(BASE_URL, session, hood, args.light)
        print(f"Light command: {reply.get('status')}")
    if args.fan is not None:
        reply = set_fan(BASE_URL, session, hood, args.fan)
        print(f"Fan command: {reply.get('status')}")

    time.sleep(STATE_REFRESH_SECONDS)
    state = select_hood(get_devices(BASE_URL, session))["dataModel"]
    print("State reported by the cloud:")
    print(f"  light: {state.get(str(LIGHT_ATTRIBUTE))}")
    print(f"  fan speed: {state.get(str(FAN_SPEED_ATTRIBUTE))}")
    print(f"  fan mode: {describe_fan_mode(state.get(str(FAN_MODE_ATTRIBUTE)) or 0)}")


def main():
    parser = argparse.ArgumentParser(description="Elica Connect probe.")
    parser.add_argument("--apk", type=Path, default=DEFAULT_APK, help="path to the Elica Connect APK")
    parser.add_argument("--email", help="Elica account email")
    parser.add_argument("--raw", action="store_true", help="also print the masked raw reply")
    parser.add_argument("--light", type=light_intensity, help="set the cooktop light, 0-100")
    parser.add_argument("--fan", type=fan_speed, help="set the manual fan speed, 0-3")
    parser.add_argument(
        "--copy-client-credential",
        action="store_true",
        help="copy the app's client credential to the clipboard and exit",
    )
    try:
        run(parser.parse_args())
    except ProbeError as err:
        sys.exit(f"Error: {err}")
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
