import sys
import os

# Add local directory to path to allow imports if running from top level
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.bot import TradingBot
from src.ui.main_window import MainWindow

def main():
    bot = TradingBot()
    app = MainWindow(bot)
    app.mainloop()
    
    # Ensure bot stops when window closes
    bot.stop()

if __name__ == "__main__":
    main()
