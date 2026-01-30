from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path

class ConflictResolution(str, Enum):
    LAST_WRITE_WINS = "last_write_wins"
    MANUAL = "manual"
    KEEP_BOTH = "keep_both"

@dataclass
class RemoteFile:
    name: str
    id: str # Remote ID or path
    modified_time: str # ISO
    size: int
    hash: str = ""

class SyncProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the provider."""
        pass

    @abstractmethod
    def list_files(self, remote_path: str = "/") -> List[RemoteFile]:
        """List files in remote directory."""
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str = "/") -> bool:
        """Upload a file."""
        pass

    @abstractmethod
    def download_file(self, remote_id: str, local_path: str) -> bool:
        """Download a file."""
        pass

def calculate_file_hash(path: str) -> str:
    """Calculate SHA256 hash of a file."""
    p = Path(path)
    if not p.exists():
        return ""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
