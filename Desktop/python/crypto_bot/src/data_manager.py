import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import csv

class DataManager:
    """Gestiona persistencia local (JSON) del bot: estado y historial."""
    
    def __init__(self, data_dir: str = "data"):
        # Usa ruta absoluta relativa a este archivo (src/data_manager.py)
        # para asegurar que siempre se ubique la carpeta de datos del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raíz del proyecto
        self.data_dir = os.path.join(base_dir, data_dir)
        self.data_file = os.path.join(self.data_dir, "bot_data.json")
        
        # Asegurar existencia de la carpeta de datos
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Inicializa estructura de datos en memoria
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Carga JSON o crea estructura por defecto si no existe."""
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
        """Estructura inicial: estado del bot + historial vacío."""
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
        """Lee estado del bot (capital y contadores)."""
        return self.data["bot_state"].copy()
    
    def save_bot_state(self, state: Dict):
        """Guarda estado del bot."""
        self.data["bot_state"].update(state)
        self._save_data()
    
    def update_capital(self, initial: float, actual: float, pnl: float):
        """Actualiza capital inicial/actual y PNL total."""
        self.data["bot_state"]["capital_initial"] = initial
        self.data["bot_state"]["capital_actual"] = actual
        self.data["bot_state"]["profit_loss_total"] = pnl
        self._save_data()
    
    def update_statistics(self, buy_count: int, sell_count: int, 
                         win_count: int, loss_count: int, last_signal: str):
        """Actualiza contadores y última señal."""
        self.data["bot_state"]["buy_count"] = buy_count
        self.data["bot_state"]["sell_count"] = sell_count
        self.data["bot_state"]["win_count"] = win_count
        self.data["bot_state"]["loss_count"] = loss_count
        self.data["bot_state"]["last_signal"] = last_signal
        self._save_data()
    
    def set_running_state(self, is_running: bool):
        """Marca si el bot está corriendo (para auto-start)."""
        self.data["bot_state"]["is_running"] = is_running
        self._save_data()
    
    def reset_statistics(self):
        """Resetea estadísticas manteniendo historial (capital se conserva)."""
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
        """Lee historial y normaliza campos faltantes (result/mode)."""
        history = self.data["trading_history"].copy()

        # Relleno de campos faltantes (result/mode) para entradas antiguas
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
            # Persistir historial normalizado
            self.data["trading_history"] = history
            self._save_data()

        return history
    
    def save_signal(self, signal_data: Dict):
        """Guarda una nueva señal en el historial (JSON)."""
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
        """Exporta historial a CSV (para análisis externo)."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"trading_history_export_{timestamp}.csv"
        
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if not self.data["trading_history"]:
                    # Historial vacío
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
        """Agrega PNL y contadores para las tarjetas de la UI.
        Devuelve: pnl_total, buy_count, sell_count, win_count, loss_count, last_signal.
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
        """Migra CSV legado al formato JSON moderno (mejor trazabilidad)."""
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
                
                # Parseo del formato antiguo: "timestamp SIGNAL pair @ price (SL: x, TP: y) | Cap: z"
                parts = line.split("|")
                if len(parts) < 2:
                    continue
                
                signal_part = parts[0].strip()
                cap_part = parts[1].strip()
                
                # Extraer timestamp
                time_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', signal_part)
                timestamp = time_match.group(1) if time_match else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Extraer tipo de señal
                if "BUY" in signal_part:
                    signal_type = "BUY"
                elif "SELL" in signal_part:
                    signal_type = "SELL"
                else:
                    continue
                
                # Extraer par
                pair_match = re.search(r'(BTC|ETH|BNB)USDT', signal_part)
                pair = pair_match.group(0) if pair_match else "UNKNOWN"
                
                # Extraer precio, SL y TP
                price_match = re.search(r'@ ([\d.]+)', signal_part)
                sl_match = re.search(r'SL: ([\d.]+)', signal_part)
                tp_match = re.search(r'TP: ([\d.]+)', signal_part)
                
                price = float(price_match.group(1)) if price_match else 0.0
                sl = float(sl_match.group(1)) if sl_match else 0.0
                tp = float(tp_match.group(1)) if tp_match else 0.0
                
                # Extraer capital
                cap_match = re.search(r'Cap: ([\d.]+)', cap_part)
                capital_after = float(cap_match.group(1)) if cap_match else 0.0
                
                # Crear entrada de señal
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
            print(f"Migración exitosa de {len(self.data['trading_history'])} señales desde CSV")
            
        except Exception as e:
            print(f"Error migrating from CSV: {e}")
