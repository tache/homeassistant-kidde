# New Lead Fork
The @tache fork will takeover as the lead fork [fork][fork] for this repo.
Thank you to @865charlesw for the awesome start to the effort.

# Kidde HomeSafe Integration
_Integration to integrate with [Kidde HomeSafe][kidde_homesafe]._

## HACS Installation

1. Follow the [HACS instructions][hacs_custom_repo] for a custom repo, using https://github.com/tache/homeassistant-kidde as the URL
1. Restart your HomeAssistant instance
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Kidde"
1. Configuration is done in the UI

You may get a notification from the Kidde app once you complete setup; either ignore or `ALLOW` it. Selecting `DENY`` may prevent this integration from updating.

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[hacs_custom_repo]: https://hacs.xyz/docs/faq/custom_repositories/
[kidde_homesafe]: https://github.com/865charlesw/kidde-homesafe
[fork]: https://github.com/tache/homeassistant-kidde

## Working with the Kidde API

A good thread on the topic is located on the [community.home-assistant.io]( [https://community.home-assistant.io/t/kidde-smart-alarms-smoke-co-detectors/381061/14)

### Step 1: Getting the AUTH Token

Send a POST request to
```
https://api.homesafe.kidde.com/api/v4/auth/login
```
The POST Request Body must have your valid Kidde account information
```
{
    "email": "----",
    "password": "----",
    "timezone": "America/New_York"
}
```

If your request is valid, the JSON response body will have the access token for the next queries
```
{
    ...
    "access_token": "----",
    ...
}
```

### Step 2: Getting the Location ID

Then you can call the API for information. You will need the `Location ID` of your devices. Use the following to get that information.

Send a GET Request to

```
https://api.homesafe.kidde.com/api/v4/location
```

The Requesst Headers are as follows. Note that your `access_token` from the Auth Request replaces `----` for `homeboy-auth`

```
homeboy-app-platform: android
homeboy-app-version: 4.0.12
homeboy-app-platform-version: 12
homeboy-app-id: afc41e9816b1f0d7
homeboy-app-brand: google
homeboy-app-device: sdk_gphone64_x86_64
homeboy-app: com.kidde.android.monitor1
homeboy-auth: ----
user-agent: com.kidde.android.monitor1/4.0.12
content-type: application/json; charset=UTF-8
cache-control: no-cache
```

The GET Request Body is the same as provided in the Auth request.

If your request is valid, the JSON response body will have the `Location ID` used in the device queries
```
{
     "id": ----,
    ...
}
```

### Step 3: Getting the Device Information

To get all the detail on the devices, use the `Location ID` in the `GET Request`, replacing ---- in the URL

```
https://api.homesafe.kidde.com/api/v4/location/----/device
```

The GET headers are the same as the location request.

The GET Request Body is the same as provided in the Auth request.

If your request is valid, the JSON response body will the extensive detail of all the devices at the provided location.

## Other Developer Notes

### Home Assistant Developer Docs
https://developers.home-assistant.io

### HACS Publisher Documentation
https://hacs.xyz/docs/publish/start/

### Building a Home Assistant Custom Component
https://aarongodfrey.dev/home%20automation/building_a_home_assistant_custom_component_part_1/

