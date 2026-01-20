import customtkinter as ctk

# === Paleta de colores (estilo Binance) ===
COLOR_BG_PRIMARY = "#0B0E11"      # Ultra Dark Background
COLOR_BG_SECONDARY = "#1E2329"    # Cards / Sidebar
COLOR_BG_CARD = "#181A20"         # Specific Card BG

COLOR_TEXT_PRIMARY = "#EAECEF"    # White / Light Grey
COLOR_TEXT_SECONDARY = "#848E9C"  # Grey labels
COLOR_TEXT_MUTED = "#707A8A"      # More muted text

COLOR_ACCENT_BUY = "#0ECB81"      # Binance Green
COLOR_ACCENT_HOVER_BUY = "#0BA366"

COLOR_ACCENT_SELL = "#F6465D"     # Binance Red
COLOR_ACCENT_HOVER_SELL = "#CF3D50"

COLOR_ACCENT_MAIN = "#FCD535"     # Binance Yellow
COLOR_ACCENT_MAIN_HOVER = "#D9B221"

COLOR_BORDER = "#2B3139"          # Subtle Borders
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
