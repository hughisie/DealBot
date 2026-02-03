#!/usr/bin/env python3
"""
DealBot Daemon - Autonomous deal processing service.

This script runs the DealBot as a headless daemon service that:
- Syncs deal files from Google Drive
- Processes deals automatically at 6am and 6pm Spain time
- Publishes qualifying deals to WhatsApp
- Sends status updates

Usage:
    python run_daemon.py [--once] [--source-dir PATH] [--use-gdrive] [--http]

Options:
    --once          Run once immediately and exit (for testing)
    --source-dir    Override source directory from config
    --use-gdrive    Sync files from Google Drive before processing
    --folder-id     Google Drive folder ID (required with --use-gdrive)
    --http          Run HTTP server for Cloud Run (default mode if PORT env var set)
"""

import argparse
import os
import sys
from pathlib import Path

from dealbot.daemon import DealBotDaemon
from dealbot.http_server import run_http_server
from dealbot.scheduler import DealBotScheduler
from dealbot.services.gdrive import GoogleDriveService
from dealbot.services.gcs_storage import GCSStorage
from dealbot.utils.config import Config
from dealbot.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


def main():
    """Main entry point for daemon."""
    parser = argparse.ArgumentParser(description="DealBot Daemon")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once immediately and exit (for testing)"
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        help="Override source directory from config"
    )
    parser.add_argument(
        "--use-gdrive",
        action="store_true",
        help="Sync files from Google Drive before processing"
    )
    parser.add_argument(
        "--folder-id",
        type=str,
        help="Google Drive folder ID (from env or arg)"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run HTTP server for Cloud Run (default if PORT env var set)"
    )

    args = parser.parse_args()

    # Auto-enable HTTP mode if PORT environment variable is set (Cloud Run standard)
    if os.getenv("PORT") and not args.once:
        args.http = True
        logger.info("PORT env var detected - enabling HTTP server mode")

    # Setup logging
    setup_logging()

    logger.info("="*60)
    logger.info("Starting DealBot Daemon")
    logger.info("="*60)

    try:
        # Load configuration
        config = Config()
        logger.info("Configuration loaded")

        # Initialize daemon
        daemon = DealBotDaemon(config)
        logger.info("Daemon initialized")

        # Setup Google Drive sync if requested or if env var set
        gdrive_service = None
        local_sync_dir = None
        folder_id = args.folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")

        # Auto-enable gdrive if credentials and folder_id are available
        if os.getenv("GOOGLE_DRIVE_CREDENTIALS") and folder_id:
            args.use_gdrive = True

        if args.use_gdrive:
            if not folder_id:
                logger.error("Google Drive folder ID not provided")
                logger.error("Set GOOGLE_DRIVE_FOLDER_ID env var or use --folder-id")
                sys.exit(1)

            try:
                gdrive_service = GoogleDriveService()
                local_sync_dir = Path("./gdrive_sync")
                logger.info(f"Google Drive service initialized (folder: {folder_id})")
            except Exception as e:
                logger.error(f"Failed to initialize Google Drive: {e}")
                logger.error("Make sure GOOGLE_DRIVE_CREDENTIALS is set correctly")
                sys.exit(1)

        # Define the task function
        def process_deals():
            """Task function that syncs (if needed) and processes deals."""
            try:
                # Sync from Google Drive if enabled
                if gdrive_service and local_sync_dir and folder_id:
                    logger.info("Syncing files from Google Drive...")
                    gdrive_service.sync_folder_to_local(
                        folder_id,
                        local_sync_dir,
                        file_extension=".txt"
                    )
                    source_dir = local_sync_dir
                else:
                    # Use configured source directory or override
                    if args.source_dir:
                        source_dir = Path(args.source_dir)
                    else:
                        source_dir = Path(config.get("default_source_dir", "."))

                # Run processing
                daemon.run_once(source_dir)

            except Exception as e:
                logger.error(f"Error in process_deals: {e}", exc_info=True)

        # Run based on mode
        if args.once:
            # Run once and exit
            logger.info("Running in --once mode (immediate single run)")
            process_deals()
            logger.info("Single run complete, exiting")
        elif args.http:
            # Run HTTP server for Cloud Run
            port = int(os.getenv("PORT", 8080))
            logger.info(f"Running in HTTP server mode on port {port}")

            # Initialize GCS storage for database persistence
            gcs_storage = None
            gcs_bucket = os.getenv("GCS_BUCKET_NAME")
            gcp_project = os.getenv("GCP_PROJECT_ID")

            if gcs_bucket:
                try:
                    gcs_storage = GCSStorage(bucket_name=gcs_bucket, project_id=gcp_project)
                    logger.info(f"GCS storage initialized for bucket: {gcs_bucket}")
                except Exception as e:
                    logger.error(f"Failed to initialize GCS storage: {e}")
                    logger.warning("Database persistence will not work without GCS")
            else:
                logger.warning("GCS_BUCKET_NAME not set - database will not persist between runs")

            run_http_server(daemon, gdrive_service, folder_id, gcs_storage, port)
        else:
            # Run on schedule (internal scheduler)
            scheduler = DealBotScheduler(task_func=process_deals)
            scheduler.run_forever()

    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Daemon shutdown complete")


if __name__ == "__main__":
    main()
