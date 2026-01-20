import os
from binance.client import Client

# === Binance Config ===
# Cargar claves desde variables de entorno (recomendado)
API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# Modo de trading: "SIM" (sin órdenes reales) o "REAL" (requiere permisos)
TRADING_MODE = os.getenv("TRADING_MODE", "SIM").upper()

# Trading Config (pares e intervalo de velas)
PAIRS = ["BNBUSDT", "BTCUSDT", "ETHUSDT"]
INTERVAL = Client.KLINE_INTERVAL_5MINUTE
LIMIT = 100
ENTRY_SIZE = 5  # USDT

# Bot Internal Config
UPDATE_INTERVAL_SECONDS = 300  # 5 minutos
