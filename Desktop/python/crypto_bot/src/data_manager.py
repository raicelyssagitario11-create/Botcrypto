import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import csv

class DataManager:
    """Manages local data persistence for the trading bot using JSON files"""
    
    def __init__(self, data_dir: str = "data"):
        # Use absolute path relative to this file's location (src/data_manager.py)
        # to ensure it always finds the data folder inside the project
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(base_dir, data_dir)
        self.data_file = os.path.join(self.data_dir, "bot_data.json")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize data structure
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load data from JSON file or create default structure"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading data file: {e}. Creating new data structure.")
                return self._create_default_data()
        else:
            return self._create_default_data()
    
    def _create_default_data(self) -> Dict:
        """Create default data structure"""
        return {
            "bot_state": {
                "capital_initial": 25.0,
                "capital_actual": 25.0,
                "profit_loss_total": 0.0,
                "buy_count": 0,
                "sell_count": 0,
                "win_count": 0,
                "loss_count": 0,
                "last_signal": "Ninguna",
                "is_running": False,
                "last_updated": datetime.now().isoformat()
            },
            "trading_history": []
        }
    
    def _save_data(self):
        """Save data to JSON file"""
        try:
            self.data["bot_state"]["last_updated"] = datetime.now().isoformat()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    # === Bot State Management ===
    
    def load_bot_state(self) -> Dict:
        """Load bot state (capital, statistics)"""
        return self.data["bot_state"].copy()
    
    def save_bot_state(self, state: Dict):
        """Save bot state"""
        self.data["bot_state"].update(state)
        self._save_data()
    
    def update_capital(self, initial: float, actual: float, pnl: float):
        """Update capital values"""
        self.data["bot_state"]["capital_initial"] = initial
        self.data["bot_state"]["capital_actual"] = actual
        self.data["bot_state"]["profit_loss_total"] = pnl
        self._save_data()
    
    def update_statistics(self, buy_count: int, sell_count: int, 
                         win_count: int, loss_count: int, last_signal: str):
        """Update trading statistics"""
        self.data["bot_state"]["buy_count"] = buy_count
        self.data["bot_state"]["sell_count"] = sell_count
        self.data["bot_state"]["win_count"] = win_count
        self.data["bot_state"]["loss_count"] = loss_count
        self.data["bot_state"]["last_signal"] = last_signal
        self._save_data()
    
    def set_running_state(self, is_running: bool):
        """Save whether the bot is running or not"""
        self.data["bot_state"]["is_running"] = is_running
        self._save_data()
    
    def reset_statistics(self):
        """Reset statistics while keeping history"""
        current_capital = self.data["bot_state"]["capital_actual"]
        self.data["bot_state"].update({
            "capital_initial": current_capital,
            "capital_actual": current_capital,
            "profit_loss_total": 0.0,
            "buy_count": 0,
            "sell_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "last_signal": "Ninguna"
        })
        self._save_data()
    
    # === Trading History Management ===
    
    def load_trading_history(self) -> List[Dict]:
        """Load trading history"""
        history = self.data["trading_history"].copy()

        # Backfill missing fields (result/mode) for older entries
        changed = False
        for entry in history:
            if not entry.get("result"):
                pnl_val = entry.get("pnl", 0.0)
                entry["result"] = "WIN" if pnl_val > 0 else ("LOSS" if pnl_val < 0 else "FLAT")
                changed = True
            if not entry.get("mode"):
                entry["mode"] = "SIM"
                changed = True

        if changed:
            # Persist normalized history
            self.data["trading_history"] = history
            self._save_data()

        return history
    
    def save_signal(self, signal_data: Dict):
        """Save a new trading signal to history"""
        pnl_val = signal_data.get("pnl", 0.0)
        inferred_result = "WIN" if pnl_val > 0 else ("LOSS" if pnl_val < 0 else "FLAT")
        signal_entry = {
            "timestamp": signal_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "signal_type": signal_data["signal_type"],
            "pair": signal_data["pair"],
            "price": signal_data["price"],
            "stop_loss": signal_data["stop_loss"],
            "take_profit": signal_data["take_profit"],
            "capital_after": signal_data.get("capital_after", 0.0),
            "pnl": pnl_val,
            "mode": signal_data.get("mode", "SIM"),
            "result": signal_data.get("result", inferred_result),
            "status": signal_data.get("status", "completed")
        }
        
        self.data["trading_history"].append(signal_entry)
        self._save_data()
    
    def clear_history(self):
        """Clear all trading history"""
        self.data["trading_history"] = []
        self._save_data()
    
    # === Export Functions ===
    
    def export_to_csv(self, output_file: Optional[str] = None) -> str:
        """Export trading history to CSV file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"trading_history_export_{timestamp}.csv"
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if not self.data["trading_history"]:
                    # Empty history
                    f.write("No trading history available\n")
                    return output_file
                
                writer = csv.DictWriter(f, fieldnames=[
                    "timestamp", "signal_type", "pair", "price", 
                    "stop_loss", "take_profit", "capital_after", "pnl", "result", "mode", "status"
                ])
                writer.writeheader()
                writer.writerows(self.data["trading_history"])
            
            return output_file
        except Exception as e:
            raise Exception(f"Error exporting to CSV: {e}")

    # === Aggregations ===
    def get_history_summary(self) -> Dict:
        """Compute totals from trading_history for UI stats.
        Returns dict with keys: pnl_total, buy_count, sell_count, win_count, loss_count, last_signal.
        """
        history = self.data.get("trading_history", [])
        pnl_total = 0.0
        buy_count = 0
        sell_count = 0
        win_count = 0
        loss_count = 0
        last_signal = "Ninguna"

        for entry in history:
            try:
                pnl_total += float(entry.get("pnl", 0.0))
            except (TypeError, ValueError):
                pass
            st = str(entry.get("signal_type", ""))
            if st == "BUY":
                buy_count += 1
            elif st == "SELL":
                sell_count += 1
            res = str(entry.get("result", "")).upper()
            if res == "WIN":
                win_count += 1
            elif res == "LOSS":
                loss_count += 1
            last_signal = f"{st} {entry.get('pair', '')}" or last_signal

        return {
            "pnl_total": pnl_total,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "win_count": win_count,
            "loss_count": loss_count,
            "last_signal": last_signal,
        }
    
    # === Migration from old CSV format ===
    
    def migrate_from_csv(self, csv_file: str):
        """Migrate data from old CSV format to new JSON format"""
        if not os.path.exists(csv_file):
            return
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            import re
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse old format: "timestamp SIGNAL pair @ price (SL: x, TP: y) | Cap: z"
                parts = line.split("|")
                if len(parts) < 2:
                    continue
                
                signal_part = parts[0].strip()
                cap_part = parts[1].strip()
                
                # Extract timestamp
                time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', signal_part)
                timestamp = time_match.group(1) if time_match else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Extract signal type
                if "BUY" in signal_part:
                    signal_type = "BUY"
                elif "SELL" in signal_part:
                    signal_type = "SELL"
                else:
                    continue
                
                # Extract pair
                pair_match = re.search(r'(BTC|ETH|BNB)USDT', signal_part)
                pair = pair_match.group(0) if pair_match else "UNKNOWN"
                
                # Extract price, SL, TP
                price_match = re.search(r'@ ([\d.]+)', signal_part)
                sl_match = re.search(r'SL: ([\d.]+)', signal_part)
                tp_match = re.search(r'TP: ([\d.]+)', signal_part)
                
                price = float(price_match.group(1)) if price_match else 0.0
                sl = float(sl_match.group(1)) if sl_match else 0.0
                tp = float(tp_match.group(1)) if tp_match else 0.0
                
                # Extract capital
                cap_match = re.search(r'Cap: ([\d.]+)', cap_part)
                capital_after = float(cap_match.group(1)) if cap_match else 0.0
                
                # Create signal entry
                signal_data = {
                    "timestamp": timestamp,
                    "signal_type": signal_type,
                    "pair": pair,
                    "price": price,
                    "stop_loss": sl,
                    "take_profit": tp,
                    "capital_after": capital_after,
                    "pnl": 0.0,  # Can't calculate from old format
                    "status": "completed"
                }
                
                self.data["trading_history"].append(signal_data)
            
            self._save_data()
            print(f"Successfully migrated {len(self.data['trading_history'])} signals from CSV")
            
        except Exception as e:
            print(f"Error migrating from CSV: {e}")
