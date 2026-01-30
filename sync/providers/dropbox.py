from typing import List
import os
import dropbox
from ..base import SyncProvider, RemoteFile

class DropboxProvider(SyncProvider):
    def __init__(self, token: str):
        self.token = token
        self.dbx = None

    @property
    def name(self) -> str:
        return "dropbox"

    def authenticate(self) -> bool:
        if not self.token: return False
        try:
            self.dbx = dropbox.Dropbox(self.token)
            # Check connection
            self.dbx.users_get_current_account()
            return True
        except:
            return False

    def list_files(self, remote_path: str = "/Apps/dot-spend") -> List[RemoteFile]:
        if not self.dbx: return []
        try:
            result = self.dbx.files_list_folder(remote_path)
            files = []
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                     files.append(RemoteFile(
                         name=entry.name,
                         id=entry.path_lower,
                         modified_time=str(entry.client_modified),
                         size=entry.size,
                         hash=entry.content_hash
                     ))
            return files
        except:
            return []

    def upload_file(self, local_path: str, remote_path: str = "/Apps/dot-spend") -> bool:
        if not self.dbx: return False
        name = os.path.basename(local_path)
        dest_path = f"{remote_path}/{name}"
        
        with open(local_path, 'rb') as f:
            try:
                self.dbx.files_upload(
                    f.read(), dest_path, mode=dropbox.files.WriteMode.overwrite)
                return True
            except:
                return False

    def download_file(self, remote_id: str, local_path: str) -> bool:
        if not self.dbx: return False
        try:
             self.dbx.files_download_to_file(local_path, remote_id)
             return True
        except:
            return False
