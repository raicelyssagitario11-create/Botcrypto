import os
from binance.client import Client

# === Binance Config ===
# Load keys from environment variables (recommended)
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# Trading mode: "SIM" (no real orders) or "REAL" (requires API trading perms)
TRADING_MODE = os.getenv("TRADING_MODE", "SIM").upper()

# Trading Config
PAIRS = ["BNBUSDT", "BTCUSDT", "ETHUSDT"]
INTERVAL = Client.KLINE_INTERVAL_5MINUTE
LIMIT = 100
ENTRY_SIZE = 5  # USDT

# Bot Internal Config
UPDATE_INTERVAL_SECONDS = 300  # 5 minutes
