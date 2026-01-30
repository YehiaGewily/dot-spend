import json
import uuid
import datetime
from pathlib import Path
from config import get_data_path, get_budget_path

def load_data():
    """Load expenses from JSON file."""
    path = get_data_path()
    if not path.exists():
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Migration: Ensure IDs and Timestamps
        modified = False
        for entry in data:
            if 'id' not in entry:
                entry['id'] = str(uuid.uuid4())[:8]
                modified = True
            if 'timestamp' not in entry:
                # Try to parse 'date' or use now
                try:
                    dt = datetime.datetime.strptime(entry['date'], "%Y-%m-%d %H:%M")
                    entry['timestamp'] = dt.isoformat()
                except:
                    entry['timestamp'] = datetime.datetime.now().isoformat()
                modified = True
        
        if modified:
            save_data(data)
            
        return data
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_data(data):
    """Save expenses to JSON file."""
    path = get_data_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_budgets():
    """Load budgets from JSON file."""
    path = get_budget_path()
    if not path.exists():
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_budgets(data):
    """Save budgets to JSON file."""
    path = get_budget_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
