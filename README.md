# Nitrado – Home Assistant Integration (foundation)

Custom integration with UI setup (config flow) instead of YAML. Currently
shows one status sensor per selected Nitrado service (`online`/`offline`,
or the raw Nitrado status such as `started`).

## Installation (manual, without HACS)

1. Copy the `custom_components/nitrado/` folder into your HA config
   directory, so it ends up at `<config>/custom_components/nitrado/`.
2. Restart Home Assistant.
3. Settings → Devices & services → Add integration → "Nitrado".
4. Enter your API token (Nitrado account → Settings → API token).
5. Select the servers that should appear in HA.

## Installation via HACS

1. Push this repository to GitHub (root must contain `hacs.json`,
   `README.md`, and `custom_components/nitrado/`).
2. In HA: HACS → three-dot menu → Custom repositories → paste the repo
   URL → category "Integration" → Add.
3. Find "Nitrado" in the HACS integration list → Download.
4. Restart Home Assistant, then add the integration as above.

Before pushing, replace the `YOUR-USERNAME` placeholders in
`manifest.json` (`documentation`, `issue_tracker`) with your actual
repository URL.

## Changing visibility later

On the integration card → "Configure" opens the options flow, where the
server selection can be adjusted at any time. Saving triggers an
automatic reload.

## Architecture

- `api.py` – thin async client, one method pair per endpoint
- `coordinator.py` – one `DataUpdateCoordinator` per account, polls all
  selected services in one go (respects Nitrado's rate limit)
- `config_flow.py` – two-step setup flow (token → server selection),
  plus an options flow for changing the selection later
- `sensor.py` – one `NitradoStatusSensor` per service, each its own HA
  device (keeps the device overview clean with multiple servers)

## Next steps (proposed, not yet implemented)

- Contract sensors (status, expiry date) via `async_get_service()` in
  `api.py` – the method already exists, only the coordinator and a
  second sensor are missing
- Player count/list as a further sensor or attribute
- `switch`/`button` entities for start/stop/restart (check token scope)
- Diagnostics support (`diagnostics.py`) with a redacted token
- Check whether the `websocket_token` included in the API responses
  enables a live feed instead of polling
- A separate `translations/xx.json` file if the integration should
  support multiple languages later (English currently lives directly
  in `strings.json`)
