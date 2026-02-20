"""Headless daemon service for autonomous deal processing."""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .controller import DealController
from .models import Deal, ProcessedDeal
from .services.whapi import WhapiService
from .utils.config import Config
from .utils.logging import get_logger

logger = get_logger(__name__)


class DealFilter:
    """Smart filtering logic for determining which deals to publish."""

    def __init__(self, config: Config):
        self.config = config

    def should_publish(self, deal: Deal, processed: ProcessedDeal) -> tuple[bool, str]:
        """
        Determine if a deal should be published based on smart rules.

        Returns:
            tuple[bool, str]: (should_publish, reason)
        """
        price_info = processed.price_info

        # Rule 0: STRICT QUALITY CHECKS - Must pass ALL to publish

        # Rule 0a: Must have an image (NO EXCEPTIONS)
        has_image = price_info and price_info.main_image_url
        if not has_image:
            return False, "❌ NO IMAGE - Cannot publish without product image"

        # Rule 0b: Must have PVP AND discount information (no exceptions)
        has_pvp = (price_info.list_price and price_info.list_price > 0) or (deal.source_pvp and deal.source_pvp > 0)
        has_discount = (price_info.savings_percentage and price_info.savings_percentage > 0) or (deal.source_discount_pct and deal.source_discount_pct > 0)

        if not has_pvp:
            return False, "❌ NO PVP - Cannot publish without original price"
        if not has_discount:
            return False, "❌ NO DISCOUNT - Cannot publish without discount percentage"

        # Rule 0c: Price validation - CRITICAL for accuracy
        # Check for severe price discrepancies that indicate bad data
        if deal.stated_price and price_info.current_price:
            price_ratio = price_info.current_price / deal.stated_price
            # If actual price is more than 2x or less than 0.5x the stated price, reject
            if price_ratio > 2.0 or price_ratio < 0.5:
                return False, f"❌ PRICE ERROR - Actual €{price_info.current_price} vs stated €{deal.stated_price} (ratio: {price_ratio:.2f})"

        # Rule 0d: Minimum discount threshold - Must be a real deal (20%+)
        actual_discount = price_info.savings_percentage or deal.source_discount_pct or 0
        if actual_discount < 20:
            return False, f"❌ INSUFFICIENT DISCOUNT - Only {actual_discount}% (minimum 20% required)"

        # Rule 0e: No mandatory delivery costs allowed
        # Deals with mandatory delivery fees make the actual price higher than advertised
        if hasattr(processed, 'has_mandatory_delivery') and processed.has_mandatory_delivery:
            delivery_cost = getattr(processed, 'delivery_cost', 0)
            return False, f"❌ MANDATORY DELIVERY - €{delivery_cost} delivery cost makes deal less attractive"

        # Rule 0f: AI validation must approve
        # Claude AI performs final sanity check on price, discount, and product-price match
        if hasattr(processed, 'ai_approved') and not processed.ai_approved:
            return False, "❌ AI REJECTED - Deal failed AI sanity check (price/discount suspicious)"

        # Rule 1: Must have a current price (stock check)
        if not price_info or not price_info.current_price:
            return False, "No current price available (out of stock)"

        # Rule 2: Must be available (not out of stock)
        if price_info.availability and price_info.availability not in ["Now", None, ""]:
            return False, f"Out of stock (availability: {price_info.availability})"

        actual_price = price_info.current_price
        txt_price = deal.stated_price
        txt_discount = deal.source_discount_pct
        txt_pvp = deal.source_pvp
        actual_pvp = price_info.list_price
        actual_discount = price_info.savings_percentage

        # Rule 3: Always publish if actual price is cheaper than TXT price
        if txt_price and actual_price < txt_price:
            return True, f"Price better than expected (€{actual_price} < €{txt_price})"

        # Rule 4: Price within 10% tolerance of TXT price
        if txt_price and actual_price <= txt_price * 1.10:
            # If TXT showed a discount, check if actual discount is within 10% of it
            if txt_discount:
                if actual_discount and actual_discount >= (txt_discount - 10):
                    return True, f"Discount within tolerance ({actual_discount}% vs {txt_discount}% expected)"
                else:
                    return False, f"Discount dropped too much ({actual_discount}% vs {txt_discount}% expected)"
            else:
                # No discount in TXT, just check price tolerance
                return True, f"Price within tolerance (€{actual_price} vs €{txt_price} expected)"

        # Rule 5: Price increased beyond tolerance
        if txt_price and actual_price > txt_price * 1.10:
            return False, f"Price increased beyond tolerance (€{actual_price} > €{txt_price * 1.10})"

        # Rule 6: Minimum "good deal" threshold (even without TXT price reference)
        # This catches deals that don't have stated prices but are good
        if actual_discount and actual_discount >= 20:
            return True, f"Minimum discount threshold met ({actual_discount}%)"

        # Rule 7: Low-risk impulse buy (cheap items)
        if actual_price <= 20:
            # Still require some discount for cheap items
            if actual_discount and actual_discount >= 15:
                return True, f"Low-risk deal under €20 with {actual_discount}% discount"

        # Default: Don't publish if none of the above criteria met
        return False, f"No criteria met for publishing (price: €{actual_price}, discount: {actual_discount}%)"


