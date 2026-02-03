"""DealBot Toga GUI application."""

import asyncio
import threading
import webbrowser
from pathlib import Path
from typing import Optional

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from .controller import DealController
from .models import Deal, ProcessedDeal
from .utils.config import Config
from .utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


class DealBot(toga.App):
    """Main DealBot application."""

    def __init__(self) -> None:
        """Initialize DealBot app."""
        super().__init__(
            "DealBot",
            "com.dealbot.app",
        )

    def startup(self) -> None:
        """Construct and show the Toga application."""
        # Initialize logging
        setup_logging()
        logger.info("="*50)
        logger.info("STARTUP: Starting DealBot...")
        logger.info("="*50)

        # Load configuration
        try:
            logger.info("STARTUP: Loading configuration...")
            self.config = Config()
            logger.info("STARTUP: Configuration loaded successfully")
        except Exception as e:
            logger.error(f"STARTUP: Configuration error: {e}", exc_info=True)
            self.main_window = toga.MainWindow(title=self.formal_name)
            self.main_window.content = toga.Box(
                children=[
                    toga.Label(
                        f"Configuration Error: {e}\nPlease check config.yaml and .env",
                        style=Pack(padding=20),
                    )
                ]
            )
            logger.info("STARTUP: Showing error window...")
            self.main_window.show()
            logger.info("STARTUP: Calling _activate_window...")
            self._activate_window()
            logger.info("STARTUP: Error window setup complete")
            return

        # Initialize controller
        try:
            logger.info("STARTUP: Initializing controller...")
            self.controller = DealController(self.config)
            logger.info("STARTUP: Controller initialized successfully")
        except Exception as e:
            logger.error(f"STARTUP: Controller error: {e}", exc_info=True)
            self.main_window = toga.MainWindow(title=self.formal_name)
            self.main_window.content = toga.Box(
                children=[
                    toga.Label(
                        f"Controller Error: {e}\nPlease check API keys in .env",
                        style=Pack(padding=20),
                    )
                ]
            )
            logger.info("STARTUP: Showing controller error window...")
            self.main_window.show()
            logger.info("STARTUP: Calling _activate_window...")
            self._activate_window()
            logger.info("STARTUP: Controller error window setup complete")
            return

        # State
        self.current_deals: list[Deal] = []
        self.processed_deals: list[ProcessedDeal] = []
        self.publish_overrides: dict[str, bool] = {}  # ASIN -> should publish

        # Build UI
        self.main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # Header
        header = toga.Label(
            "DealBot - Amazon Deal Publisher",
            style=Pack(padding=(0, 0, 10, 0), font_size=18, font_weight="bold"),
        )
        self.main_box.add(header)

        # File selection
        file_box = toga.Box(style=Pack(direction=ROW, padding=5))
        self.file_label = toga.Label(
            "No file selected", style=Pack(padding_right=10, flex=1)
        )
        select_btn = toga.Button(
            "Select TXT File",
            on_press=self.select_file,
            style=Pack(padding=5),
        )
        file_box.add(self.file_label)
        file_box.add(select_btn)
        self.main_box.add(file_box)

        # Help text for preview features
        help_text = toga.Label(
            "💡 Select rows → Toggle to override publish decision • Status: ✅ Ready | ⚠️ Price Check | ❌ Out of Stock | 🔁 Duplicate (48h)",
            style=Pack(padding=5, font_size=10),
        )
        self.main_box.add(help_text)

        # Deals table with enhanced preview columns
        self.deals_table = toga.Table(
            headings=[
                "Select", "Title", "ASIN", "Price", "PVP", "Discount", 
                "Rating", "Stock", "Status"
            ],
            style=Pack(flex=1, padding=5),
            on_select=self.on_deal_selected,
            # Note: on_double_click not supported by Toga - removed
            multiple_select=True,
        )
        self.main_box.add(self.deals_table)

        # Options
        options_box = toga.Box(style=Pack(direction=ROW, padding=5))
        self.send_to_group_switch = toga.Switch(
            "Send to Group",
            value=self.config.send_to_group,
            on_change=self.toggle_group,
            style=Pack(padding=5),
        )
        options_box.add(self.send_to_group_switch)
        self.main_box.add(options_box)

        # Action buttons
        button_box = toga.Box(style=Pack(direction=ROW, padding=5))
        
        clear_btn = toga.Button(
            "Clear Deals",
            on_press=self.clear_deals,
            style=Pack(padding=5, flex=1),
        )
        button_box.add(clear_btn)
        
        toggle_btn = toga.Button(
            "Toggle Selected (Override)",
            on_press=self.toggle_selected_deals,
            style=Pack(padding=5, flex=1),
        )
        button_box.add(toggle_btn)
        
        publish_btn = toga.Button(
            "Publish Marked Deals",
            on_press=self.publish_deals,
            style=Pack(padding=5, flex=1),
        )
        button_box.add(publish_btn)
        self.main_box.add(button_box)

        # Status log
        status_label = toga.Label(
            "Status Log:",
            style=Pack(padding=(10, 0, 5, 0), font_weight="bold"),
        )
        self.main_box.add(status_label)

        self.status_log = toga.MultilineTextInput(
            readonly=True,
            style=Pack(height=150, padding=5),
        )
        self.main_box.add(self.status_log)

        # Create main window
        logger.info("STARTUP: Creating main window...")
        self.main_window = toga.MainWindow(title=self.formal_name)
        logger.info("STARTUP: Setting window content...")
        self.main_window.content = self.main_box

        # Create menu
        logger.info("STARTUP: Creating menu...")
        self._create_menu()

        # Show window and bring to front
        logger.info("STARTUP: Showing main window...")
        self.main_window.show()
        logger.info("STARTUP: Calling _activate_window...")
        self._activate_window()
        logger.info("STARTUP: Window activation complete")
        logger.info("STARTUP: Startup sequence complete!")
        logger.info("="*50)
        self.log_status("DealBot ready. Select a TXT file to begin.")

    def _activate_window(self) -> None:
        """Bring app window to foreground (macOS specific)."""
        try:
            import subprocess
            subprocess.run(
                ['osascript', '-e', 'tell application "DealBot" to activate'],
                check=False,
                capture_output=True,
                timeout=2
            )
        except Exception:
            pass  # Silently fail if activation doesn't work

    def _create_menu(self) -> None:
        """Create application menu."""
        # File menu
        file_menu = toga.Group("File")
        self.commands.add(
            toga.Command(
                self.select_file,
                "Open TXT File",
                shortcut=toga.Key.MOD_1 + "o",
                group=file_menu,
            ),
            toga.Command(
                self.export_csv,
                "Export to CSV",
                shortcut=toga.Key.MOD_1 + "e",
                group=file_menu,
            ),
        )

        # Tools menu
        tools_menu = toga.Group("Tools")
        self.commands.add(
            toga.Command(
                self.open_database,
                "Open Database",
                group=tools_menu,
            ),
            toga.Command(
                self.edit_config,
                "Edit Configuration",
                group=tools_menu,
            ),
        )

    def select_file(self, widget: Optional[toga.Widget] = None) -> None:
        """Open file picker for TXT file selection."""
        try:
            default_path = Path(self.config.default_source_dir)
            if not default_path.exists():
                default_path = Path.home()

            self.main_window.open_file_dialog(
                "Select Deal TXT File",
                initial_directory=default_path,
                file_types=["txt"],
                on_result=self.on_file_selected,
            )
        except Exception as e:
            self.log_status(f"Error opening file dialog: {e}")

    def on_file_selected(self, widget: toga.Window, path: Optional[Path]) -> None:
        """Handle file selection."""
        if not path:
            return

        self.log_status(f"📂 Loading file: {path.name}")
        self.file_label.text = f"⏳ Processing: {path.name}"

        # Parse and process deals for preview in background thread
        def parse_worker() -> None:
            try:
                # Parse the file
                self.current_deals = self.controller.parse_file(path)
                
                # Log to console (not UI) from background thread
                logger.info(f"Parsed {len(self.current_deals)} deals. Processing for preview...")
                
                # Update UI from main thread
                self.main_window.app.add_background_task(
                    lambda w: self.log_status(f"Parsed {len(self.current_deals)} deals. Processing...")
                )
                
                # Process each deal to get price, stock, rating info for preview
                self.processed_deals = []
                duplicates_found = 0
                
                for i, deal in enumerate(self.current_deals, 1):
                    try:
                        # Check if this ASIN was recently published (within 48h)
                        recent = self.controller.db.was_recently_published(deal.asin, hours=48) if deal.asin else None
                        
                        if recent:
                            duplicates_found += 1
                            logger.info(f"⚠️ Duplicate found: {deal.asin} was published {recent['published_at']}")
                        
                        processed = self.controller.process_deal(deal)
                        
                        # Mark as duplicate if recently published
                        if recent:
                            processed.is_duplicate = True
                            processed.last_published = recent['published_at']
                        
                        self.processed_deals.append(processed)
                        
                        # Log progress to console
                        logger.info(f"Processed {i}/{len(self.current_deals)}: {deal.title[:40]}")
                        
                        # Update UI periodically (every deal)
                        title_preview = deal.title[:40]
                        self.main_window.app.add_background_task(
                            lambda w, idx=i, total=len(self.current_deals), t=title_preview: 
                                self.log_status(f"Processing {idx}/{total}: {t}...")
                        )
                    except Exception as e:
                        logger.error(f"Error processing deal {deal.asin}: {e}")
                        error_msg = f"Error: {deal.asin}: {str(e)}"
                        self.main_window.app.add_background_task(
                            lambda w, msg=error_msg: self.log_status(msg)
                        )
                
                # Log duplicates summary
                if duplicates_found > 0:
                    dup_msg = f"⚠️ Found {duplicates_found} duplicate(s) published within 48h"
                    logger.warning(dup_msg)
                    self.main_window.app.add_background_task(
                        lambda w, msg=dup_msg: self.log_status(msg)
                    )
                
                # Update table with processed deals (from main thread)
                self.main_window.app.add_background_task(self._update_table_with_preview)
                
            except Exception as e:
                logger.error(f"Failed to parse file: {e}")
                error_msg = f"Error parsing file: {str(e)}"
                self.main_window.app.add_background_task(
                    lambda w, msg=error_msg: self.log_status(msg)
                )

        threading.Thread(target=parse_worker, daemon=True).start()

    def _update_table(self, widget: Optional[toga.Widget] = None) -> None:
        """Update deals table with parsed deals (legacy method)."""
        self._update_table_with_preview(widget)

    def _update_table_with_preview(self, widget: Optional[toga.Widget] = None) -> None:
        """Update deals table with full preview information."""
        self.deals_table.data.clear()
        
        # Update file label to show completion
        if hasattr(self, 'file_label') and self.processed_deals:
            filename = self.file_label.text.replace("⏳ Processing: ", "")
            self.file_label.text = f"✅ {filename}"

        for processed in self.processed_deals:
            # Extract info from processed deal
            price_info = processed.price_info
            deal = processed.deal
            
            # Format price
            price_str = f"€{processed.adjusted_price:.2f}" if processed.adjusted_price else "N/A"
            
            # Format PVP (original price)
            pvp_str = f"€{price_info.list_price:.2f}" if price_info and price_info.list_price else "-"
            
            # Format discount
            discount_str = f"-{price_info.savings_percentage:.0f}%" if price_info and price_info.savings_percentage else "-"
            
            # Format rating
            if price_info and price_info.review_rating:
                rating_str = f"⭐{price_info.review_rating:.1f} ({price_info.review_count or 0})"
            else:
                rating_str = "-"
            
            # Stock status
            if price_info:
                if price_info.availability == "Now":
                    stock_str = "✅ In Stock"
                elif not price_info.current_price:
                    stock_str = "❌ Out of Stock"
                elif price_info.availability:
                    stock_str = f"⚠️ {price_info.availability}"
                else:
                    stock_str = "❓ Unknown"
            else:
                stock_str = "❓ Unknown"
            
            # Status (check duplicate first)
            if processed.is_duplicate:
                status_str = "🔁 Duplicate (48h)"
            elif price_info and not price_info.current_price:
                status_str = "❌ Out of Stock"
            elif price_info and price_info.needs_review:
                # Price discrepancy warning
                status_str = "⚠️ Price Check"
            else:
                status_str = "✅ Ready"
            
            # Determine publish decision (with override support)
            asin = deal.asin
            if asin in self.publish_overrides:
                # User has manually overridden
                should_publish = self.publish_overrides[asin]
            else:
                # Auto-decision: only publish if in stock AND not a duplicate
                should_publish = bool(
                    price_info and 
                    price_info.current_price and 
                    price_info.availability == "Now" and
                    not processed.is_duplicate  # Skip duplicates
                )
            
            # Format select column
            select_str = "✅ Publish" if should_publish else "❌ Skip"
            
            self.deals_table.data.append(
                (
                    select_str,
                    deal.title[:45] + ("..." if len(deal.title) > 45 else ""),
                    deal.asin or "N/A",
                    price_str,
                    pvp_str,
                    discount_str,
                    rating_str,
                    stock_str,
                    status_str,
                )
            )

        self.log_status(f"Preview ready: {len(self.processed_deals)} deals processed")

    def on_deal_selected(self, table: toga.Table, row: Optional[object] = None) -> None:
        """Handle deal selection in table."""
        if row:
            self.log_status(f"Selected: {row.title if hasattr(row, 'title') else 'deal'}")

    def on_asin_double_click(self, table: toga.Table, row: Optional[object] = None) -> None:
        """Handle double-click on table row - open Amazon product page."""
        if not row:
            return
        
        # Extract ASIN from the row
        asin = row.asin if hasattr(row, 'asin') else None
        if not asin or asin == "N/A":
            self.log_status("⚠️ No ASIN available for this product")
            return
        
        # Build Amazon URL (default to .es, could be made configurable)
        amazon_url = f"https://www.amazon.es/dp/{asin}"
        
        try:
            webbrowser.open(amazon_url)
            self.log_status(f"🌐 Opened {asin} in browser")
        except Exception as e:
            self.log_status(f"❌ Failed to open browser: {e}")

    def clear_deals(self, widget: toga.Button) -> None:
        """Clear all loaded deals to allow loading a new file."""
        if not self.current_deals and not self.processed_deals:
            self.log_status("ℹ️ No deals to clear")
            return
        
        deal_count = len(self.current_deals) if self.current_deals else len(self.processed_deals)
        
        # Clear all state
        self.current_deals = []
        self.processed_deals = []
        self.publish_overrides = {}
        
        # Clear table
        self.deals_table.data.clear()
        
        # Reset file label
        self.file_label.text = "No file selected"
        
        self.log_status(f"🗑️ Cleared {deal_count} deal(s). Ready to load new file.")

    def toggle_selected_deals(self, widget: toga.Button) -> None:
        """Toggle publish decision for selected deals (user override)."""
        if not self.deals_table.selection:
            self.log_status("⚠️ No deals selected. Select rows to toggle.")
            return
        
        # Get selected rows (Toga returns a list-like selection object)
        try:
            selected_rows = list(self.deals_table.selection)
            if not selected_rows:
                self.log_status("⚠️ No deals selected.")
                return
            
            toggled_count = 0
            for row in selected_rows:
                # Find the deal by ASIN from the row
                asin = row.asin if hasattr(row, 'asin') else None
                if not asin or asin == "N/A":
                    continue
                
                # Find the processed deal
                matching_deal = next((d for d in self.processed_deals if d.deal.asin == asin), None)
                if not matching_deal:
                    continue
                
                # Toggle the override
                current_status = self.publish_overrides.get(asin)
                if current_status is None:
                    # No override yet - check auto-decision and flip it
                    price_info = matching_deal.price_info
                    auto_decision = bool(price_info and price_info.current_price and price_info.availability == "Now")
                    self.publish_overrides[asin] = not auto_decision
                else:
                    # Already overridden - flip it
                    self.publish_overrides[asin] = not current_status
                
                toggled_count += 1
                new_status = "✅ Publish" if self.publish_overrides[asin] else "❌ Skip"
                self.log_status(f"Toggled {asin}: {new_status}")
            
            # Refresh table to show changes
            self._update_table_with_preview()
            self.log_status(f"✅ Toggled {toggled_count} deal(s)")
            
        except Exception as e:
            logger.error(f"Error toggling deals: {e}")
            self.log_status(f"Error toggling deals: {e}")

    def toggle_group(self, widget: toga.Switch) -> None:
        """Toggle send to group setting."""
        self.config.set_send_to_group(widget.value)
        status = "enabled" if widget.value else "disabled"
        self.log_status(f"Send to group: {status}")

    def publish_deals(self, widget: toga.Button) -> None:
        """Publish deals marked for publishing (respects user overrides)."""
        if not self.processed_deals:
            self.log_status("No deals to publish. Please select a file first.")
            return

        # Filter deals based on "Select" column decision (with overrides)
        ready_deals = []
        for deal in self.processed_deals:
            asin = deal.deal.asin
            
            # Check if user has overridden the decision
            if asin in self.publish_overrides:
                should_publish = self.publish_overrides[asin]
            else:
                # Auto-decision: only publish if in stock
                should_publish = bool(
                    deal.price_info and 
                    deal.price_info.current_price and 
                    deal.price_info.availability == "Now"
                )
            
            if should_publish:
                ready_deals.append(deal)

        if not ready_deals:
            self.log_status("❌ No deals marked for publishing (all are ❌ Skip)")
            return

        skipped_count = len(self.processed_deals) - len(ready_deals)
        if skipped_count > 0:
            self.log_status(f"ℹ️ Publishing {len(ready_deals)}, skipping {skipped_count}")

        self.log_status(f"Publishing {len(ready_deals)} ready deals...")
        widget.enabled = False

        # Publish in background thread
        def publish_worker() -> None:
            try:
                include_group = self.send_to_group_switch.value
                published_count = 0
                
                for i, processed in enumerate(ready_deals, 1):
                    try:
                        # Publish the already-processed deal
                        result = self.controller.publish_deal(processed, include_group=include_group)
                        
                        if result.publish_result and result.publish_result.success:
                            published_count += 1
                            # Log to console from background thread
                            logger.info(f"✅ Published {i}/{len(ready_deals)}: {processed.deal.title[:40]}")
                            # Update UI from main thread
                            title_preview = processed.deal.title[:40]
                            self.main_window.app.add_background_task(
                                lambda w, idx=i, total=len(ready_deals), t=title_preview: 
                                    self.log_status(f"✅ Published {idx}/{total}: {t}...")
                            )
                        else:
                            error_msg = result.publish_result.error if result.publish_result else "Unknown error"
                            logger.error(f"❌ Failed {i}/{len(ready_deals)}: {error_msg}")
                            self.main_window.app.add_background_task(
                                lambda w, msg=error_msg: self.log_status(f"❌ Failed: {msg}")
                            )
                    except Exception as e:
                        logger.error(f"Error publishing deal {processed.deal.asin}: {e}")
                        error_text = f"❌ Error: {processed.deal.asin}: {str(e)}"
                        self.main_window.app.add_background_task(
                            lambda w, msg=error_text: self.log_status(msg)
                        )

                # Update UI in main thread
                self.main_window.app.add_background_task(
                    lambda w: self._on_publish_complete(widget, published_count, len(ready_deals))
                )
            except Exception as e:
                logger.error(f"Failed to publish deals: {e}")
                error_msg = f"Error publishing: {str(e)}"
                # Update UI from main thread
                self.main_window.app.add_background_task(
                    lambda w, msg=error_msg, btn=widget: self._on_publish_error(btn, msg)
                )

        threading.Thread(target=publish_worker, daemon=True).start()

    def _on_publish_error(self, button: toga.Button, error_msg: str) -> None:
        """Handle publish error."""
        self.log_status(error_msg)
        button.enabled = True

    def _on_publish_complete(self, button: toga.Button, published_count: int, total_ready: int) -> None:
        """Handle publish completion."""
        self.log_status(
            f"✅ Published {published_count}/{total_ready} ready deals successfully"
        )

        # Refresh table to show publish status
        self._update_table_with_preview()
        button.enabled = True

    def log_status(self, message: str) -> None:
        """Prepend message to status log (newest at top)."""
        current = self.status_log.value or ""
        self.status_log.value = message + "\n" + current
        logger.info(message)

    def export_csv(self, widget: toga.Widget) -> None:
        """Export deals database to CSV."""
        try:
            output_path = Path.home() / "dealbot_export.csv"
            self.controller.db.export_to_csv(output_path)
            self.log_status(f"Exported to: {output_path}")
        except Exception as e:
            self.log_status(f"Export error: {e}")

    def open_database(self, widget: toga.Widget) -> None:
        """Open database file in default application."""
        import subprocess

        try:
            db_path = self.controller.db.db_path
            subprocess.run(["open", str(db_path)], check=True)
        except Exception as e:
            self.log_status(f"Failed to open database: {e}")

    def edit_config(self, widget: toga.Widget) -> None:
        """Open config.yaml in default editor."""
        import subprocess

        try:
            subprocess.run(["open", "-e", "config.yaml"], check=True)
        except Exception as e:
            self.log_status(f"Failed to open config: {e}")


def main() -> DealBot:
    """Main entry point."""
    return DealBot()


if __name__ == "__main__":
    main().main_loop()
