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

# 3. Ensure Directory Exists
def init_storage():
    """Checks if storage folder exists, creates it if not."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if not DATA_FILE.exists():
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)

def get_data_path():
    return DATA_FILE