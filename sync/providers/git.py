import git
import os
from typing import List
from ..base import SyncProvider, RemoteFile

class GitProvider(SyncProvider):
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = None

    @property
    def name(self) -> str:
        return "git"

    def authenticate(self) -> bool:
        try:
            if not os.path.exists(self.repo_path):
                # Init if not exists? Or expect it to exist
                return False
            self.repo = git.Repo(self.repo_path)
            return True
        except:
            return False

    def list_files(self, remote_path: str = "/") -> List[RemoteFile]:
        # For Git, "remote" is just checking the remote state? 
        # Or listing tracked files?
        # Usually we just sync the whole repo.
        return []

    def upload_file(self, local_path: str, remote_path: str = "/") -> bool:
        # Commit and Push
        if not self.repo: return False
        try:
            # Gitpython requires relative paths for index.add usually
            # Calculate relative path from repo root
            rel_path = os.path.relpath(local_path, self.repo.working_dir)
            
            self.repo.index.add([rel_path])
            if self.repo.is_dirty():
                self.repo.index.commit(f"Auto-sync: update {os.path.basename(local_path)}")
            
            # Use 'origin' or first remote
            if 'origin' in self.repo.remotes:
                origin = self.repo.remotes.origin
            elif self.repo.remotes:
                origin = self.repo.remotes[0]
            else:
                print("No git remote found.")
                return False
                
            origin.push()
            return True
        except Exception as e:
            print(f"Git push failed: {e}")
            return False

    def download_file(self, remote_id: str, local_path: str) -> bool:
        # Pull
        if not self.repo: return False
        try:
            origin = self.repo.remote(name='origin')
            origin.pull()
            return True
        except Exception as e:
            print(f"Git pull failed: {e}")
            return False
