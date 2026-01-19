# Dependencias:
# pip install customtkinter python-binance pandas matplotlib schedule mplfinance

import customtkinter as ctk
from threading import Thread
import schedule, time, datetime
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplfinance as mpf
from binance.client import Client

# === Configuración Binance ===
API_KEY = "TU_API_KEY"
API_SECRET = "TU_API_SECRET"
PAIRS = ["BNBUSDT", "BTCUSDT", "ETHUSDT"]
INTERVAL = Client.KLINE_INTERVAL_5MINUTE
LIMIT = 100
ENTRY_SIZE = 5  # cada entrada será de 5 USDT

client = Client(API_KEY, API_SECRET)
running = False

# === Capital fijo ===
capital_inicial = 25.0
capital_actual = capital_inicial
profit_loss_total = 0.0  # acumulado de ganancias/pérdidas en USDT

# === Estadísticas ===
buy_count = 0
sell_count = 0
win_count = 0
loss_count = 0
last_signal = "Ninguna"

# === Indicadores ===
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

# === Gestión de riesgo (1:3) ===
def calculate_levels(price, signal_type):
    risk_percent = 0.02   # 2% stop
    reward_percent = 0.06 # 6% take profit (1:3 ratio)

    if signal_type == "BUY":
        stop_loss = price * (1 - risk_percent)
        take_profit = price * (1 + reward_percent)
    else:  # SELL
        stop_loss = price * (1 + risk_percent)
        take_profit = price * (1 - reward_percent)

    return stop_loss, take_profit

# === Señales ===
def check_signal(symbol):
    global buy_count, sell_count, win_count, loss_count, last_signal, capital_actual, profit_loss_total

    try:
        klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=LIMIT)
    except Exception as e:
        msg = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ❌ Error al obtener datos de {symbol}: {e}"
        text_box.insert("end", msg + "\n")
        text_box.see("end")
        return

    df = pd.DataFrame(klines, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_asset_volume","trades",
        "taker_buy_base","taker_buy_quote","ignore"
    ])
    df["close"] = df["close"].astype(float)

    closes = df["close"]
    ema_fast = ema(closes, 9)
    ema_slow = ema(closes, 21)
    rsi_val = rsi(closes).iloc[-1]
    price = closes.iloc[-1]

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if ema_fast.iloc[-2] < ema_slow.iloc[-2] and ema_fast.iloc[-1] > ema_slow.iloc[-1] and rsi_val < 40:
        stop_loss, take_profit = calculate_levels(price, "BUY")
        signal = (
            f"{timestamp} 📈 BUY {symbol} — Entrada: $5 — Precio: {price:.2f}, "
            f"SL: {stop_loss:.2f}, TP: {take_profit:.2f}, RSI: {rsi_val:.2f}"
        )
        buy_count += 1
        last_signal = signal
        gain = ENTRY_SIZE * 0.06
        capital_actual += gain
        profit_loss_total += gain
        win_count += 1

    elif ema_fast.iloc[-2] > ema_slow.iloc[-2] and ema_fast.iloc[-1] < ema_slow.iloc[-1] and rsi_val > 60:
        stop_loss, take_profit = calculate_levels(price, "SELL")
        signal = (
            f"{timestamp} 📉 SELL {symbol} — Entrada: $5 — Precio: {price:.2f}, "
            f"SL: {stop_loss:.2f}, TP: {take_profit:.2f}, RSI: {rsi_val:.2f}"
        )
        sell_count += 1
        last_signal = signal
        loss = ENTRY_SIZE * 0.02
        capital_actual -= loss
        profit_loss_total -= loss
        loss_count += 1

    else:
        signal = f"{timestamp} ⏳ Sin señal en {symbol}. RSI={rsi_val:.2f}"

    # Mostrar en interfaz
    text_box.insert("end", signal + "\n")
    text_box.see("end")

    # Guardar en CSV
    try:
        with open("signals_history.csv", "a", encoding="utf-8") as f:
            f.write(
                f"{signal} | Capital actual: {capital_actual:.2f} | "
                f"Gan/Pérdida acumulada: {profit_loss_total:.2f}\n"
            )
    except Exception as e:
        text_box.insert("end", f"⚠️ Error al escribir CSV: {e}\n")

    # Actualizar estadísticas
    rendimiento = ((capital_actual - capital_inicial) / capital_inicial) * 100
    stats_label.configure(
        text=(
            f"📊 BUY: {buy_count}, SELL: {sell_count}, Ganadoras: {win_count}, Perdedoras: {loss_count}\n"
            f"💰 Capital inicial: {capital_inicial:.2f} USDT — Actual: {capital_actual:.2f} USDT\n"
            f"📈 Rendimiento: {rendimiento:.2f}% — Gan/Pérdida acumulada: {profit_loss_total:.2f} USDT\n"
            f"Última señal: {last_signal}"
        )
    )

# === Loop del bot ===
def job():
    for pair in PAIRS:
        check_signal(pair)

def run_bot():
    while running:
        schedule.run_pending()
        time.sleep(1)

def start_bot():
    global running
    if running:
        return
    running = True
    schedule.clear()
    schedule.every(5).minutes.do(job)
    Thread(target=run_bot, daemon=True).start()
    status_label.configure(text="✅ Bot en ejecución")
    text_box.insert("end", "▶ Bot iniciado. Revisando pares cada 5 minutos...\n")

