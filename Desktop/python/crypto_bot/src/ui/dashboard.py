import customtkinter as ctk
from .styles import *
from ..config import PAIRS
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as mticker
import mplfinance as mpf
import pandas as pd

class DashboardView(ctk.CTkFrame):
    # Vista principal: estadísticas, overview y gráfica.
    def __init__(self, master, bot):
        super().__init__(master, fg_color=COLOR_BG_PRIMARY)
        self.bot = bot
        self.current_pair = "BTCUSDT"  # Par actual mostrado en la gráfica
        
        # === Grid ===
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.grid_rowconfigure(1, weight=1)  # Fila: overview + log
        self.grid_rowconfigure(2, weight=2)  # Fila: gráfica
        
        # === Stats Cards ===
        # Tarjetas superiores: capital, PNL total, win rate y ticker.
        stats_container = ctk.CTkFrame(self, fg_color="transparent")
        stats_container.grid(row=0, column=0, columnspan=4, sticky="ew", padx=20, pady=(16, 8))
        stats_container.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Capital card
        self.card_capital = self._create_card(stats_container, 0, "TOTAL CAPITAL", "25.00 USDT", "💰", self.edit_capital)
        
        # PNL card (with manual recompute button)
        self.card_pnl = self._create_card(stats_container, 1, "TOTAL PNL", "+0.00 USDT", "📈", self.recompute_stats)
        
        # Win rate card
        self.card_winrate = self._create_card(stats_container, 2, "WIN RATE", "0% (0/0)", "🎯", self.reset_stats)

        # Price ticker card
        self.card_price = self._create_card(stats_container, 3, "LIVE PRICE", "--.-- USDT", "⚡", None, COLOR_ACCENT_BUY)

        # === Market Overview Panel (left) ===
        # Resumen de pares con precio/cambio/RSI y señal.
        from .market_overview import MarketOverview
        self.market_overview = MarketOverview(self, self.bot, self.switch_pair)
        self.market_overview.grid(row=1, column=0, columnspan=3, padx=20, pady=10, sticky="nsew")

        # === Activity Log (right) ===
        # Consola de eventos y señales.
        self.log_frame = ctk.CTkFrame(self, fg_color=COLOR_BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=COLOR_BORDER)
        self.log_frame.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")

        log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(log_header, text="ACTIVITY LOG", font=(FONT_FAMILY, 12, "bold"), text_color=COLOR_TEXT_MUTED).pack(side="left")

        self.log_box = ctk.CTkTextbox(
            self.log_frame, 
            font=("Consolas", 12), 
            text_color=COLOR_TEXT_PRIMARY, 
            fg_color=COLOR_BG_PRIMARY,
            border_width=0,
            corner_radius=6
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # === Chart Section (full width) ===
        # Gráfica de velas embebida con mplfinance.
        self.chart_frame = ctk.CTkFrame(self, fg_color=COLOR_BG_SECONDARY, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=COLOR_BORDER)
        self.chart_frame.grid(row=2, column=0, columnspan=4, padx=20, pady=(4, 16), sticky="nsew")
        
        header_frame = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=10)
        # Referencia para no destruir este encabezado al refrescar la gráfica
        self.header_frame = header_frame
        
        self.chart_label = ctk.CTkLabel(header_frame, text=f"MARKET OVERVIEW ({self.current_pair})", font=(FONT_FAMILY, 14, "bold"), text_color=COLOR_TEXT_SECONDARY)
        self.chart_label.pack(side="left")

        # Selector de par (dropdown)
        self.pair_var = ctk.StringVar(value=self.current_pair)
        self.pair_selector = ctk.CTkOptionMenu(
            header_frame,
            values=PAIRS,
            variable=self.pair_var,
            command=self.switch_pair,
            fg_color=COLOR_BG_PRIMARY,
            button_color=COLOR_BG_SECONDARY,
            button_hover_color="#2B3139",
            text_color=COLOR_TEXT_PRIMARY,
            font=(FONT_FAMILY, 12)
        )
        self.pair_selector.pack(side="right")
        
        # Placeholder para la gráfica
        self.canvas = None
        
        # === Hooks ===
        # Conexiones thread-safe hacia la UI.
        self.bot.log_callback = self.update_log_safe
        self.bot.stats_callback = self.update_stats_safe
        self.bot.notification_callback = self.show_notification_safe
        
        # Carga inicial de gráfica después de 1s
        self.after(1000, self.update_chart)
        # Inicia ticker de precio
        self.after(2000, self.update_ticker)


    def _create_card(self, parent, col, title, value, icon, command=None, value_color=COLOR_TEXT_PRIMARY):
        frame = ctk.CTkFrame(parent, fg_color=COLOR_BG_CARD, corner_radius=CARD_CORNER_RADIUS, border_width=1, border_color=COLOR_BORDER)
        frame.grid(row=0, column=col, padx=10, pady=10, sticky="ew")
        
        # Encabezado con icono y título
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 0))
        
        icon_lbl = ctk.CTkLabel(header, text=icon, font=(FONT_FAMILY, 16))
        icon_lbl.pack(side="left", padx=(0, 5))
        
        title_lbl = ctk.CTkLabel(header, text=title, font=(FONT_FAMILY, 11, "bold"), text_color=COLOR_TEXT_SECONDARY)
        title_lbl.pack(side="left")
        
        if command:
            btn = ctk.CTkButton(
                header, 
                text="⚙️" if "CAPITAL" in title else "🔄", 
                command=command,
                width=24, height=24,
                fg_color="transparent",
                hover_color=COLOR_BG_SECONDARY,
                text_color=COLOR_TEXT_MUTED,
                font=(FONT_FAMILY, 12)
            )
            btn.pack(side="right")
        
        # Valor principal de la tarjeta
        val_lbl = ctk.CTkLabel(frame, text=value, font=(FONT_FAMILY, 22, "bold"), text_color=value_color)
        val_lbl.pack(padx=12, pady=(4, 12), anchor="w")
        
        return val_lbl

    def log(self, message):
        self.update_log_safe(message)

    def update_log_safe(self, message):
        # Asegura actualización en hilo principal de Tk.
        # Las llamadas deben ser seguras de hilo para Tkinter
        self.after(0, lambda: self._log_impl(message))

    def _log_impl(self, message):
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")

    def update_stats_safe(self, stats):
        # Actualiza tarjetas de forma segura desde callbacks del bot.
        self.after(0, lambda: self._stats_impl(stats))

    def _stats_impl(self, stats):
        self.card_capital.configure(text=f"{stats['capital_actual']:.2f} USDT")
        
        pnl = stats['pnl']
        sign = "+" if pnl >= 0 else ""
        color = COLOR_ACCENT_BUY if pnl >= 0 else COLOR_ACCENT_SELL
        self.card_pnl.configure(text=f"{sign}{pnl:.2f} USDT", text_color=color)
        
        wins = stats['win_count']
        losses = stats['loss_count']
        total = wins + losses
        rate = (wins / total * 100) if total > 0 else 0
        self.card_winrate.configure(text=f"{rate:.1f}% ({wins}/{total})")

    def switch_pair(self, pair):
        """Cambia el par principal y refresca overview/charteo."""
        self.current_pair = pair
        self.chart_label.configure(text=f"MARKET OVERVIEW ({pair})")
        self.update_chart()
        # Refresh market overview immediately to reflect the new focus
        try:
            self.market_overview.update_market_data()
            self.market_overview.set_active_pair(pair)
        except Exception:
            pass
        self.log(f"📊 Switched to {pair}")

    def show_notification_safe(self, signal_data):
        """Thread-safe notification trigger"""
        self.after(0, lambda: self._show_notification(signal_data))

    def _show_notification(self, signal_data):
        """Display signal notification popup"""
        from .notification import SignalNotification
        SignalNotification(
            self.winfo_toplevel(),
            signal_data['type'],
            signal_data['pair'],
            signal_data['price'],
            signal_data['sl'],
            signal_data['tp']
        )

        # Opción de refrescar gráfica aquí si es necesario.
        # Se puede actualizar con cada cambio de stats o con temporizador.
        # Por ahora solo se dispara una vez o bajo demanda.
        pass

    def update_chart(self):
        # Programar próximo refresco en 60 segundos
        if not self.winfo_exists():
            return
            
        self.after(60000, self.update_chart)

        try:
            df = self.bot.get_chart_data(self.current_pair)
            
            # Limpiar área de gráfica manteniendo el encabezado (label + dropdown)
            for widget in self.chart_frame.winfo_children():
                if widget != self.header_frame:
                    widget.destroy()

            if df is None or df.empty: 
                error_label = ctk.CTkLabel(self.chart_frame, text="⚠️ No Data Available (Check Internet/API)", text_color=COLOR_ACCENT_SELL)
                error_label.pack(expand=True)
                return

            # === Premium Chart Style ===
            # Estilo oscuro y legible, coherente con el resto de la UI.
            mc = mpf.make_marketcolors(
                up=COLOR_ACCENT_BUY, 
                down=COLOR_ACCENT_SELL,
                edge='inherit',
                wick='inherit',
                volume={'up': COLOR_ACCENT_BUY, 'down': COLOR_ACCENT_SELL},
                alpha=0.8
            )
            
            s = mpf.make_mpf_style(
                base_mpf_style='nightclouds', 
                marketcolors=mc,
                facecolor=COLOR_BG_SECONDARY,
                gridcolor='#2B3139',
                gridstyle='dotted',
                edgecolor=COLOR_BG_SECONDARY,
                figcolor=COLOR_BG_SECONDARY,
                rc={
                    'font.size': 8,
                    'axes.titlesize': 10,
                    'axes.labelsize': 8,
                    'xtick.labelsize': 8,
                    'ytick.labelsize': 8,
                    'lines.linewidth': 1,
                }
            )

            # Crear figura y ejes
            fig, ax = mpf.plot(
                df,
                type="candle",
                style=s,
                volume=True,
                title="",
                returnfig=True,
                figsize=(10, 5),
                tight_layout=False,
                datetime_format='%H:%M',
                xrotation=0,
                show_nontrading=False
            )
            # Garantizar etiquetas visibles con márgenes cómodos
            try:
                fig.subplots_adjust(left=0.08, right=0.98, bottom=0.18, top=0.96, hspace=0.10)
            except Exception:
                pass
            
            # Ajustes finos de ejes de precio y volumen
            # ax[0]: precio, ax[2]: volumen
            ax[0].set_ylabel("Price (USDT)", color=COLOR_TEXT_PRIMARY, labelpad=12, fontsize=11)
            ax[0].yaxis.set_label_position("right")
            ax[0].yaxis.tick_right()
            
            # Decimales dinámicos en eje de precio para mejor legibilidad
            try:
                last_price = float(df['close'].iloc[-1])
            except Exception:
                last_price = 0.0
            decimals = 0 if last_price >= 1000 else (2 if last_price >= 1 else 4)
            ax[0].yaxis.set_major_formatter(mticker.StrMethodFormatter(f'{{x:,.{decimals}f}}'))
            ax[0].yaxis.set_major_locator(mticker.MaxNLocator(nbins=6, prune='both'))
            
            # Eje de volumen
            if len(ax) > 2:
                ax[2].set_ylabel("Vol", color=COLOR_TEXT_PRIMARY, fontsize=9)
                ax[2].yaxis.set_major_formatter(mticker.StrMethodFormatter('{x:,.0f}'))
                ax[2].yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, prune='both'))
            
            # Personalización general de ejes y rejilla
            for a in ax:
                a.tick_params(axis='x', colors=COLOR_TEXT_PRIMARY, labelsize=11, pad=8)
                a.tick_params(axis='y', colors=COLOR_TEXT_PRIMARY, labelsize=11, pad=8)
                a.spines['top'].set_visible(False)
                a.spines['right'].set_visible(False)
                a.spines['left'].set_visible(False)
                a.spines['bottom'].set_color(COLOR_BORDER)
                a.grid(alpha=0.12, linestyle=':')

            # Integrar figura en Tkinter
            self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            self.canvas.draw()
            canvas_widget = self.canvas.get_tk_widget()
            canvas_widget.configure(bg=COLOR_BG_SECONDARY)
            canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
            
        except Exception as e:
            self.log(f"❌ Chart Error: {e}")
            # Mostrar error en área de gráfica
            err = ctk.CTkLabel(self.chart_frame, text=f"Chart Error: {str(e)}", text_color=COLOR_ACCENT_SELL)
            err.pack(expand=True)
    
    def edit_capital(self):
        """Show dialog to edit initial capital"""
        dialog = ctk.CTkInputDialog(
            text="Enter new initial capital (USDT):",
            title="Edit Capital"
        )
        new_value = dialog.get_input()
        
        if new_value is not None and str(new_value).strip():
            try:
                # Clean the input - remove spaces and handle comma as decimal separator
                cleaned_value = str(new_value).strip().replace(',', '.')
                new_capital = float(cleaned_value)
                
                if new_capital > 0:
                    self.bot.update_initial_capital(new_capital)
                else:
                    self.log("❌ Capital must be positive")
            except (ValueError, AttributeError, TypeError) as e:
                self.log(f"❌ Invalid capital value. Please enter a valid number.")
    
    def reset_stats(self):
        """Reset statistics with confirmation"""
        # Confirmación simple mediante diálogo
        dialog = ctk.CTkInputDialog(
            text="Type 'RESET' to confirm resetting statistics:",
            title="Reset Statistics"
        )
        confirmation = dialog.get_input()
        
        if confirmation and confirmation.upper() == "RESET":
            self.bot.reset_statistics()
        else:
            self.log("❌ Reset cancelled")

    def update_ticker(self):
        """Update the live price ticker every 15 seconds"""
        if not self.winfo_exists():
            return
        try:
            price = self.bot.get_current_price(self.current_pair)
            if price:
                self.card_price.configure(text=f"{price:,.2f} USDT")
        except Exception as e:
            pass
            
        # Programar próximo update (rápido: 2 segundos)
        self.after(2000, self.update_ticker)

    def recompute_stats(self):
        """Trigger bot stats recompute from dashboard button"""
        try:
            self.bot.recompute_stats()
        except Exception as e:
            self.log(f"❌ Error al recalcular estadísticas: {e}")



