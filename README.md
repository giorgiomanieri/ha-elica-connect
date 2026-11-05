# Elica Connect for Home Assistant

[Italiano](README.it.md)

Custom integration to control Elica Connect hoods from Home Assistant, through the Elica cloud.

> **Unofficial project.** It is not affiliated with, endorsed by or supported by Elica S.p.A. "Elica" is a trademark of its respective owners and is used only to identify compatible products. Use this integration at your own risk: it may stop working if the cloud changes, and using it may not comply with the Elica service terms, which could lead to your account being blocked.

## Active features

Every feature in this table has been tested on a real hood.

| Entity | Function |
|---|---|
| Fan | Off, speeds 1, 2 and 3, boost (25, 50, 75 and 100%) |
| Light | On, off and intensity |
| Grease filter | Efficiency and status, as diagnostic sensors |
| Reset grease filter | Button to mark the filter as clean |

State changes arrive in real time through the Elica MQTT broker, usually within 1-2 seconds, including those made from the hood panel. If MQTT is unavailable, the integration falls back to polling the cloud every 30 seconds.

The interface is available in English, Italian, Spanish, French and German, following the Home Assistant language.

## Compatibility

So far the integration has been tested on a single hood:

| Model | Code | Data model | Installation |
|---|---|---|---|
| Boxin Advance Plus IX/A/60 | `PRF0191539` | `dataModelIdx` 9 | Extractor |

Login, token refresh after a Home Assistant restart and state reading have also been tested.

### Not verified yet

- Charcoal filter and recirculating installation: the code handles them, but they have not been tested.
- Refresh token lifetime.
- Setup by uploading the APK.
- Installation through HACS.
- Other hood models and data models. Entities are created from the attributes reported by the cloud, but behavior may differ. In particular, boost uses the values observed on data model 9.
- Snap air purifiers are not supported.

If you try it on another model, open an [issue](https://github.com/giorgiomanieri/ha-elica-connect/issues) with the model, its `dataModelIdx` and what works. Do not include credentials, serial numbers or device identifiers.

## Requirements

- Home Assistant 2026.3 or later.
- An Elica Connect account with the hood already paired in the app.
- Your own copy of the Elica Connect app as a single APK file, preferably taken from your phone. This repository does not include it.

## Installation

With HACS: add this repository as a custom repository of type **Integration**, install **Elica Connect** and restart Home Assistant.

Manually: copy `custom_components/elica_connect` to `/config/custom_components/` and restart Home Assistant.

## Configuration

1. In Home Assistant open **Settings > Devices & services > Add integration** and search for **Elica Connect**.
2. Upload your copy of the APK. Home Assistant reads the app credential from it and then deletes the upload.
3. Enter your Elica email and password.

The password is used only for the first login and is not stored. Home Assistant keeps the refresh token and the app credential in `.storage`, so treat that folder and your backups as sensitive data. If the token expires, Home Assistant asks for the password again.

## Privacy

The integration and `elica_probe.py` communicate only with the Elica cloud (`cloudprod.elica.com`, and `cloudprodmqtt.elica.com` for real-time updates), as the official app does. Credentials and commands go to Elica, and hood state and filter data come from Elica.

This project includes no telemetry and sends no data to its author or to other services. Elica's handling of your data is governed by its privacy policy.

## Tools

`elica_probe.py` is an optional command line client to read the state and try the light and fan. It is not needed to install the integration and uses only the Python standard library:

```bash
python elica_probe.py --apk PATH_TO_APK --raw
```

## License

[MIT](LICENSE). The license covers only the code in this repository.
