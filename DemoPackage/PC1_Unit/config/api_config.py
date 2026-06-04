"""
API Configuration
Central place for all connection settings.
"""

# ──── DATABASE SETTINGS ────
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'army_logistics',
    'user': 'postgres',
    'password': 'mypass'
}

# ──── API SERVER SETTINGS ────
API_HOST = '0.0.0.0'          # Use 127.0.0 for local only
API_PORT = 5000

# Base URL construction
API_BASE_URL = f"http://{API_HOST}:{API_PORT}/api/v1"

# Timeouts (seconds)
TIMEOUT_CONNECT = 30          # Initial handshake timeout
TIMEOUT_READ = 60               # Query timeout
POLL_INTERVAL_GATE = 3000          # ms (3 sec) - How often GATE checks status
POLL_INTERVAL_WAREHOUSE = 5000     # ms (5 sec) - How often WH checks in

# ──── SECURITY ────
SECRET_KEY = "ARMYLOGISTICS_2025_SECRET_KEY_CHANGE_ME_IN_PRODUCTION"
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24

# Allowed origins for CORS (CORS)
CORS_ORIGINS = [
    "http://localhost:*",
    f"http://{API_HOST}:{API_PORT}",
]

# Simulation settings (for when no real UHF)
SIMULATION_MODE = True
AUTO_GENERATE_UHF_PREFIX = "DEMO-EPC"  # Will generate like "DEMO-EPC-000001"

if SIMULATION_MODE:
    print(" WARNING: Running in DEMO MODE")
    print("   (No real UHF reader connected)")
    print("   Using simulated UHF data...")
else:
    print(" PRODUCTION MODE (Real UHF enabled)")