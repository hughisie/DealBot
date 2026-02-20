"""SQLite database management."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..models import ProcessedDeal, PublishResult
from ..utils.logging import get_logger

logger = get_logger(__name__)


class Database:
    """SQLite database wrapper for deal storage and analytics."""

    def __init__(self, db_path: str | Path = "dealbot.db") -> None:
        """Initialize database connection."""
        # If using default path, use Application Support directory
        if db_path == "dealbot.db":
            app_support = Path.home() / "Library" / "Application Support" / "DealBot"
            app_support.mkdir(parents=True, exist_ok=True)
            self.db_path = app_support / "dealbot.db"
        else:
            self.db_path = Path(db_path)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Deals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                deal_id TEXT PRIMARY KEY,
                asin TEXT,
                title TEXT,
                src_url TEXT,
                validated_price REAL,
                adjusted_price REAL,
                list_price REAL,
                discount_pct REAL,
                degree INTEGER,
                currency TEXT,
                rating REAL,
                rating_count INTEGER,
                short_url TEXT,
                provider TEXT,
                created_at TIMESTAMP,
                published_at TIMESTAMP,
                status TEXT
            )
        """)

        # Add new columns to existing DBs that pre-date this schema
        for col, col_type in [("list_price", "REAL"), ("discount_pct", "REAL"), ("degree", "INTEGER")]:
            try:
                cursor.execute(f"ALTER TABLE deals ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass  # Column already exists

        # Destinations table (many-to-many with deals)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS destinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id TEXT,
                jid TEXT,
                type TEXT,
                sent_at TIMESTAMP,
                message_id TEXT,
                FOREIGN KEY (deal_id) REFERENCES deals(deal_id)
            )
        """)

        # Events table (analytics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deal_id TEXT,
                type TEXT,
                meta TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (deal_id) REFERENCES deals(deal_id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_asin ON deals(asin)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_status ON deals(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_destinations_deal ON destinations(deal_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_deal ON events(deal_id)")

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def save_deal(self, deal: ProcessedDeal) -> None:
        """Save a processed deal to database."""
        cursor = self.conn.cursor()

        rating = deal.rating.value if deal.rating else None
        rating_count = deal.rating.count if deal.rating else None

        # Determine best available discount/PVP from either PA-API or source file
        list_price = deal.price_info.list_price or deal.deal.source_pvp
        discount_pct = deal.price_info.savings_percentage or deal.deal.source_discount_pct

        cursor.execute(
            """
            INSERT OR REPLACE INTO deals (
                deal_id, asin, title, src_url, validated_price, adjusted_price,
                list_price, discount_pct, degree,
                currency, rating, rating_count, short_url, provider,
                created_at, published_at, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                deal.deal.deal_id,
                deal.deal.asin,
                deal.deal.title,
                deal.deal.url,
                deal.price_info.current_price,
                deal.adjusted_price,
                list_price,
                discount_pct,
                deal.deal.degree,
                deal.price_info.currency.value,
                rating,
                rating_count,
                deal.short_link.short_url,
                deal.short_link.provider,
                datetime.now().isoformat(),
                (
                    deal.publish_result.sent_at.isoformat()
                    if deal.publish_result
                    else None
                ),
                deal.deal.status.value,
            ),
        )

        # Save destinations if published
        if deal.publish_result:
            for dest, msg_id in deal.publish_result.message_ids.items():
                dest_type = "channel" if "broadcast" in dest else "group"
                cursor.execute(
                    """
                    INSERT INTO destinations (deal_id, jid, type, sent_at, message_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        deal.deal.deal_id,
                        dest,
                        dest_type,
                        deal.publish_result.sent_at.isoformat(),
                        msg_id,
                    ),
                )

        self.conn.commit()
        logger.debug(f"Saved deal {deal.deal.deal_id} to database")

    def log_event(self, deal_id: str, event_type: str, meta: dict[str, Any]) -> None:
        """Log an analytics event."""
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO events (deal_id, type, meta, created_at)
            VALUES (?, ?, ?, ?)
        """,
            (deal_id, event_type, json.dumps(meta), datetime.now().isoformat()),
        )

        self.conn.commit()

    def get_deal(self, deal_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a deal by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM deals WHERE deal_id = ?", (deal_id,))
        row = cursor.fetchone()

        return dict(row) if row else None

    def get_all_deals(self, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve all deals (latest first)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM deals ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def was_recently_published(self, asin: str, hours: int = 48) -> Optional[dict[str, Any]]:
        """Check if ASIN was published within the last N hours."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM deals 
            WHERE asin = ? 
            AND status = 'published'
            AND published_at IS NOT NULL
            AND datetime(published_at) > datetime('now', ?)
            ORDER BY published_at DESC
            LIMIT 1
            """,
            (asin, f'-{hours} hours'),
        )
        
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_top_deals_today(self, limit: int = 3) -> list[dict[str, Any]]:
        """
        Return today's top published deals sorted by hotness.
        Primary sort: degree (Chollometro temperature) descending.
        Secondary sort: discount_pct descending.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM deals
            WHERE status = 'published'
              AND datetime(published_at) > datetime('now', '-24 hours')
            ORDER BY
                COALESCE(degree, 0) DESC,
                COALESCE(discount_pct, 0) DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def export_to_csv(self, output_path: str | Path) -> None:
        """Export deals to CSV file."""
        import csv

        output_path = Path(output_path)
        deals = self.get_all_deals(limit=10000)

        if not deals:
            logger.warning("No deals to export")
            return

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=deals[0].keys())
            writer.writeheader()
            writer.writerows(deals)

        logger.info(f"Exported {len(deals)} deals to {output_path}")

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()

    def __enter__(self) -> "Database":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
