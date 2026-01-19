import customtkinter as ctk
import os
from datetime import datetime
from tkinter import filedialog
from .styles import *

class HistoryView(ctk.CTkFrame):
    """Professional history table for past signals"""
    def __init__(self, master, bot):
        super().__init__(master, fg_color=COLOR_BG_PRIMARY)
        self.bot = bot
        
        # Header Area
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(side="left")

        ctk.CTkLabel(
            title_container,
            text="📜 TRADING HISTORY",
            font=(FONT_FAMILY, 24, "bold"),
            text_color=COLOR_TEXT_PRIMARY
        ).pack(side="top", anchor="w")

        ctk.CTkLabel(
            title_container,
            text="Detailed log of all automated trading signals",
            font=(FONT_FAMILY, 12),
            text_color=COLOR_TEXT_MUTED
        ).pack(side="top", anchor="w")
        
        # Action Buttons
        refresh_btn = ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            command=self.load_history,
            fg_color="#2B3139",
            hover_color=COLOR_ACCENT_HOVER_BUY,
            width=110,
            font=(FONT_FAMILY, 12, "bold"),
            corner_radius=6
        )
        refresh_btn.pack(side="right", padx=(10, 0))
        
        export_btn = ctk.CTkButton(
            header_frame,
            text="📥 Export CSV",
            command=self.export_history,
            fg_color=COLOR_ACCENT_MAIN,
            hover_color=COLOR_ACCENT_MAIN_HOVER,
            text_color="black",
            width=110,
            font=(FONT_FAMILY, 12, "bold"),
            corner_radius=6
        )
        export_btn.pack(side="right", padx=10)
        
        # Table container
        table_container = ctk.CTkFrame(self, fg_color=COLOR_BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=COLOR_BORDER)
        table_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        # Headers
        headers_frame = ctk.CTkFrame(table_container, fg_color="#181A20", corner_radius=0)
        headers_frame.pack(fill="x", padx=2, pady=2)
        
        headers = ["Time", "Pair", "Signal", "Price", "SL", "TP", "Status"]
        widths = [150, 100, 80, 100, 100, 100, 100]
        
        for i, (header, width) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(
                headers_frame,
                text=header.upper(),
                font=(FONT_FAMILY, 11, "bold"),
                text_color=COLOR_TEXT_MUTED,
                width=width,
                anchor="w"
            )
            lbl.grid(row=0, column=i, padx=15, pady=12, sticky="w")
        
        # Scrollable rows
        self.rows_frame = ctk.CTkScrollableFrame(
            table_container,
            fg_color="transparent",
            scrollbar_button_color=COLOR_BORDER,
            scrollbar_button_hover_color=COLOR_TEXT_MUTED
        )
        self.rows_frame.pack(fill="both", expand=True, padx=2, pady=(0, 10))
        
        # Load initial data
        self.load_history()
    
    def load_history(self):
        """Load trading history from JSON"""
        for widget in self.rows_frame.winfo_children():
            widget.destroy()
        
        try:
            history = self.bot.data_manager.load_trading_history()
            
            if not history:
                no_data = ctk.CTkLabel(
                    self.rows_frame,
                    text="No trading history yet. Start the bot to generate signals!",
                    font=(FONT_FAMILY, 14),
                    text_color=COLOR_TEXT_MUTED
                )
                no_data.pack(pady=100)
                return
            
            history.reverse()
            for idx, signal in enumerate(history[:50]):
                self._create_history_row(idx, signal)
                
        except Exception as e:
            error_lbl = ctk.CTkLabel(
                self.rows_frame,
                text=f"Error loading history: {e}",
                font=(FONT_FAMILY, 12),
                text_color=COLOR_ACCENT_SELL
            )
            error_lbl.pack(pady=20)
    
    def _create_history_row(self, idx, signal):
        """Create a row from signal dictionary"""
        try:
            time_str = signal.get("timestamp", "Unknown")
            signal_type = signal.get("signal_type", "NEUTRAL")
            pair = signal.get("pair", "Unknown")
            price = signal.get("price", 0.0)
            sl = signal.get("stop_loss", 0.0)
            tp = signal.get("take_profit", 0.0)
            status = signal.get("status", "completed")
            
            signal_color = COLOR_ACCENT_BUY if signal_type == "BUY" else COLOR_ACCENT_SELL
            
            # Create row
            row_bg = "transparent" if idx % 2 == 0 else "#181A20"
            row_frame = ctk.CTkFrame(self.rows_frame, fg_color=row_bg, corner_radius=0)
            row_frame.pack(fill="x", pady=0)
            
            # Columns
            ctk.CTkLabel(row_frame, text=time_str, font=(FONT_FAMILY, 11), width=150, anchor="w", text_color=COLOR_TEXT_SECONDARY).grid(row=0, column=0, padx=15, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=pair, font=(FONT_FAMILY, 11, "bold"), width=100, anchor="w", text_color=COLOR_TEXT_PRIMARY).grid(row=0, column=1, padx=15, pady=8, sticky="w")
            
            # Signal badge
            s_bg = "#142620" if signal_type == "BUY" else "#2D191E"
            sig_lbl = ctk.CTkLabel(row_frame, text=signal_type, font=(FONT_FAMILY, 10, "bold"), text_color=signal_color, width=70, fg_color=s_bg, corner_radius=4)
            sig_lbl.grid(row=0, column=2, padx=15, pady=8, sticky="w")
            
            ctk.CTkLabel(row_frame, text=f"{price:,.2f}", font=(FONT_FAMILY, 11), width=100, anchor="w").grid(row=0, column=3, padx=15, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"{sl:,.2f}", font=(FONT_FAMILY, 11), width=100, anchor="w", text_color=COLOR_TEXT_MUTED).grid(row=0, column=4, padx=15, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=f"{tp:,.2f}", font=(FONT_FAMILY, 11), width=100, anchor="w", text_color=COLOR_TEXT_MUTED).grid(row=0, column=5, padx=15, pady=8, sticky="w")
            ctk.CTkLabel(row_frame, text=status.capitalize(), font=(FONT_FAMILY, 11), text_color=signal_color, width=100, anchor="w").grid(row=0, column=6, padx=15, pady=8, sticky="w")
            
        except Exception as e:
            pass
    
    def export_history(self):
        """Export history to CSV using a file dialog"""
        try:
            # Default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"trading_history_{timestamp}.csv"
            
            # Show Save As Dialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_name,
                title="Export Trading History"
            )
            
            if not file_path:
                return # User cancelled

            # Export via DataManager
            self.bot.data_manager.export_to_csv(file_path)
            
            # Visual Feedback
            feedback_lbl = ctk.CTkLabel(
                self, 
                text=f"✅ Exported successfully!", 
                font=(FONT_FAMILY, 12, "bold"),
                fg_color=COLOR_ACCENT_BUY,
                text_color="black",
                corner_radius=6,
                padx=20,
                pady=10
            )
            feedback_lbl.place(relx=0.5, rely=0.9, anchor="s")
            self.after(3000, feedback_lbl.destroy)
            self.bot.log(f"✅ History exported to: {file_path}")
            
        except Exception as e:
            self.bot.log(f"❌ Export failed: {e}")
