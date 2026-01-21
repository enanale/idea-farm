"""
Drive Service

Handles interaction with Google Drive.
Supports both Service Account (default) and User Credentials (for offline access).
"""

import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

logger = logging.getLogger(__name__)

class DriveService:
    def __init__(self, credentials=None):
        if credentials:
            self.service = build('drive', 'v3', credentials=credentials)
        else:
            # Fallback to Application Default Credentials (ADC)
            self.service = build('drive', 'v3')

    def find_folder(self, folder_name: str) -> str | None:
        """Finds a folder by name that the user/service account has access to."""
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

    def create_folder(self, folder_name: str) -> str | None:
        """Creates a new folder."""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            file = self.service.files().create(body=file_metadata, fields='id').execute()
            return file.get('id')
        except Exception as e:
            logger.error(f"Error creating folder {folder_name}: {e}")
            return None

    def ensure_folder(self, folder_name: str) -> str | None:
        """Finds or creates a folder."""
        folder_id = self.find_folder(folder_name)
        if folder_id:
            return folder_id
        return self.create_folder(folder_name)

    def upload_markdown(self, filename: str, content: str, folder_name: str = "Idea Farm") -> str | None:
        """Uploads markdown content to a specific folder (created if missing)."""
        try:
            folder_id = self.ensure_folder(folder_name)
            
            file_metadata = {
                'name': filename, 
                # No extension in name usually needed for GDrive if mime attached, but good for display
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')),
                mimetype='text/markdown',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            logger.info(f"Uploaded file {filename} ({file.get('id')})")
            return file.get('id')
            
        except Exception as e:
            logger.error(f"Error uploading file {filename}: {e}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """Deletes a file by ID."""
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file {file_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False

def get_drive_service(credentials=None):
    return DriveService(credentials)
