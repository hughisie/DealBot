"""Simple HTTP server for Cloud Run integration."""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

from .daemon import DealBotDaemon
from .services.gdrive import GoogleDriveService
from .services.gcs_storage import GCSStorage
from .utils.config import Config
from .utils.logging import get_logger

logger = get_logger(__name__)


class DealBotHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Cloud Run triggers."""

    daemon: DealBotDaemon = None
    gdrive_service: GoogleDriveService = None
    folder_id: str = None
    gcs_storage: GCSStorage = None  # For database persistence

    def do_HEAD(self):
        """Handle HEAD requests (for Cloud Run health checks)."""
        # Respond to all HEAD requests with 200 OK
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests from Cloud Scheduler."""
        if self.path.startswith('/?') or self.path == '/':
            # Trigger deal processing
            logger.info("Received HTTP trigger for deal processing")

            try:
                # Download database from GCS (for duplicate detection)
                db_path = Path.home() / "Library" / "Application Support" / "DealBot" / "dealbot.db"
                if self.gcs_storage:
                    try:
                        db_path.parent.mkdir(parents=True, exist_ok=True)
                        logger.info(f"📥 Downloading database from GCS...")
                        success = self.gcs_storage.download_file("dealbot.db", db_path)
                        if success:
                            logger.info("✅ Database downloaded from GCS")
                        else:
                            logger.info("ℹ️  No existing database in GCS (first run)")
                    except Exception as e:
                        logger.error(f"❌ Failed to download database from GCS: {e}", exc_info=True)
                        # Continue anyway - database will be created fresh

                # Sync deal files from Google Drive if configured
                if self.gdrive_service and self.folder_id:
                    logger.info("🔄 Syncing deal files from Google Drive...")
                    local_sync_dir = Path("/app/gdrive_sync")

                    self.gdrive_service.sync_folder_to_local(
                        self.folder_id,
                        local_sync_dir,
                        file_extension=".txt"
                    )
                    source_dir = local_sync_dir
                    logger.info(f"✅ Deal files synced to {local_sync_dir}")
                else:
                    logger.warning("⚠️ Google Drive not configured, using local directory")
                    # Use configured source directory
                    config = Config()
                    source_dir = Path(config.get("default_source_dir", "."))

                # Run processing
                self.daemon.run_once(source_dir)

                # Upload database to GCS (to persist for next run)
                if self.gcs_storage:
                    logger.info("📤 Uploading database to GCS...")
                    db_path = Path.home() / "Library" / "Application Support" / "DealBot" / "dealbot.db"
                    if db_path.exists():
                        success = self.gcs_storage.upload_file(db_path, "dealbot.db")
                        if success:
                            logger.info("✅ Database uploaded to GCS successfully")
                        else:
                            logger.error("❌ Failed to upload database to GCS")
                    else:
                        logger.warning(f"⚠️  Database file not found at {db_path}, skipping upload")

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Deal processing completed successfully')

            except Exception as e:
                logger.error(f"Error processing deals: {e}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())

        elif self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"HTTP: {format % args}")


def run_http_server(daemon: DealBotDaemon, gdrive_service=None, folder_id=None, gcs_storage=None, port=8080):
    """
    Run HTTP server for Cloud Run.

    Args:
        daemon: DealBotDaemon instance
        gdrive_service: Optional GoogleDriveService instance (for deal files)
        folder_id: Optional Google Drive folder ID
        gcs_storage: Optional GCSStorage instance (for database persistence)
        port: Port to listen on (default: 8080, Cloud Run standard)
    """
    # Set class variables for handler
    DealBotHTTPHandler.daemon = daemon
    DealBotHTTPHandler.gdrive_service = gdrive_service
    DealBotHTTPHandler.folder_id = folder_id
    DealBotHTTPHandler.gcs_storage = gcs_storage

    server = HTTPServer(('0.0.0.0', port), DealBotHTTPHandler)
    logger.info(f"HTTP server listening on port {port}")
    logger.info("Ready to receive triggers from Cloud Scheduler")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("HTTP server stopped")
    finally:
        server.server_close()
