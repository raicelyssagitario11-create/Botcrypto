import customtkinter as ctk
from .styles import *
import winsound
import threading

class SignalNotification(ctk.CTkToplevel):
    """Popup de notificación para señales (con sonido y autocierre)."""
    def __init__(self, parent, signal_type, pair, price, sl, tp):
        super().__init__(parent)
        
        self.signal_type = signal_type  # "BUY" or "SELL"
        self.pair = pair
        self.price = price
        self.sl = sl
        self.tp = tp
        
        # Configuración de ventana
        self.title("Trading Signal")
        self.geometry("400x250")
        self.resizable(False, False)
        
        # Siempre encima de otras ventanas
        self.attributes('-topmost', True)
        
        # Posicionar centrado respecto al padre
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 125
        self.geometry(f"+{x}+{y}")
        
        # Colores según tipo de señal
        if signal_type == "BUY":
            bg_color = COLOR_ACCENT_BUY
            icon = "📈"
        else:
            bg_color = COLOR_ACCENT_SELL
            icon = "📉"
        
        # Frame principal
        self.configure(fg_color=COLOR_BG_SECONDARY)
        
        # Encabezado
        header_frame = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        header_label = ctk.CTkLabel(
            header_frame, 
            text=f"{icon} {signal_type} SIGNAL", 
            font=(FONT_FAMILY, 24, "bold"),
            text_color="white"
        )
        header_label.pack(pady=15)
        
        # Contenido
        content_frame = ctk.CTkFrame(self, fg_color=COLOR_BG_SECONDARY)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Par
        pair_label = ctk.CTkLabel(
            content_frame,
            text=f"Pair: {pair}",
            font=(FONT_FAMILY, 18, "bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        pair_label.pack(pady=5)
        
        # Precio
        price_label = ctk.CTkLabel(
            content_frame,
            text=f"Entry: ${price:.2f}",
            font=(FONT_FAMILY, 14),
            text_color=COLOR_TEXT_PRIMARY
        )
        price_label.pack(pady=2)
        
        # SL/TP
        sl_tp_label = ctk.CTkLabel(
            content_frame,
            text=f"SL: ${sl:.2f} | TP: ${tp:.2f}",
            font=(FONT_FAMILY, 12),
            text_color=COLOR_TEXT_SECONDARY
        )
        sl_tp_label.pack(pady=2)
        
        # Botón cerrar
        close_btn = ctk.CTkButton(
            content_frame,
            text="OK",
            command=self.destroy,
            fg_color=bg_color,
            hover_color=COLOR_BG_PRIMARY,
            width=100
        )
        close_btn.pack(pady=15)
        
        # Autocierre a los 8 segundos
        self.after(8000, self.destroy)
        
        # Reproducir sonido en hilo de fondo
        threading.Thread(target=self._play_sound, daemon=True).start()
    
    def _play_sound(self):
        """Reproduce beep del sistema (Windows)."""
        try:
            # Windows beep: frequency, duration
            winsound.Beep(1000, 300)  # 1000Hz for 300ms
        except:
            pass  # Ignorar si el sonido falla