class DealBotDaemon:
    """Main daemon for autonomous deal processing."""

    def __init__(self, config: Config):
        self.config = config
        self.controller = DealController(config)
        self.filter = DealFilter(config)
        self.whapi = WhapiService(config)

        # Track processed files to avoid duplicates
        self.processed_files: set[str] = set()

        # Stats for status updates
        self.stats = {
            'files_processed': 0,
            'deals_found': 0,
            'deals_published': 0,
            'deals_filtered': 0,
            'last_run': None,
            'errors': []
        }

    def find_latest_deal_files(self, source_dir: Path, since: Optional[datetime] = None) -> list[Path]:
        """
        Find TXT files in the source directory.

        Args:
            source_dir: Directory to search
            since: Only return files with dates after this time (parsed from filename)

        Returns:
            List of TXT file paths, sorted by date from filename (newest first)
        """
        if not source_dir.exists():
            logger.error(f"Source directory does not exist: {source_dir}")
            return []

        # Find all .txt files recursively
        txt_files = list(source_dir.rglob("*.txt"))

        # Parse date from filename (format: 2025-11-19_1602_evening_whatsapp.txt)
        import re
        date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})_(\d{2})(\d{2})')

        def get_file_date(file_path: Path) -> Optional[datetime]:
            """Extract datetime from filename."""
            match = date_pattern.search(file_path.name)
            if match:
                year, month, day, hour, minute = map(int, match.groups())
                try:
                    return datetime(year, month, day, hour, minute)
                except ValueError:
                    logger.warning(f"Invalid date in filename: {file_path.name}")
            return None

        # Filter by date from filename if specified
        filtered_files = []
        for f in txt_files:
            file_date = get_file_date(f)
            if file_date:
                if since is None or file_date > since:
                    filtered_files.append((f, file_date))
            else:
                # If we can't parse date, include it anyway (fallback to old behavior)
                filtered_files.append((f, datetime.fromtimestamp(f.stat().st_mtime)))

        # Sort by date (newest first)
        filtered_files.sort(key=lambda x: x[1], reverse=True)
        result = [f for f, _ in filtered_files]

        logger.info(f"Found {len(result)} TXT files in {source_dir} (filtered from {len(txt_files)} total)")
        return result

    def process_file(self, file_path: Path) -> dict:
        """
        Process a single deal file.

        Returns:
            dict with processing stats
        """
        file_key = str(file_path)

        # Skip if already processed
        if file_key in self.processed_files:
            logger.info(f"Skipping already processed file: {file_path.name}")
            return {'deals_found': 0, 'deals_published': 0, 'deals_filtered': 0}

        logger.info(f"Processing file: {file_path.name}")

        try:
            # Parse deals from file
            deals = self.controller.parse_file(file_path)
            logger.info(f"Found {len(deals)} deals in {file_path.name}")

            # Enrich with Scrapula data before processing
            self.controller.enrich_deals_before_publish(deals)

            published_count = 0
            filtered_count = 0
            duplicate_count = 0
            published_deals = []

            for deal in deals:
                try:
                    # Check for duplicates first (use stated price if available)
                    if deal.asin and self.is_duplicate(deal.asin, deal.stated_price):
                        logger.info(f"⏭️  Skipping duplicate: {deal.title[:50]} (ASIN: {deal.asin})")
                        duplicate_count += 1
                        filtered_count += 1
                        continue

                    # Process the deal (validate price, etc.)
                    processed = self.controller.process_deal(deal, for_preview=False)

                    # Apply smart filtering
                    should_publish, reason = self.filter.should_publish(deal, processed)

                    if should_publish:
                        logger.info(f"✅ Publishing: {deal.title[:50]} - {reason}")
                        # Publish to WhatsApp
                        self.controller.publish_deal(processed, include_group=False)
                        published_count += 1
                        published_deals.append({
                            'title': deal.title,  # Full title
                            'title_en': deal.title_en or deal.title,  # Full English title
                            'asin': deal.asin,
                            'price': processed.price_info.current_price if processed.price_info else deal.stated_price
                        })
                    else:
                        logger.info(f"⏭️  Filtering out: {deal.title[:50]} - {reason}")
                        filtered_count += 1

                except Exception as e:
                    logger.error(f"Error processing deal {deal.title[:50]}: {e}", exc_info=True)
                    error_msg = f"{deal.title[:30]}: {str(e)[:50]}"
                    self.stats['errors'].append(error_msg)
                    filtered_count += 1

                    # Send immediate error notification for critical errors
                    if "PA-API" not in str(e):  # Don't spam for PA-API errors (expected)
                        self.send_status_update(
                            f"⚠️ Error Processing Deal\n\n"
                            f"Deal: {deal.title[:50]}\n"
                            f"Error: {str(e)[:100]}\n"
                            f"Time: {datetime.now().strftime('%H:%M')}"
                        )

                # Small delay between deals to avoid rate limits
                time.sleep(2)

            # Mark file as processed
            self.processed_files.add(file_key)

            return {
                'deals_found': len(deals),
                'deals_published': published_count,
                'deals_filtered': filtered_count,
                'duplicates_skipped': duplicate_count,
                'published_deals': published_deals
            }

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
            self.stats['errors'].append(f"File {file_path.name}: {str(e)[:50]}")
            return {'deals_found': 0, 'deals_published': 0, 'deals_filtered': 0}

    def send_status_update(self, message: str):
        """Send status update to personal WhatsApp number."""
        try:
            # Send to personal number for status updates, fallback to channel if not configured
            status_recipient = self.config.get("whatsapp", {}).get("recipients", {}).get("status")
            if not status_recipient:
                status_recipient = self.config.get("whatsapp", {}).get("recipients", {}).get("channel")

            recipients = [status_recipient]
            if recipients[0]:
                logger.info(f"Sending status update: {message}")
                self.whapi.send_message(
                    recipients,
                    message,
                    deal_id="status_update",
                    image_url=None
                )
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")

    def is_duplicate(self, asin: str, current_price: Optional[float] = None) -> bool:
        """
        Check if deal with this ASIN has already been published recently.

        Args:
            asin: Product ASIN to check
            current_price: Current price (optional) - if significantly different from last published price, not considered duplicate

        Returns:
            True if duplicate (same ASIN published recently at similar price), False otherwise
        """
        try:
            from datetime import datetime, timedelta

            cursor = self.controller.db.conn.cursor()

            # Check for deals published in the last 7 days
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()

            cursor.execute(
                """SELECT deal_id, adjusted_price, created_at
                   FROM deals
                   WHERE asin = ? AND status = 'published' AND created_at > ?
                   ORDER BY created_at DESC
                   LIMIT 1""",
                (asin, cutoff_date)
            )
            result = cursor.fetchone()

            if result is None:
                return False

            # If we have the current price, check if it's significantly different
            if current_price and result[1]:  # result[1] is adjusted_price
                previous_price = float(result[1])
                price_diff_pct = abs(current_price - previous_price) / previous_price * 100

                # If price changed by more than 10%, consider it a new deal
                if price_diff_pct > 10:
                    logger.info(f"Same ASIN {asin} but price changed significantly: €{previous_price} -> €{current_price} ({price_diff_pct:.1f}%)")
                    return False

            # Same ASIN, recently published, similar price = duplicate
            logger.info(f"Duplicate detected: {asin} (last published: {result[2]})")
            return True

        except Exception as e:
            logger.error(f"Error checking duplicate for {asin}: {e}")
            return False

    def run_once(self, source_dir: Optional[Path] = None) -> dict:
        """
        Run a single processing cycle.

        Args:
            source_dir: Directory to process (uses config default if not specified)

        Returns:
            dict with processing stats
        """
        if source_dir is None:
            source_dir = Path(self.config.get("default_source_dir", "."))

        logger.info("="*60)
        logger.info(f"Starting deal processing cycle at {datetime.now()}")
        logger.info("="*60)

        # Reset error list for this run
        self.stats['errors'] = []

        # Find deal files (look for files from last 24 hours)
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=24)

        deal_files = self.find_latest_deal_files(source_dir, since=cutoff_time)

        if not deal_files:
            logger.info("No new deal files found")
            self.send_status_update(
                f"🤖 DealBot Status Update\n\n"
                f"✅ System running normally\n"
                f"📁 No new deals found\n"
                f"🕐 Checked at {datetime.now().strftime('%H:%M')} CET"
            )
            return self.stats

        # Process each file
        total_found = 0
        total_published = 0
        total_filtered = 0
        total_duplicates = 0
        all_published_deals = []

        for file_path in deal_files[:5]:  # Limit to 5 most recent files per run
            result = self.process_file(file_path)
            total_found += result['deals_found']
            total_published += result['deals_published']
            total_filtered += result['deals_filtered']
            total_duplicates += result.get('duplicates_skipped', 0)
            all_published_deals.extend(result.get('published_deals', []))

        # Update stats
        self.stats['files_processed'] += len(deal_files[:5])
        self.stats['deals_found'] += total_found
        self.stats['deals_published'] += total_published
        self.stats['deals_filtered'] += total_filtered
        self.stats['last_run'] = datetime.now()

        # Send detailed status update
        status_msg = (
            f"🤖 DealBot Status - {datetime.now().strftime('%H:%M')} CET\n\n"
            f"✅ Processing Complete\n"
            f"📁 Files: {len(deal_files[:5])}\n"
            f"🔍 Found: {total_found} deals\n"
            f"📤 Published: {total_published}\n"
            f"🔁 Duplicates: {total_duplicates}\n"
            f"⏭️  Filtered: {total_filtered - total_duplicates}\n"
        )

        # Add all published deal names
        if all_published_deals:
            status_msg += f"\n📦 Published Deals (Full English Listings):\n"
            for i, deal in enumerate(all_published_deals, 1):
                # Show full English title (no truncation)
                english_title = deal.get('title_en') or deal.get('title')
                status_msg += f"{i}. {english_title} - €{deal['price']}\n"

        if self.stats['errors']:
            status_msg += f"\n⚠️ Errors: {len(self.stats['errors'])}"
            for error in self.stats['errors'][:3]:
                status_msg += f"\n  • {error}"

        self.send_status_update(status_msg)

        logger.info("="*60)
        logger.info(f"Processing cycle complete: {total_published} deals published")
        logger.info("="*60)

        return self.stats

    def send_daily_summary(self):
        """
        Query today's top 3 published deals and send a single summary post
        to the configured daily-summary WhatsApp group.
        """
        from .ui.whatsapp_format import WhatsAppFormatter

        summary_jid = self.config.get("whatsapp", {}).get("recipients", {}).get("daily_summary")
        if not summary_jid:
            logger.warning("No daily_summary JID configured — skipping summary")
            return

        top_deals = self.controller.db.get_top_deals_today(limit=3)

        if not top_deals:
            logger.info("No published deals in the last 24 h — skipping daily summary")
            return

        message = WhatsAppFormatter.format_daily_summary(top_deals)
        logger.info(f"Sending daily summary ({len(top_deals)} deals) to {summary_jid}")
        self.whapi.send_message(
            [summary_jid],
            message,
            deal_id="daily_summary",
            image_url=None,
        )
        logger.info("Daily summary sent successfully")

    def shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down daemon...")
        self.controller.shutdown()
