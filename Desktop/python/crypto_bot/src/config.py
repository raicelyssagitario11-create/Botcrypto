import os
from binance.client import Client

# === Binance Config ===
# TODO: Load these from environment variables or a secure file in production
API_KEY = "TU_API_KEY"
API_SECRET = "TU_API_SECRET"

# Trading Config
PAIRS = ["BNBUSDT", "BTCUSDT", "ETHUSDT"]
INTERVAL = Client.KLINE_INTERVAL_5MINUTE
LIMIT = 100
ENTRY_SIZE = 5  # USDT

# Bot Internal Config
UPDATE_INTERVAL_SECONDS = 300  # 5 minutes
