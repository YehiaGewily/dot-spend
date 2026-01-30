import json
from pathlib import Path
from typing import Optional
from .base import SyncProvider, ConflictResolution
from .providers.google_drive import GoogleDriveProvider
from .providers.git import GitProvider
from .providers.dropbox import DropboxProvider

CONFIG_FILE = Path("sync_config.json")

class SyncManager:
    def __init__(self):
        # ... (no change to init)
        self.provider: Optional[SyncProvider] = None
        self.config = self._load_config()
        self._init_provider()

    def _load_config(self):
        # Load from DATA_DIR instead of CWD to be globally accessible
        from config import DATA_DIR
        config_path = DATA_DIR / "sync_config.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {"enabled": False, "provider": None, "auto_sync": False}

    def save_config(self):
        from config import DATA_DIR
        config_path = DATA_DIR / "sync_config.json"
        with open(config_path, "w") as f:
            json.dump(self.config, f)

    def _init_provider(self):
        if not self.config.get("enabled"): return
        
        provider_name = self.config.get("provider")
        data = self.config.get("provider_data", {})
        
        if provider_name == "google_drive":
            self.provider = GoogleDriveProvider() # creds path?
        elif provider_name == "git":
            from config import DATA_DIR
            repo_path = data.get("repo_path") or str(DATA_DIR)
            self.provider = GitProvider(repo_path)
        elif provider_name == "dropbox":
            self.provider = DropboxProvider(data.get("token", ""))
            
        if self.provider:
            self.provider.authenticate()

    def setup(self, provider_name: str, **kwargs):
        self.config["provider"] = provider_name
        self.config["enabled"] = True
        self.config["provider_data"] = kwargs
        self.save_config()
        self._init_provider()
        
    def sync_now(self, local_files: list):
        if not self.provider: return "Sync disabled or provider not ready."
        
        # Simple Sync: Upload Local -> Remote (Last Write Wins)
        # TODO: Real merge logic
        results = []
        for path in local_files:
            success = self.provider.upload_file(path)
            results.append(f"Upload {path}: {'OK' if success else 'Fail'}")
            
        return "\n".join(results)