def stop_bot():
    global running
    running = False
    status_label.configure(text="⏳ Bot detenido")
    text_box.insert("end", "⏹ Bot detenido.\n")

# === Gráfico de velas japonesas con abrir/cerrar y selección de par ===
chart_frame = None

def show_chart():
    global chart_frame

    symbol = pair_entry.get().strip().upper()
    if not symbol:
        text_box.insert("end", "⚠️ Debes escribir un par, ejemplo: BTCUSDT\n")
        return

    try:
        klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=LIMIT)
    except Exception as e:
        text_box.insert("end", f"❌ Error al obtener datos de {symbol}: {e}\n")
        return

    df = pd.DataFrame(klines, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_asset_volume","trades",
        "taker_buy_base","taker_buy_quote","ignore"
    ])
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)

    # Si ya hay un gráfico abierto, cerrarlo primero
    close_chart()

    chart_frame = ctk.CTkFrame(root)
    chart_frame.pack(pady=10, fill="both", expand=True)

    close_button = ctk.CTkButton(chart_frame, text="❌ Cerrar gráfico", command=close_chart)
    close_button.pack(pady=5)

    fig, ax = mpf.plot(
        df,
        type="candle",
        style="charles",   # prueba 'binance', 'yahoo', 'classic' si prefieres
        volume=True,
        title=f"{symbol} - Velas japonesas (5m)",
        returnfig=True
    )

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    text_box.insert("end", f"📊 Gráfico de velas japonesas mostrado para {symbol}.\n")

def close_chart():
    global chart_frame
    if chart_frame is not None:
        chart_frame.destroy()
        chart_frame = None
        text_box.insert("end", "❌ Gráfico cerrado.\n")

# === Historial: abrir/cerrar como el gráfico ===
history_box = None
history_label = None

def show_history():
    global history_box, history_label
    try:
        with open("signals_history.csv", "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        content = "⚠️ No existe aún el archivo de historial."
    except Exception as e:
        content = f"❌ Error al leer historial: {e}"

    # Si ya existen, destruirlos primero
    close_history()

    history_label = ctk.CTkLabel(root, text="📂 Historial de operaciones guardadas:")
    history_label.pack(pady=5)

    history_box = ctk.CTkTextbox(root, height=10, width=980)
    history_box.pack(padx=10, pady=5, fill="both", expand=True)
    history_box.insert("end", content)

    text_box.insert("end", "📂 Historial mostrado.\n")

def close_history():
    global history_box, history_label
    if history_box is not None:
        history_box.destroy()
        history_box = None
    if history_label is not None:
        history_label.destroy()
        history_label = None
    text_box.insert("end", "❌ Historial cerrado.\n")

# === Interfaz CustomTkinter ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Bot de Trading Spot")
root.geometry("1100x820")

# Frame superior (controles)
top_frame = ctk.CTkFrame(root)
top_frame.pack(fill="x", padx=10, pady=10)

status_label = ctk.CTkLabel(top_frame, text="⏳ Bot detenido", font=("Arial", 16))
status_label.pack(side="left", padx=10)

start_button = ctk.CTkButton(top_frame, text="▶ Iniciar Bot", command=start_bot)
start_button.pack(side="left", padx=5)

stop_button = ctk.CTkButton(top_frame, text="⏹ Detener Bot", command=stop_bot)
stop_button.pack(side="left", padx=5)

# Selector de par para el gráfico
pair_label = ctk.CTkLabel(top_frame, text="Par (ej: BTCUSDT):")
pair_label.pack(side="left", padx=10)

pair_entry = ctk.CTkEntry(top_frame, width=160)
pair_entry.insert(0, "BTCUSDT")
pair_entry.pack(side="left")

chart_button = ctk.CTkButton(top_frame, text="📊 Mostrar gráfico", command=show_chart)
chart_button.pack(side="left", padx=5)

close_chart_button = ctk.CTkButton(top_frame, text="❌ Cerrar gráfico", command=close_chart)
close_chart_button.pack(side="left", padx=5)

# Botones de historial
history_button = ctk.CTkButton(top_frame, text="📂 Ver historial", command=show_history)
history_button.pack(side="left", padx=5)

close_history_button = ctk.CTkButton(top_frame, text="❌ Cerrar historial", command=close_history)
close_history_button.pack(side="left", padx=5)

# Estadísticas
stats_label = ctk.CTkLabel(
    root,
    text=(
        f"📊 BUY: 0, SELL: 0, Ganadoras: 0, Perdedoras: 0\n"
        f"💰 Capital inicial: {capital_inicial:.2f} USDT — Actual: {capital_actual:.2f} USDT\n"
        f"📈 Rendimiento: 0.00% — Gan/Pérdida acumulada: {profit_loss_total:.2f} USDT\n"
        f"Última señal: Ninguna"
    ),
    font=("Arial", 14),
    justify="left"
)
stats_label.pack(padx=10, pady=10, fill="x")

# Cuadro de texto para señales en vivo
text_box = ctk.CTkTextbox(root, height=16, width=980)
text_box.pack(padx=10, pady=5, fill="both", expand=True)

# Iniciar interfaz
root.mainloop()