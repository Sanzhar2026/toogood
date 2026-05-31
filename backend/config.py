# backend/config.py - Add these settings

# WebSocket settings
WEBSOCKET_HEARTBEAT_INTERVAL = 25  # seconds
WEBSOCKET_HEARTBEAT_TIMEOUT = 60   # seconds
WEBSOCKET_MAX_CONNECTIONS = 1000
WEBSOCKET_RECONNECT_DELAY = 5      # seconds

# For production on Render.com
WEBSOCKET_PING_INTERVAL = 20
WEBSOCKET_PING_TIMEOUT = 30