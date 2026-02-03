"""Scheduler for running deal processing at specific times."""

import time
from datetime import datetime, timedelta
from typing import Callable

import pytz

from .utils.logging import get_logger

logger = get_logger(__name__)


class DealBotScheduler:
    """Scheduler for running deal processing at 6am and 6pm Spain time."""

    def __init__(self, task_func: Callable, timezone: str = "Europe/Madrid"):
        """
        Initialize scheduler.

        Args:
            task_func: Function to call at scheduled times
            timezone: Timezone for schedule (default: Spain/Madrid)
        """
        self.task_func = task_func
        self.timezone = pytz.timezone(timezone)
        self.schedule_times = [6, 18]  # 6am and 6pm
        self.last_run_date: dict[int, str] = {}  # Track last run for each hour

    def get_next_run_time(self) -> datetime:
        """Calculate the next scheduled run time."""
        now = datetime.now(self.timezone)
        today = now.date()

        # Check each scheduled time today
        for hour in self.schedule_times:
            scheduled_time = self.timezone.localize(
                datetime.combine(today, datetime.min.time()).replace(hour=hour)
            )

            # Check if this time hasn't passed yet and hasn't run today
            if scheduled_time > now:
                run_key = f"{today}_{hour}"
                if run_key not in self.last_run_date:
                    return scheduled_time

        # If all today's times have passed, schedule for first time tomorrow
        tomorrow = today + timedelta(days=1)
        next_scheduled = self.timezone.localize(
            datetime.combine(tomorrow, datetime.min.time()).replace(hour=self.schedule_times[0])
        )

        return next_scheduled

    def should_run_now(self) -> bool:
        """Check if we should run the task now."""
        now = datetime.now(self.timezone)
        current_hour = now.hour
        today = now.date()

        # Check if current hour matches a schedule time
        if current_hour in self.schedule_times:
            run_key = f"{today}_{current_hour}"

            # Check if we haven't run yet this hour today
            if run_key not in self.last_run_date:
                # Mark as run
                self.last_run_date[run_key] = now.isoformat()
                return True

        return False

    def run_forever(self):
        """Run the scheduler forever, executing tasks at scheduled times."""
        logger.info("="*60)
        logger.info("DealBot Scheduler Started")
        logger.info(f"Schedule: {', '.join([f'{h}:00' for h in self.schedule_times])} CET")
        logger.info("="*60)

        while True:
            try:
                if self.should_run_now():
                    logger.info(f"⏰ Scheduled run triggered at {datetime.now(self.timezone)}")
                    self.task_func()
                else:
                    next_run = self.get_next_run_time()
                    logger.debug(f"Next run scheduled for: {next_run}")

                # Check every minute
                time.sleep(60)

            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}", exc_info=True)
                # Continue running even if there's an error
                time.sleep(60)

    def run_once_now(self):
        """Run the task immediately (for testing)."""
        logger.info("▶️  Running task immediately (manual trigger)")
        try:
            self.task_func()
            logger.info("✅ Manual run completed")
        except Exception as e:
            logger.error(f"❌ Manual run failed: {e}", exc_info=True)
