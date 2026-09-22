"""Constants for the Nitrado integration."""

DOMAIN = "nitrado"

CONF_API_TOKEN = "api_token"
CONF_SERVICES = "services"

API_BASE_URL = "https://api.nitrado.net"

DEFAULT_SCAN_INTERVAL = 300  # seconds

# Games where the allocated RAM (memory_mb) is meaningful enough to surface
# as its own sensor. Matched case-insensitively against `game_human`.
MEMORY_SENSOR_GAMES = ("minecraft", "hytale")
