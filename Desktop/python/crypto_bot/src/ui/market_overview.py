import customtkinter as ctk
from .styles import *
import pandas as pd

class MarketOverview(ctk.CTkFrame):
    """Multi-pair market overview panel"""
    def __init__(self, master, bot, on_pair_select):
        super().__init__(master, fg_color=COLOR_BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=COLOR_BORDER)
        self.bot = bot
        self.on_pair_select = on_pair_select
        
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
        
        # Rows
        self.rows_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.rows_frame.pack(fill="both", expand=True, padx=2, pady=(0, 2))
        
        self.pair_rows = {}
        
        from ..config import PAIRS
        for idx, pair in enumerate(PAIRS):
            self._create_pair_row(idx, pair)
        
        self.update_market_data()
    
    def _create_pair_row(self, idx, pair):
        row_bg = "transparent" if idx % 2 == 0 else "#181A20"
        row_frame = ctk.CTkFrame(self.rows_frame, fg_color=row_bg, cursor="hand2", corner_radius=0)
        row_frame.pack(fill="x", pady=0)
        
        def on_click(e): self.on_pair_select(pair)
        row_frame.bind("<Button-1>", on_click)
        
        # Pair
        p_lbl = ctk.CTkLabel(row_frame, text=pair, font=(FONT_FAMILY, 12, "bold"), width=100, anchor="w")
        p_lbl.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        p_lbl.bind("<Button-1>", on_click)
        
        # Price
        pr_lbl = ctk.CTkLabel(row_frame, text="Loading...", font=(FONT_FAMILY, 12), width=120, anchor="w")
        pr_lbl.grid(row=0, column=1, padx=15, pady=10, sticky="w")
        pr_lbl.bind("<Button-1>", on_click)
        
        # Change
        ch_lbl = ctk.CTkLabel(row_frame, text="--", font=(FONT_FAMILY, 11), width=100, anchor="w")
        ch_lbl.grid(row=0, column=2, padx=15, pady=10, sticky="w")
        ch_lbl.bind("<Button-1>", on_click)
        
        # RSI
        rs_lbl = ctk.CTkLabel(row_frame, text="--", font=(FONT_FAMILY, 11), width=80, anchor="w")
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
            'signal_frame': sig_frame
        }
    
    def update_market_data(self):
        if not self.winfo_exists():
            return
        from ..config import PAIRS
        for pair in PAIRS:
            try:
                df = self.bot.get_chart_data(pair)
                if df is None or df.empty: continue
                
                curr = df['close'].iloc[-1]
                prev = df['close'].iloc[0]
                chg = ((curr - prev) / prev) * 100
                
                from ..bot import rsi, ema
                rsi_v = rsi(df['close']).iloc[-1]
                ef = ema(df['close'], 9)
                es = ema(df['close'], 21)
                
                if ef.iloc[-2] < es.iloc[-2] and ef.iloc[-1] > es.iloc[-1] and rsi_v < 40:
                    sig, col, bg = "BUY", COLOR_ACCENT_BUY, "#142620"
                elif ef.iloc[-2] > es.iloc[-2] and ef.iloc[-1] < es.iloc[-1] and rsi_v > 60:
                    sig, col, bg = "SELL", COLOR_ACCENT_SELL, "#2D191E"
                else:
                    sig, col, bg = "NEUTRAL", COLOR_TEXT_SECONDARY, "#2B3139"
                
                row = self.pair_rows[pair]
                row['price'].configure(text=f"${curr:,.2f}")
                row['change'].configure(text=f"{chg:+.2f}%", text_color=COLOR_ACCENT_BUY if chg>=0 else COLOR_ACCENT_SELL)
                row['rsi'].configure(text=f"{rsi_v:.0f}")
                row['signal_lbl'].configure(text=sig, text_color=col)
                row['signal_frame'].configure(fg_color=bg)
                
            except: pass
        
        # Schedule next update (faster: 5 seconds)
        self.after(5000, self.update_market_data)
