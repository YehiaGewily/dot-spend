import json
import datetime
from pathlib import Path
from config import get_history_path

class HistoryManager:
    def __init__(self):
        self.path = get_history_path()
        self.max_history = 1000

    def _load(self):
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"transactions": []}

    def _save(self, data):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def log_transaction(self, action: str, expense_id: str, before: dict = None, after: dict = None, expense: dict = None):
        """
        Logs a transaction.
        action: 'add', 'edit', 'delete'
        expense_id: ID of the expense involved
        before: State before change (for edit)
        after: State after change (for edit)
        expense: The full expense object (for add/delete context)
        """
        data = self._load()
        
        transaction = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "expense_id": expense_id,
        }
        
        if before: transaction["before"] = before
        if after: transaction["after"] = after
        if expense: transaction["expense"] = expense
        
        data["transactions"].append(transaction)
        
        # Enforce limit
        if len(data["transactions"]) > self.max_history:
            data["transactions"] = data["transactions"][-self.max_history:]
            
        self._save(data)

    def pop_last_transaction(self):
        """Removes and returns the last transaction."""
        data = self._load()
        if not data["transactions"]:
            return None
        
        last = data["transactions"].pop()
        self._save(data)
        return last

    def get_history(self, limit=20):
        data = self._load()
        return data["transactions"][-limit:]

    def clear_history(self):
        self._save({"transactions": []})
