import customtkinter as ctk
from .styles import *
from .dashboard import DashboardView
# from .history import HistoryView # Implement later

class MainWindow(ctk.CTk):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        self.title("Antigravity - Crypto Intelligence")
        self.geometry("1400x900")
        apply_theme()
        
        # Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # === Sidebar ===
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLOR_BG_SECONDARY)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        # Header / Logo
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        self.logo_label = ctk.CTkLabel(
            self.logo_frame, 
            text="⚡ CRYPTO BOT", 
            font=(FONT_FAMILY, 24, "bold"), 
            text_color=COLOR_ACCENT_MAIN
        )
        self.logo_label.pack()
        
        self.status_pill = ctk.CTkLabel(
            self.logo_frame, 
            text="OFFLINE", 
            font=(FONT_FAMILY, 10, "bold"),
            fg_color="#363C44",
            corner_radius=10,
            padx=10,
            text_color=COLOR_TEXT_SECONDARY
        )
        self.status_pill.pack(pady=5)
        
        # Navigation
        self.btn_dashboard = self._create_nav_btn("📊 Dashboard", self.show_dashboard, 1)
        self.btn_history = self._create_nav_btn("📜 History", self.show_history, 2)
        # self.btn_settings = self._create_nav_btn("⚙️ Settings", self.show_settings, 3)

        # Control Section
        control_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        control_frame.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
        
        self.btn_start = ctk.CTkButton(
            control_frame, 
            text="START BOT", 
            command=self.start_bot_wrapper, 
            fg_color=COLOR_ACCENT_BUY, 
            hover_color=COLOR_ACCENT_HOVER_BUY, 
            text_color="white", 
            font=(FONT_FAMILY, 13, "bold"),
            height=40,
            corner_radius=BUTTON_CORNER_RADIUS
        )
        self.btn_start.pack(fill="x", pady=5)

        self.btn_stop = ctk.CTkButton(
            control_frame, 
            text="STOP BOT", 
            command=self.stop_bot_wrapper, 
            fg_color="#2B3139", # Neutral dark for stop
            hover_color=COLOR_ACCENT_HOVER_SELL, 
            text_color=COLOR_TEXT_SECONDARY, 
            font=(FONT_FAMILY, 13, "bold"),
            height=40,
            corner_radius=BUTTON_CORNER_RADIUS
        )
        self.btn_stop.pack(fill="x", pady=5)
        
        # === Content Area ===
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_BG_PRIMARY)
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        # Views
        self.dashboard_view = DashboardView(self.content_area, self.bot)
        from .history import HistoryView
        self.history_view = HistoryView(self.content_area, self.bot)
        
        self.show_dashboard()

        # Auto-start logic
        saved_state = self.bot.data_manager.load_bot_state()
        if saved_state.get("is_running", False):
            self.after(2000, self.start_bot_wrapper)

    def _create_nav_btn(self, text, command, row):
        btn = ctk.CTkButton(
            self.sidebar, 
            text=text, 
            command=command, 
            fg_color="transparent", 
            text_color=COLOR_TEXT_SECONDARY, 
            hover_color="#2B3139", 
            anchor="w", 
            height=45, 
            font=(FONT_FAMILY, 15),
            corner_radius=6
        )
        btn.grid(row=row, column=0, padx=15, pady=2, sticky="ew")
        return btn

    def show_dashboard(self):
        self._select_btn(self.btn_dashboard)
        self.history_view.grid_forget()
        self.dashboard_view.grid(row=0, column=0, sticky="nsew")

    def show_history(self):
        self._select_btn(self.btn_history)
        self.dashboard_view.grid_forget()
        self.history_view.grid(row=0, column=0, sticky="nsew")
        self.history_view.load_history()

    def _select_btn(self, active_btn):
        for btn in [self.btn_dashboard, self.btn_history]:
            btn.configure(fg_color="transparent", text_color=COLOR_TEXT_SECONDARY)
        active_btn.configure(fg_color="#2B3139", text_color=COLOR_ACCENT_MAIN)

    def start_bot_wrapper(self):
        self.bot.start()
        self.status_pill.configure(text="● RUNNING", text_color=COLOR_ACCENT_BUY, fg_color="#142620")
        self.dashboard_view.log("▶ Command: Start Bot")

    def stop_bot_wrapper(self):
        self.bot.stop()
        self.status_pill.configure(text="OFFLINE", text_color=COLOR_TEXT_SECONDARY, fg_color="#363C44")
        self.dashboard_view.log("⏹ Command: Stop Bot")
