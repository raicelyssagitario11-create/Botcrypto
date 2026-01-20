import customtkinter as ctk
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog
from .styles import *

class HistoryView(ctk.CTkFrame):
    """Tabla profesional del historial de señales con scroll y export."""
    def __init__(self, master, bot):
        super().__init__(master, fg_color=COLOR_BG_PRIMARY)
        self.bot = bot
        self._auto_refresh_id = None
        self._auto_refresh_ms = 15000  # 15s
        
        # Área de encabezado
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
        
        # Action Buttons (Refresh removed per request)
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
        
        # Contenedor de tabla (Canvas + scrollbars para H/V)
        table_container = ctk.CTkFrame(self, fg_color=COLOR_BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=COLOR_BORDER)
        table_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        try:
            table_container.grid_columnconfigure(0, weight=1)
            table_container.grid_rowconfigure(1, weight=1)
        except Exception:
            pass

        # Canvas para scroll horizontal y vertical
        self.table_canvas = tk.Canvas(table_container, bg=COLOR_BG_SECONDARY, highlightthickness=0, bd=0)
        self.table_canvas.grid(row=1, column=0, sticky="nsew", padx=2, pady=(0, 2))
        
        # Scrollbars (tema oscuro, integradas con CTk)
        self.h_scroll = ctk.CTkScrollbar(
            table_container,
            orientation="horizontal",
            command=self.table_canvas.xview,
            fg_color=COLOR_BG_PRIMARY,
            button_color=COLOR_BG_CARD,
            button_hover_color=COLOR_BORDER
        )
        self.h_scroll.grid(row=2, column=0, sticky="ew", padx=2, pady=(0, 8))

        self.v_scroll = ctk.CTkScrollbar(
            table_container,
            orientation="vertical",
            command=self.table_canvas.yview,
            fg_color=COLOR_BG_PRIMARY,
            button_color=COLOR_BG_CARD,
            button_hover_color=COLOR_BORDER
        )
        self.v_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 2))
        self.table_canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        # Frame interno dentro del canvas (contenido desplazable)
        self.content_frame = ctk.CTkFrame(self.table_canvas, fg_color="transparent")
        self.canvas_window = self.table_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        try:
            for c in range(9):
                self.content_frame.grid_columnconfigure(c, weight=0)
            self.content_frame.grid_columnconfigure(8, weight=1)
        except Exception:
            pass

        # Cabeceras dentro del contenido (se desplazan junto con filas)
        headers_frame = ctk.CTkFrame(self.content_frame, fg_color="#181A20", corner_radius=0)
        headers_frame.grid(row=0, column=0, columnspan=9, sticky="ew")
        headers = ["Time", "Pair", "Signal", "Price", "SL", "TP", "Result", "Mode", "Status"]
        widths = [150, 100, 80, 100, 100, 100, 90, 80, 120]
        for i, (header, width) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(headers_frame, text=header.upper(), font=(FONT_FAMILY, 11, "bold"), text_color=COLOR_TEXT_MUTED, width=width, anchor="w")
            lbl.grid(row=0, column=i, padx=15, pady=12, sticky="w")

        # Mantener scrollregion sincronizada cuando cambia el tamaño
        def _update_scrollregion(event=None):
            try:
                self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))
                # Keep content aligned to left when resized
                self.table_canvas.itemconfigure(self.canvas_window, width=max(self.content_frame.winfo_reqwidth(), self.table_canvas.winfo_width()))
            except Exception:
                pass
        self.content_frame.bind("<Configure>", _update_scrollregion)
        self.table_canvas.bind("<Configure>", _update_scrollregion)
        
        # Load initial data
        self.load_history()
        # Start auto-refresh
        self.start_auto_refresh()
    
    def load_history(self):
        """Carga historial desde JSON y renderiza filas en la tabla."""
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") == "#181A20":
                # keep headers_frame
                continue
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

            # Actualizar scrollregion del canvas tras crear filas
            try:
                self.content_frame.update_idletasks()
                self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))
            except Exception:
                pass
                
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
            result = signal.get("result", "-")
            mode = signal.get("mode", "SIM")
            
            signal_color = COLOR_ACCENT_BUY if signal_type == "BUY" else COLOR_ACCENT_SELL
            
            # Create row
            row_bg = "transparent" if idx % 2 == 0 else "#181A20"
            row_frame = ctk.CTkFrame(self.content_frame, fg_color=row_bg, corner_radius=0)
            row_frame.grid(row=idx+1, column=0, sticky="ew")
            
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

            # Result badge
            res_color = COLOR_ACCENT_BUY if result.upper() == "WIN" else COLOR_ACCENT_SELL if result.upper() == "LOSS" else COLOR_TEXT_SECONDARY
            res_bg = "#142620" if result.upper() == "WIN" else "#2D191E" if result.upper() == "LOSS" else "#2B3139"
            res_lbl = ctk.CTkLabel(row_frame, text=result.upper(), font=(FONT_FAMILY, 10, "bold"), text_color=res_color, width=70, fg_color=res_bg, corner_radius=4)
            res_lbl.grid(row=0, column=6, padx=15, pady=8, sticky="w")

            mode_lbl = ctk.CTkLabel(row_frame, text=mode.upper(), font=(FONT_FAMILY, 10, "bold"), text_color=COLOR_TEXT_SECONDARY, width=60, fg_color="#2B3139", corner_radius=4)
            mode_lbl.grid(row=0, column=7, padx=15, pady=8, sticky="w")

            ctk.CTkLabel(row_frame, text=status.capitalize(), font=(FONT_FAMILY, 11), text_color=signal_color, width=100, anchor="w").grid(row=0, column=8, padx=15, pady=8, sticky="w")
            
        except Exception as e:
            pass
    
    def export_history(self):
        """Exporta historial a CSV usando cuadro de diálogo."""
        try:
            # Nombre de archivo por defecto
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"trading_history_{timestamp}.csv"
            
            # Diálogo Guardar como...
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_name,
                title="Export Trading History"
            )
            
            if not file_path:
                return # Usuario canceló

            # Exportar vía DataManager
            self.bot.data_manager.export_to_csv(file_path)
            
            # Feedback visual de exportación
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

    def start_auto_refresh(self):
        """Activa auto-refresh periódico de la vista de historial."""
        if self._auto_refresh_id is None:
            self._schedule_next_refresh()

    def stop_auto_refresh(self):
        """Detiene el auto-refresh periódico."""
        if self._auto_refresh_id is not None:
            try:
                self.after_cancel(self._auto_refresh_id)
            except Exception:
                pass
            self._auto_refresh_id = None

    def _schedule_next_refresh(self):
        try:
            self._auto_refresh_id = self.after(self._auto_refresh_ms, self._auto_refresh_tick)
        except Exception:
            self._auto_refresh_id = None

    def _auto_refresh_tick(self):
        try:
            # Refresh only when view is visible/mapped
            if self.winfo_ismapped():
                self.load_history()
            self._schedule_next_refresh()
        except Exception:
            self._schedule_next_refresh()
