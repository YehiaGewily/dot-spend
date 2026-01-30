import os
import json
from pathlib import Path
from platformdirs import user_data_dir

# 1. Define App Metadata
APP_NAME = "dot-spend"
APP_AUTHOR = "Personal"

# 2. Determine OS-Specific Data Path
# On Windows: C:\Users\You\AppData\Local\Personal\dot-spend
# On Linux: /home/you/.local/share/dot-spend
DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
DATA_FILE = DATA_DIR / "expenses.json"
BUDGET_FILE = DATA_DIR / "budgets.json"
HISTORY_FILE = DATA_DIR / "history.json"

# 3. Ensure Directory Exists
def init_storage():
    """Checks if storage folder exists, creates it if not."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DATA_FILE.exists():
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)

    if not BUDGET_FILE.exists():
        with open(BUDGET_FILE, 'w') as f:
            json.dump({}, f)

    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'w') as f:
            json.dump({"transactions": []}, f)

def get_data_path():
    return DATA_FILE

def get_budget_path():
    return BUDGET_FILE

def get_history_path():
    return HISTORY_FILE

def get_db_path():
    return DATA_DIR / "expenses.db"

SETTINGS_FILE = DATA_DIR / "settings.json"

def load_settings():
    if not SETTINGS_FILE.exists():
        return {"storage_backend": "json"}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"storage_backend": "json"}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def get_storage_backend():
    return load_settings().get("storage_backend", "json")

# Storage Configuration
STORAGE_BACKEND = get_storage_backend()