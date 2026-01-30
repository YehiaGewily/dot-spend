from typing import List
import os
import io
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from ..base import SyncProvider, RemoteFile

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json' # Placeholder, should be config
TOKEN_FILE = 'token.pickle'

class GoogleDriveProvider(SyncProvider):
    def __init__(self, token_path: str = TOKEN_FILE, creds_path: str = CREDENTIALS_FILE):
        self.token_path = token_path
        self.creds_path = creds_path
        self.service = None
        self.folder_id = None # Root folder ID

    @property
    def name(self) -> str:
        return "google_drive"

    def authenticate(self) -> bool:
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.creds_path):
                    print(f"Credentials file not found: {self.creds_path}")
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.creds_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        try:
            self.service = build('drive', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"Auth failed: {e}")
            return False

    def _get_folder_id(self, folder_name="dot-spend"):
        if self.folder_id: return self.folder_id
        
        # Check if exists
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, spaces='drive').execute()
        items = results.get('files', [])
        
        if not items:
            # Create
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = self.service.files().create(body=metadata, fields='id').execute()
            self.folder_id = file.get('id')
        else:
            self.folder_id = items[0]['id']
            
        return self.folder_id

    def list_files(self, remote_path: str = "/") -> List[RemoteFile]:
        if not self.service: return []
        folder_id = self._get_folder_id()
        
        query = f"'{folder_id}' in parents and trashed = false"
        results = self.service.files().list(
            q=query, fields="files(id, name, modifiedTime, size, md5Checksum)").execute()
        items = results.get('files', [])
        
        files = []
        for item in items:
            files.append(RemoteFile(
                name=item['name'],
                id=item['id'],
                modified_time=item.get('modifiedTime'),
                size=int(item.get('size', 0)),
                hash=item.get('md5Checksum', "") # Google Drive provides MD5
            ))
        return files

    def upload_file(self, local_path: str, remote_path: str = "/") -> bool:
        if not self.service: return False
        folder_id = self._get_folder_id()
        name = os.path.basename(local_path)
        
        # Check if exists to update or create
        existing = [f for f in self.list_files() if f.name == name]
        
        media = MediaFileUpload(local_path, resumable=True)
        
        if existing:
            file_id = existing[0].id
            self.service.files().update(
                fileId=file_id,
                media_body=media).execute()
        else:
            metadata = {'name': name, 'parents': [folder_id]}
            self.service.files().create(
                body=metadata,
                media_body=media,
                fields='id').execute()
        return True

    def download_file(self, remote_id: str, local_path: str) -> bool:
        if not self.service: return False
        request = self.service.files().get_media(fileId=remote_id)
        fh = io.FileIO(local_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return True
