import customtkinter as ctk
from .styles import *
import pandas as pd
import threading

class MarketOverview(ctk.CTkFrame):
    """Multi-pair market overview panel"""
    def __init__(self, master, bot, on_pair_select):
        super().__init__(master, fg_color=COLOR_BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=COLOR_BORDER)
        self.bot = bot
        self.on_pair_select = on_pair_select
        self.active_pair = None
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="📡 MARKET OVERVIEW",
            font=(FONT_FAMILY, 14, "bold"),
            text_color=COLOR_TEXT_SECONDARY
        ).pack(side="left")
        
        # Headers Table
        headers_frame = ctk.CTkFrame(self, fg_color="#181A20", corner_radius=0)
        headers_frame.pack(fill="x", padx=2, pady=0)
        
        headers = ["Pair", "Price", "24h Chg", "RSI (14)", "Signal"]
        widths = [100, 120, 100, 80, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(
                headers_frame,
                text=header.upper(),
                font=(FONT_FAMILY, 10, "bold"),
                text_color=COLOR_TEXT_MUTED,
                width=width,
                anchor="w"
            )
            lbl.grid(row=0, column=i, padx=15, pady=10, sticky="w")
        
        # Rows (scrollable with fixed visible height to avoid being collapsed by the chart)
        self.rows_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLOR_BG_SECONDARY,
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_TEXT_MUTED,
            height=220
        )
        self.rows_frame.pack(fill="both", expand=True, padx=0, pady=(0, 2))
        self.rows_frame.pack_propagate(False)
        # Use grid inside scrollable frame to avoid pack/layout conflicts
        try:
            self.rows_frame.grid_columnconfigure(0, weight=1)
        except Exception:
            pass
        
        self.pair_rows = {}
        
        from ..config import PAIRS
        pairs = PAIRS or ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        for idx, pair in enumerate(pairs):
            self._create_pair_row(idx, pair)
        
        self.update_market_data()

    def set_active_pair(self, pair):
        """Visually highlight the active pair row"""
        self.active_pair = pair
        for p, row in self.pair_rows.items():
            if p == pair:
                row['frame'].configure(border_width=2, border_color=COLOR_ACCENT_MAIN)
            else:
                row['frame'].configure(border_width=0, border_color=COLOR_BORDER)
    
    def _create_pair_row(self, idx, pair):
        row_bg = "#11151b" if idx % 2 == 0 else "#181A20"
        row_frame = ctk.CTkFrame(self.rows_frame, fg_color=row_bg, cursor="hand2", corner_radius=0, border_width=0, border_color=COLOR_BORDER)
        row_frame.configure(height=46)
        # Place rows using grid to ensure they render inside CTkScrollableFrame
        row_frame.grid(row=idx, column=0, sticky="ew", padx=0, pady=0)
        try:
            self.rows_frame.grid_rowconfigure(idx, weight=0)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(2, weight=1)
            row_frame.grid_columnconfigure(3, weight=1)
            row_frame.grid_columnconfigure(4, weight=1)
        except Exception:
            pass
        
        def on_click(e): self.on_pair_select(pair)
        row_frame.bind("<Button-1>", on_click)
        
        # Pair
        p_lbl = ctk.CTkLabel(row_frame, text=pair, font=(FONT_FAMILY, 12, "bold"), width=100, anchor="w", text_color=COLOR_TEXT_PRIMARY)
        p_lbl.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        p_lbl.bind("<Button-1>", on_click)
        
        # Price
        pr_lbl = ctk.CTkLabel(row_frame, text="Loading...", font=(FONT_FAMILY, 12, "bold"), width=120, anchor="w", text_color=COLOR_TEXT_PRIMARY)
        pr_lbl.grid(row=0, column=1, padx=15, pady=10, sticky="w")
        pr_lbl.bind("<Button-1>", on_click)
        
        # Change
        ch_lbl = ctk.CTkLabel(row_frame, text="--", font=(FONT_FAMILY, 11), width=100, anchor="w", text_color=COLOR_TEXT_PRIMARY)
        ch_lbl.grid(row=0, column=2, padx=15, pady=10, sticky="w")
        ch_lbl.bind("<Button-1>", on_click)
        
        # RSI
        rs_lbl = ctk.CTkLabel(row_frame, text="--", font=(FONT_FAMILY, 11), width=80, anchor="w", text_color=COLOR_TEXT_PRIMARY)
        rs_lbl.grid(row=0, column=3, padx=15, pady=10, sticky="w")
        rs_lbl.bind("<Button-1>", on_click)
        
        # Signal Badge
        sig_frame = ctk.CTkFrame(row_frame, fg_color="#2B3139", corner_radius=4, width=80, height=24)
        sig_frame.grid(row=0, column=4, padx=15, pady=10, sticky="w")
        sig_frame.grid_propagate(False)
        sig_frame.bind("<Button-1>", on_click)
        
        sig_lbl = ctk.CTkLabel(sig_frame, text="--", font=(FONT_FAMILY, 10, "bold"), text_color=COLOR_TEXT_SECONDARY)
        sig_lbl.place(relx=0.5, rely=0.5, anchor="center")
        sig_lbl.bind("<Button-1>", on_click)
        
        self.pair_rows[pair] = {
            'frame': row_frame,
            'price': pr_lbl,
            'change': ch_lbl,
            'rsi': rs_lbl,
            'signal_lbl': sig_lbl,
            'signal_frame': sig_frame,
            'default_bg': row_bg
        }
    
    def update_market_data(self):
        if not self.winfo_exists():
            return
        from ..config import PAIRS
        pairs = PAIRS or list(self.pair_rows.keys())

        # Ensure rows exist if they were not created for any reason
        if not self.pair_rows:
            for idx, pair in enumerate(pairs):
                self._create_pair_row(idx, pair)

        def worker():
            results = []
            for pair in pairs:
                try:
                    df = self.bot.get_chart_data(pair)
                    results.append((pair, df, None))
                except Exception as e:
                    results.append((pair, None, e))
            self.after(0, lambda: self._apply_market_data(results))

        threading.Thread(target=worker, daemon=True).start()
        # Schedule next update (faster: 5 seconds)
        self.after(5000, self.update_market_data)

    def _apply_market_data(self, results):
        from ..bot import rsi, ema
        for pair, df, err in results:
            if err:
                row = self.pair_rows.get(pair)
                if row:
                    row['price'].configure(text="--")
                    row['change'].configure(text="--")
                    row['rsi'].configure(text="--")
                    row['signal_lbl'].configure(text="ERROR", text_color=COLOR_ACCENT_SELL)
                    row['signal_frame'].configure(fg_color="#2D191E")
                continue

            if df is None or df.empty:
                row = self.pair_rows.get(pair)
                if row:
                    row['price'].configure(text="--")
                    row['change'].configure(text="--")
                    row['rsi'].configure(text="--")
                    row['signal_lbl'].configure(text="NO DATA", text_color=COLOR_TEXT_SECONDARY)
                    row['signal_frame'].configure(fg_color="#2B3139")
                continue

            curr = df['close'].iloc[-1]
            prev = df['close'].iloc[0]
            chg = ((curr - prev) / prev) * 100

            rsi_v = rsi(df['close']).iloc[-1]
            ef = ema(df['close'], 9)
            es = ema(df['close'], 21)

            if ef.iloc[-2] < es.iloc[-2] and ef.iloc[-1] > es.iloc[-1] and rsi_v < 40:
                sig, col, bg = "BUY", COLOR_ACCENT_BUY, "#142620"
            elif ef.iloc[-2] > es.iloc[-2] and ef.iloc[-1] < es.iloc[-1] and rsi_v > 60:
                sig, col, bg = "SELL", COLOR_ACCENT_SELL, "#2D191E"
            else:
                sig, col, bg = "NEUTRAL", COLOR_TEXT_SECONDARY, "#2B3139"

            row = self.pair_rows.get(pair)
            if not row:
                continue

            row['price'].configure(text=f"${curr:,.2f}")
            row['change'].configure(text=f"{chg:+.2f}%", text_color=COLOR_ACCENT_BUY if chg>=0 else COLOR_ACCENT_SELL)
            row['rsi'].configure(text=f"{rsi_v:.0f}")
            row['signal_lbl'].configure(text=sig, text_color=col)
            row['signal_frame'].configure(fg_color=bg)
