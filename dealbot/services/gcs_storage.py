"""Google Cloud Storage service for database persistence."""

from pathlib import Path
from typing import Optional

from google.cloud import storage

from ..utils.logging import get_logger

logger = get_logger(__name__)


class GCSStorage:
    """Service for storing and retrieving files from Google Cloud Storage."""

    def __init__(self, bucket_name: str, project_id: Optional[str] = None):
        """
        Initialize GCS storage service.

        Args:
            bucket_name: Name of the GCS bucket
            project_id: Optional GCP project ID (uses default credentials if not provided)
        """
        self.bucket_name = bucket_name
        self.client = storage.Client(project=project_id) if project_id else storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        logger.info(f"GCS Storage initialized for bucket: {bucket_name}")

    def upload_file(self, local_path: Path, remote_name: Optional[str] = None) -> bool:
        """
        Upload a file to GCS bucket.

        Args:
            local_path: Local file path to upload
            remote_name: Name to use in GCS (defaults to filename)

        Returns:
            True if successful, False otherwise
        """
        if not local_path.exists():
            logger.error(f"File not found: {local_path}")
            return False

        remote_name = remote_name or local_path.name

        try:
            blob = self.bucket.blob(remote_name)
            blob.upload_from_filename(str(local_path))
            logger.info(f"✅ Successfully uploaded {local_path.name} to gs://{self.bucket_name}/{remote_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload {local_path.name}: {e}")
            return False

    def download_file(self, remote_name: str, local_path: Path) -> bool:
        """
        Download a file from GCS bucket.

        Args:
            remote_name: Name of file in GCS
            local_path: Local path to save file

        Returns:
            True if successful, False otherwise
        """
        try:
            blob = self.bucket.blob(remote_name)

            if not blob.exists():
                logger.info(f"File {remote_name} does not exist in GCS bucket (first run)")
                return False

            # Create parent directory if needed
            local_path.parent.mkdir(parents=True, exist_ok=True)

            blob.download_to_filename(str(local_path))
            logger.info(f"✅ Successfully downloaded {remote_name} from GCS to {local_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to download {remote_name}: {e}")
            return False

    def file_exists(self, remote_name: str) -> bool:
        """
        Check if a file exists in the GCS bucket.

        Args:
            remote_name: Name of file in GCS

        Returns:
            True if file exists, False otherwise
        """
        try:
            blob = self.bucket.blob(remote_name)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking if {remote_name} exists: {e}")
            return False
