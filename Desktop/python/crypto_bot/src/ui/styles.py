import customtkinter as ctk

# === Paleta de colores (estilo Binance) ===
COLOR_BG_PRIMARY = "#0B0E11"      # Fondo ultra oscuro
COLOR_BG_SECONDARY = "#1E2329"    # Tarjetas / Sidebar
COLOR_BG_CARD = "#181A20"         # Fondo específico de card

COLOR_TEXT_PRIMARY = "#EAECEF"    # Blanco / Gris claro
COLOR_TEXT_SECONDARY = "#848E9C"  # Etiquetas grises
COLOR_TEXT_MUTED = "#707A8A"      # Texto más atenuado

COLOR_ACCENT_BUY = "#0ECB81"      # Verde Binance
COLOR_ACCENT_HOVER_BUY = "#0BA366"

COLOR_ACCENT_SELL = "#F6465D"     # Rojo Binance
COLOR_ACCENT_HOVER_SELL = "#CF3D50"

COLOR_ACCENT_MAIN = "#FCD535"     # Amarillo Binance
COLOR_ACCENT_MAIN_HOVER = "#D9B221"

COLOR_BORDER = "#2B3139"          # Bordes sutiles
COLOR_DIVIDER = "#2B3139"

# === Constantes de estilo ===
CARD_CORNER_RADIUS = 12
BUTTON_CORNER_RADIUS = 8
INPUT_CORNER_RADIUS = 6

# === Fuentes ===
FONT_FAMILY = "Segoe UI"  # Fuente moderna de Windows
FONT_WEIGHT_BOLD = "bold"
FONT_WEIGHT_MEDIUM = "normal" # Default weight

def apply_theme():
    # Tema oscuro consistente para toda la app
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
