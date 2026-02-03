"""Google Drive API integration for accessing deal files."""

import io
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from ..utils.logging import get_logger

logger = get_logger(__name__)


class GoogleDriveService:
    """Service for accessing files from Google Drive."""

    SCOPES = ['https://www.googleapis.com/auth/drive']  # Read and write access

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Drive service.

        Args:
            credentials_path: Path to service account JSON file
                            (defaults to GOOGLE_DRIVE_CREDENTIALS env var)
        """
        if credentials_path is None:
            credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS")

        if not credentials_path:
            raise ValueError(
                "Google Drive credentials not provided. "
                "Set GOOGLE_DRIVE_CREDENTIALS environment variable or pass credentials_path"
            )

        # In Cloud Run, GOOGLE_DRIVE_CREDENTIALS might be JSON content not a file path
        # Check if it's a file path or JSON content
        if os.path.exists(credentials_path):
            # It's a file path
            pass
        else:
            # Might be JSON content from secret, write it to temp file
            import tempfile
            import json
            try:
                # Try to parse as JSON
                json.loads(credentials_path)
                # It's valid JSON, write to temp file
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                temp_file.write(credentials_path)
                temp_file.close()
                credentials_path = temp_file.name
            except (json.JSONDecodeError, TypeError):
                raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

        # Authenticate using service account
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=self.SCOPES
        )

        # Build the Drive service
        self.service = build('drive', 'v3', credentials=self.credentials)
        logger.info("Google Drive service initialized")

    def get_folder_id_from_path(self, folder_path: str) -> Optional[str]:
        """
        Get folder ID from a shared drive path.

        Note: This requires the folder to be shared with the service account.
        For simplicity, we'll use direct folder IDs instead.

        Args:
            folder_path: Path like "Shared drives/Team/Folder/SubFolder"

        Returns:
            Folder ID or None if not found
        """
        # This is complex - easier to use folder ID directly
        # Users should share the folder and use the ID from the URL
        logger.warning("get_folder_id_from_path is not implemented - use folder ID directly")
        return None

    def list_files_in_folder(
        self,
        folder_id: str,
        mime_type: Optional[str] = None,
        recursive: bool = True
    ) -> list[dict]:
        """
        List files in a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID
            mime_type: Filter by MIME type (e.g., 'text/plain')
            recursive: Search subfolders recursively

        Returns:
            List of file metadata dicts
        """
        all_files = []

        try:
            # Query for files in this folder
            query = f"'{folder_id}' in parents and trashed=false"
            if mime_type:
                query += f" and mimeType='{mime_type}'"

            results = self.service.files().list(
                q=query,
                pageSize=1000,
                fields="files(id, name, mimeType, modifiedTime, size)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])
            logger.info(f"Found {len(files)} items in folder {folder_id}")

            for file in files:
                # If it's a folder and we want recursive, search it too
                if file['mimeType'] == 'application/vnd.google-apps.folder' and recursive:
                    subfolder_files = self.list_files_in_folder(
                        file['id'],
                        mime_type=mime_type,
                        recursive=True
                    )
                    all_files.extend(subfolder_files)
                else:
                    all_files.append(file)

            return all_files

        except Exception as e:
            logger.error(f"Error listing files in folder {folder_id}: {e}", exc_info=True)
            return []

    def download_file(self, file_id: str, destination_path: Path) -> bool:
        """
        Download a file from Google Drive.

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()

            logger.info(f"Downloading file: {file_metadata['name']}")

            # Download file content
            request = self.service.files().get_media(
                fileId=file_id,
                supportsAllDrives=True
            )

            # Create directory if it doesn't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Download to file
            with io.FileIO(str(destination_path), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.debug(f"Download progress: {int(status.progress() * 100)}%")

            logger.info(f"Downloaded: {destination_path}")
            return True

        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}", exc_info=True)
            return False

    def sync_folder_to_local(
        self,
        folder_id: str,
        local_dir: Path,
        file_extension: str = ".txt"
    ) -> list[Path]:
        """
        Sync files from Google Drive folder to local directory.

        Args:
            folder_id: Google Drive folder ID
            local_dir: Local directory to sync to
            file_extension: Only sync files with this extension

        Returns:
            List of downloaded file paths
        """
        logger.info(f"Syncing Google Drive folder {folder_id} to {local_dir}")

        # Create local directory
        local_dir.mkdir(parents=True, exist_ok=True)

        # Get list of files from Drive
        files = self.list_files_in_folder(folder_id, recursive=True)

        # Filter by extension
        txt_files = [f for f in files if f['name'].endswith(file_extension)]
        logger.info(f"Found {len(txt_files)} {file_extension} files")

        downloaded_paths = []

        for file in txt_files:
            # Create local path (preserving structure would be complex, so flat structure)
            local_path = local_dir / file['name']

            # Check if file exists and is up to date
            if local_path.exists():
                # Compare modification times (simplified - just skip existing)
                logger.debug(f"Skipping existing file: {file['name']}")
                downloaded_paths.append(local_path)
                continue

            # Download the file
            if self.download_file(file['id'], local_path):
                downloaded_paths.append(local_path)

        logger.info(f"Synced {len(downloaded_paths)} files to {local_dir}")
        return downloaded_paths

    def upload_file(self, file_path: Path, folder_id: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to Google Drive folder with retry logic.

        Args:
            file_path: Local path to file to upload
            folder_id: Google Drive folder ID to upload to
            filename: Optional filename (defaults to file_path.name)

        Returns:
            File ID of uploaded file, or None if upload failed
        """
        import time
        from googleapiclient.http import MediaFileUpload

        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        filename = filename or file_path.name
        max_retries = 3
        retry_delay = 1  # Start with 1 second

        for attempt in range(max_retries):
            try:
                # Check if file already exists in folder
                query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
                results = self.service.files().list(
                    q=query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                file_metadata = {
                    'name': filename,
                    'parents': [folder_id]
                }

                # Use non-resumable upload for small files to avoid "Broken pipe" errors in Cloud Run
                # Database files are typically < 5MB, so non-resumable is faster and more reliable
                media = MediaFileUpload(str(file_path), resumable=False)

                if results.get('files'):
                    # File exists, update it
                    file_id = results['files'][0]['id']
                    logger.info(f"Updating existing file in Google Drive: {filename} (attempt {attempt + 1}/{max_retries})")
                    file = self.service.files().update(
                        fileId=file_id,
                        media_body=media,
                        supportsAllDrives=True
                    ).execute()
                else:
                    # Create new file
                    logger.info(f"Uploading new file to Google Drive: {filename} (attempt {attempt + 1}/{max_retries})")
                    file = self.service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id',
                        supportsAllDrives=True
                    ).execute()

                logger.info(f"✅ Successfully uploaded {filename} (ID: {file.get('id')})")
                return file.get('id')

            except Exception as e:
                logger.warning(f"Upload attempt {attempt + 1}/{max_retries} failed for {filename}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"❌ Failed to upload {filename} after {max_retries} attempts")
                    return None

        return None

    def sync_database(self, db_path: Path, folder_id: str, download: bool = True) -> bool:
        """
        Sync database file with Google Drive.

        Args:
            db_path: Local path to database file
            folder_id: Google Drive folder ID for database storage
            download: If True, download from Drive (at startup). If False, upload to Drive (at shutdown).

        Returns:
            True if sync successful, False otherwise
        """
        db_filename = "dealbot.db"

        if download:
            # Download database from Drive (if exists)
            try:
                query = f"name='{db_filename}' and '{folder_id}' in parents and trashed=false"
                results = self.service.files().list(
                    q=query,
                    fields="files(id, name)",
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                if results.get('files'):
                    file_id = results['files'][0]['id']
                    logger.info(f"Downloading database from Google Drive...")
                    return self.download_file(file_id, db_path)
                else:
                    logger.info(f"No existing database found in Google Drive, will create new one")
                    return True  # Not an error, just no existing DB

            except Exception as e:
                logger.error(f"Failed to download database: {e}")
                return False
        else:
            # Upload database to Drive
            try:
                logger.info(f"Uploading database to Google Drive...")
                file_id = self.upload_file(db_path, folder_id, db_filename)
                return file_id is not None
            except Exception as e:
                logger.error(f"Failed to upload database: {e}")
                return False
