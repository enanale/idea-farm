"""
Drive Service

Handles interaction with Google Drive using Application Default Credentials (Service Account).
Requires the target folder to be shared with the Service Account.
"""

import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import json

logger = logging.getLogger(__name__)

# Scope is implied by ADC, but for Drive specific operations we might need to be explicit if using credentials object
# With Cloud Functions, default credentials usually have scope if enabled in Service Account.

class DriveService:
    def __init__(self):
        self.service = build('drive', 'v3')

    def find_folder(self, folder_name: str) -> str | None:
        """Finds a folder by name that the service account has access to."""
        try:
            # Query for folder
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            return None
        except Exception as e:
            logger.error(f"Error finding folder {folder_name}: {e}")
            return None

    def upload_text_file(self, folder_id: str, title: str, content: str, mime_type: str = 'text/plain', extension: str = 'txt') -> str | None:
        """Uploads a text content as a file to the specified folder."""
        try:
            file_metadata = {
                'name': f"{title}.{extension}",
                'parents': [folder_id]
            }
            
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            logger.info(f"Uploaded file {title} ({file.get('id')})")
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Error uploading file {title}: {e}")
            return None

# Singleton instance
_drive_service = None

def get_drive_service():
    global _drive_service
    if not _drive_service:
        _drive_service = DriveService()
    return _drive_service
