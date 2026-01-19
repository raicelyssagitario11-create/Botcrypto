import schedule
import time
import datetime
import pandas as pd
import threading
import ctypes
from binance.client import Client
from .config import API_KEY, API_SECRET, PAIRS, INTERVAL, LIMIT, ENTRY_SIZE
from .data_manager import DataManager

# Indicators
def ema(series, period):
    return pd.Series(series).ewm(span=period, adjust=False).mean()

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

class TradingBot:
    def __init__(self, log_callback=None, stats_callback=None, notification_callback=None):
        self.client = Client(API_KEY, API_SECRET)
        self.running = False
        self.log_callback = log_callback      # Function to call with new log messages
        self.stats_callback = stats_callback  # Function to call with updated stats
        self.notification_callback = notification_callback  # Function to call with signal notifications
        
        # Initialize data manager
        self.data_manager = DataManager()
        
        # Migrate old CSV data if exists
        self.history_file = "signals_history.csv"
        self.data_manager.migrate_from_csv(self.history_file)
        
        # Load saved state
        saved_state = self.data_manager.load_bot_state()
        self.capital_initial = saved_state["capital_initial"]
        self.capital_actual = saved_state["capital_actual"]
        self.profit_loss_total = saved_state["profit_loss_total"]
        self.buy_count = saved_state["buy_count"]
        self.sell_count = saved_state["sell_count"]
        self.win_count = saved_state["win_count"]
        self.loss_count = saved_state["loss_count"]
        self.last_signal = saved_state["last_signal"]

    def log(self, message):
        if self.log_callback:
            self.log_callback(message)
        print(message) # Fallback

    def update_stats(self):
        # Save state to data manager
        self.data_manager.update_capital(
            self.capital_initial,
            self.capital_actual,
            self.profit_loss_total
        )
        self.data_manager.update_statistics(
            self.buy_count,
            self.sell_count,
            self.win_count,
            self.loss_count,
            self.last_signal
        )
        
        if self.stats_callback:
            stats = {
                "capital_initial": self.capital_initial,
                "capital_actual": self.capital_actual,
                "pnl": self.profit_loss_total,
                "buy_count": self.buy_count,
                "sell_count": self.sell_count,
                "win_count": self.win_count,
                "loss_count": self.loss_count,
                "last_signal": self.last_signal
            }
            self.stats_callback(stats)

    def calculate_levels(self, price, signal_type):
        risk_percent = 0.02
        reward_percent = 0.06
        if signal_type == "BUY":
            stop_loss = price * (1 - risk_percent)
            take_profit = price * (1 + reward_percent)
        else: # SELL
            stop_loss = price * (1 + risk_percent)
            take_profit = price * (1 - reward_percent)
        return stop_loss, take_profit

    def check_signal(self, symbol):
        try:
            klines = self.client.get_klines(symbol=symbol, interval=INTERVAL, limit=LIMIT)
        except Exception as e:
            self.log(f"❌ Error al obtener datos de {symbol}: {e}")
            return

    def _process_klines(self, klines):
        df = pd.DataFrame(klines, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","quote_asset_volume","trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])
        df["close"] = df["close"].astype(float)
        return df

    def check_signal(self, symbol):
        try:
            klines = self.client.get_klines(symbol=symbol, interval=INTERVAL, limit=LIMIT)
        except Exception as e:
            self.log(f"❌ Error al obtener datos de {symbol}: {e}")
            return
        
        df = self._process_klines(klines)

        closes = df["close"]
        ema_fast = ema(closes, 9)
        ema_slow = ema(closes, 21)
        rsi_val = rsi(closes).iloc[-1]
        price = closes.iloc[-1]
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Logic
        signal_msg = None
        signal_data = None
        
        if ema_fast.iloc[-2] < ema_slow.iloc[-2] and ema_fast.iloc[-1] > ema_slow.iloc[-1] and rsi_val < 40:
            stop_loss, take_profit = self.calculate_levels(price, "BUY")
            gain = ENTRY_SIZE * 0.06
            self.capital_actual += gain
            self.profit_loss_total += gain
            
            signal_msg = f"{timestamp} 📈 BUY {symbol} @ {price:.2f} (SL: {stop_loss:.2f}, TP: {take_profit:.2f})"
            signal_data = {
                'timestamp': timestamp,
                'signal_type': 'BUY',
                'pair': symbol,
                'price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'capital_after': self.capital_actual,
                'pnl': gain,
                'status': 'completed',
                # For notification (legacy format)
                'type': 'BUY',
                'sl': stop_loss,
                'tp': take_profit
            }
            self.buy_count += 1
            self.win_count += 1 # Simulado ganadora
            self.last_signal = f"BUY {symbol}"

        elif ema_fast.iloc[-2] > ema_slow.iloc[-2] and ema_fast.iloc[-1] < ema_slow.iloc[-1] and rsi_val > 60:
            stop_loss, take_profit = self.calculate_levels(price, "SELL")
            loss = ENTRY_SIZE * 0.02
            self.capital_actual -= loss
            self.profit_loss_total -= loss
            
            signal_msg = f"{timestamp} 📉 SELL {symbol} @ {price:.2f} (SL: {stop_loss:.2f}, TP: {take_profit:.2f})"
            signal_data = {
                'timestamp': timestamp,
                'signal_type': 'SELL',
                'pair': symbol,
                'price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'capital_after': self.capital_actual,
                'pnl': -loss,
                'status': 'completed',
                # For notification (legacy format)
                'type': 'SELL',
                'sl': stop_loss,
                'tp': take_profit
            }
            self.sell_count += 1
            self.loss_count += 1 # Simulado perdedora
            self.last_signal = f"SELL {symbol}"

        else:
            # self.log(f"{timestamp} ⏳ Sin señal en {symbol}. RSI={rsi_val:.2f}")
            pass

        if signal_msg:
            self.log(signal_msg)
            self.save_to_history(signal_msg, signal_data)
            self.update_stats()
            
            # Trigger notification
            if self.notification_callback and signal_data:
                self.notification_callback(signal_data)

    def save_to_history(self, message, signal_data=None):
        # Legacy CSV save (optional, for backup)
        try:
             with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(f"{message} | Cap: {self.capital_actual:.2f}\n")
        except Exception as e:
            self.log(f"⚠️ Error CSV: {e}")
        
        # Save to JSON via DataManager
        if signal_data:
            try:
                self.data_manager.save_signal(signal_data)
            except Exception as e:
                self.log(f"⚠️ Error saving to data manager: {e}")

    def job(self):
        for pair in PAIRS:
            self.check_signal(pair)

    def _run_loop(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def _prevent_sleep(self):
        """Prevent Windows from entering sleep mode while the bot is running"""
        try:
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_AWAYMODE_REQUIRED
            # This tells Windows the system is performing a background task and should not sleep
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001 | 0x00000040)
            self.log("🛡️ Prevención de suspensión activada")
        except Exception as e:
            self.log(f"⚠️ No se pudo activar la prevención de suspensión: {e}")

    def _allow_sleep(self):
        """Allow Windows to enter sleep mode normally"""
        try:
            # ES_CONTINUOUS (reset to default)
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            self.log("💤 Prevención de suspensión desactivada")
        except Exception as e:
            self.log(f"⚠️ No se pudo desactivar la prevención de suspensión: {e}")

    def start(self):
        if self.running:
            return
        self.running = True
        self.data_manager.set_running_state(True)
        self._prevent_sleep()
        
        schedule.clear()
        schedule.every(30).seconds.do(self.job)
        threading.Thread(target=self._run_loop, daemon=True).start()
        self.log("✅ Bot iniciado. Escaneando cada 30 segundos...")

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.data_manager.set_running_state(False)
        self._allow_sleep()
        self.log("⏹ Bot detenido.")

    def _process_klines(self, klines):
        df = pd.DataFrame(klines, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","quote_asset_volume","trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])
        cols = ["open", "high", "low", "close", "volume"]
        for c in cols:
            df[c] = df[c].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df.set_index("open_time", inplace=True)
        return df

    def get_current_price(self, symbol):
        """Get the current ticker price for a symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except Exception as e:
            self.log(f"Error fetching price for {symbol}: {e}")
            return None

    def get_chart_data(self, symbol):
        try:
            klines = self.client.get_klines(symbol=symbol, interval=INTERVAL, limit=LIMIT)
            return self._process_klines(klines)
        except Exception as e:
            self.log(f"Error fetching chart data: {e}")
            return None
    
    def update_initial_capital(self, new_capital: float):
        """Update the initial capital (callable from UI)"""
        self.capital_initial = new_capital
        self.capital_actual = new_capital
        self.profit_loss_total = 0.0
        self.update_stats()
        self.log(f"💰 Capital inicial actualizado a {new_capital:.2f} USDT")
    
    def reset_statistics(self):
        """Reset all statistics while keeping history"""
        self.data_manager.reset_statistics()
        
        # Reload state
        saved_state = self.data_manager.load_bot_state()
        self.capital_initial = saved_state["capital_initial"]
        self.capital_actual = saved_state["capital_actual"]
        self.profit_loss_total = saved_state["profit_loss_total"]
        self.buy_count = saved_state["buy_count"]
        self.sell_count = saved_state["sell_count"]
        self.win_count = saved_state["win_count"]
        self.loss_count = saved_state["loss_count"]
        self.last_signal = saved_state["last_signal"]
        
        self.update_stats()
        self.log("🔄 Estadísticas reseteadas")
