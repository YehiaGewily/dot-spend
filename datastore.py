from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import json
import sqlite3
import datetime
import uuid
from pathlib import Path
from config import get_data_path, get_budget_path, get_db_path

class DataStore(ABC):
    @abstractmethod
    def add_expense(self, amount: float, category: str, note: str, timestamp: str, expense_id: str = None) -> Dict:
        pass

    @abstractmethod
    def get_expenses(self, filters: Dict = None) -> List[Dict]:
        pass

    @abstractmethod
    def get_expense(self, expense_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def update_expense(self, expense_id: str, updates: Dict) -> bool:
        pass

    @abstractmethod
    def delete_expense(self, expense_id: str) -> bool:
        pass

    @abstractmethod
    def load_budgets(self) -> Dict:
        pass

    @abstractmethod
    def save_budgets(self, budgets: Dict):
        pass

    @abstractmethod
    def clear_all_expenses(self):
        pass

class JSONDataStore(DataStore):
    def __init__(self):
        self.data_path = get_data_path()
        self.budget_path = get_budget_path()

    def _load_data(self) -> List[Dict]:
        if not self.data_path.exists():
            return []
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_data(self, data: List[Dict]):
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def add_expense(self, amount: float, category: str, note: str, timestamp: str, expense_id: str = None) -> Dict:
        data = self._load_data()
        if not expense_id:
            expense_id = str(uuid.uuid4())[:8]
            
        entry = {
            "id": expense_id,
            "date": datetime.datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M"),
            "timestamp": timestamp,
            "amount": amount,
            "category": category.upper(),
            "note": note
        }
        data.append(entry)
        self._save_data(data)
        return entry

    def get_expenses(self, filters: Dict = None) -> List[Dict]:
        data = self._load_data()
        # Filters can be applied here or by the caller. For now, we return all and let caller filter.
        # But for SQL optimization, we'd want filters down here.
        # Implemented for SQLite later.
        return data

    def get_expense(self, expense_id: str) -> Optional[Dict]:
        data = self._load_data()
        for item in data:
            if item['id'] == expense_id:
                return item
        return None

    def update_expense(self, expense_id: str, updates: Dict) -> bool:
        data = self._load_data()
        for i, item in enumerate(data):
            if item['id'] == expense_id:
                data[i].update(updates)
                self._save_data(data)
                return True
        return False

    def delete_expense(self, expense_id: str) -> bool:
        data = self._load_data()
        initial_len = len(data)
        data = [item for item in data if item['id'] != expense_id]
        if len(data) < initial_len:
            self._save_data(data)
            return True
        return False

    def load_budgets(self) -> Dict:
        if not self.budget_path.exists():
            return {}
        try:
            with open(self.budget_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_budgets(self, budgets: Dict):
        with open(self.budget_path, 'w', encoding='utf-8') as f:
            json.dump(budgets, f, indent=4)

    def clear_all_expenses(self):
        self._save_data([])

class SQLiteDataStore(DataStore):
    def __init__(self):
        self.db_path = get_db_path()
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Expenses Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                timestamp TEXT NOT NULL,
                date_display TEXT
            )
        ''')
        
        # Budgets Table (Simplified Key-Value store for now to match JSON structure, or structured?)
        # Let's keep it structured but map to the Dict format expected by app
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                amount REAL NOT NULL,
                period TEXT NOT NULL,
                created TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_expense(self, amount: float, category: str, note: str, timestamp: str, expense_id: str = None) -> Dict:
        if not expense_id:
            expense_id = str(uuid.uuid4())[:8]
        date_display = datetime.datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (id, amount, category, note, timestamp, date_display) VALUES (?, ?, ?, ?, ?, ?)",
            (expense_id, amount, category.upper(), note, timestamp, date_display)
        )
        conn.commit()
        conn.close()
        
        return {
            "id": expense_id,
            "amount": amount,
            "category": category.upper(),
            "note": note,
            "timestamp": timestamp,
            "date": date_display
        }

    def get_expenses(self, filters: Dict = None) -> List[Dict]:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses")
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            item = dict(row)
            if 'date_display' in item:
                item['date'] = item['date_display']
            result.append(item)
        
        return result

    def get_expense(self, expense_id: str) -> Optional[Dict]:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            item = dict(row)
            if 'date_display' in item:
                item['date'] = item['date_display']
            return item
        return None

    def update_expense(self, expense_id: str, updates: Dict) -> bool:
        # Construct query dynamically
        if not updates:
            return False
            
        fields = []
        values = []
        for k, v in updates.items():
            if k == 'date': k = 'date_display' # Map internal name
            fields.append(f"{k} = ?")
            values.append(v)
        
        values.append(expense_id)
        
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?", values)
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def delete_expense(self, expense_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def load_budgets(self) -> Dict:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budgets")
        rows = cursor.fetchall()
        conn.close()
        
        budgets = {}
        for row in rows:
            budgets[row['category']] = {
                "amount": row['amount'],
                "period": row['period'],
                "created": row['created']
            }
        return budgets

    def save_budgets(self, budgets: Dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Full replace strategy for simplicity to match JSON behavior
        cursor.execute("DELETE FROM budgets")
        
        for cat, info in budgets.items():
            cursor.execute(
                "INSERT INTO budgets (category, amount, period, created) VALUES (?, ?, ?, ?)",
                (cat, info['amount'], info['period'], info.get('created', ''))
            )
            
        conn.commit()
        conn.close()

    def clear_all_expenses(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses")
        conn.commit()
        conn.close()

class DataStoreFactory:
    _instance = None
    
    @staticmethod
    def get_store() -> DataStore:
        if DataStoreFactory._instance is None:
            # Check config (mocked for now, need to read from a real config or file)
            # For now, default to JSON unless we see a config file saying otherwise
            from config import STORAGE_BACKEND
            
            if STORAGE_BACKEND == "sqlite":
                DataStoreFactory._instance = SQLiteDataStore()
            else:
                DataStoreFactory._instance = JSONDataStore()
        return DataStoreFactory._instance
