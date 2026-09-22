# Nitrado – Home Assistant Integration

Custom integration with UI setup (config flow) instead of YAML. Adds one
"Nitrado Account" device plus one device per selected game server, each
polled by its own `DataUpdateCoordinator` so entities never poll
individually.

## Entities

**Nitrado Account** (one per configured account)

- **Credit** – account balance, converted from cents to the account
  currency (e.g. `19.55 EUR`)
- **User ID**, **Username** – diagnostic sensors
- **Avatar** – account profile picture

Email address and postal address from the API are intentionally never
turned into entities.

**Per game server** (one per selected service)

- **Status** – the game process itself (`started`/`stopped`/...)
- **Must be started** – the admin-configured target state; compare against
  Status to spot a server that should be running but isn't
- **Contract status** – the subscription (`active`/`suspended`/...),
  distinct from the process status above, with `slots`, `address`,
  `comment`, and `delete_date` as attributes
- **Expiry date** – when the service will be suspended unless renewed
- **Auto extension** – whether the subscription renews itself
- **Player count** – current/max players, with a `players` name list
  attribute
- **Map**, **Version**, **Connect address** – from the game's query
  response
- **Memory** – allocated RAM in MB, only added for Minecraft/Hytale where
  that figure is meaningful
- **Start**, **Stop**, **Restart** buttons – Start and Restart both call
  Nitrado's restart endpoint (there is no separate start endpoint; restart
  also brings up a stopped server). Requires the API token to have server
  control permission, otherwise a press surfaces the resulting error in HA
  instead of failing silently.

Not every game answers the query protocol. Player count, map, version, and
connect address simply stay `unknown` for those instead of erroring.

Device credentials (FTP/MySQL passwords) and access tokens
(`websocket_token`) returned by the API are never turned into entities. The
`websocket_token` was investigated as a possible live-update feed instead of
polling: it appears to be scoped to a per-container console/log stream
(gated by the game's `has_container_websocket` capability flag), not a
general live status feed, and its connection protocol isn't publicly
documented — polling remains the integration's update mechanism.

## Installation (manual, without HACS)

1. Copy the `custom_components/nitrado/` folder into your HA config
   directory, so it ends up at `<config>/custom_components/nitrado/`.
2. Restart Home Assistant.
3. Settings → Devices & services → Add integration → "Nitrado".
4. Enter your API token (Nitrado account → Settings → API token).
5. Select the servers that should appear in HA.

## Installation via HACS

1. In HA: HACS → three-dot menu → Custom repositories → paste
   `https://github.com/niKaphalor/ha-nitrado` → category "Integration" →
   Add.
2. Find "Nitrado" in the HACS integration list → Download.
3. Restart Home Assistant, then add the integration as above.

## Changing visibility later

On the integration card → "Configure" opens the options flow, where the
server selection can be adjusted at any time. Saving triggers an
automatic reload.

## Architecture

- `api.py` – thin async client, one method pair per endpoint
- `coordinator.py` – `NitradoCoordinator` (one per account, polls all
  selected services plus the bulk `/services` contract list in one update)
  and `NitradoAccountCoordinator` (account-level `/user` data)
- `config_flow.py` – two-step setup flow (token → server selection), plus
  an options flow for changing the selection later
- `entity.py` – shared `DeviceInfo` builders for the account and per-server
  devices
- `sensor.py` / `binary_sensor.py` / `image.py` / `button.py` – the
  entities described above
- `diagnostics.py` – config entry diagnostics dump (Settings → Devices &
  services → Nitrado → Download diagnostics), with the API token,
  `websocket_token`, FTP/MySQL credentials, email, and postal address all
  redacted
- `translations/en.json` – entity names; `strings.json` alone is not read
  for entity `translation_key` resolution at runtime, only for config/
  options flow text
- `brand/` – local brand icon (HA 2026.3.0+ local-brands mechanism, no
  `home-assistant/brands` submission needed)
