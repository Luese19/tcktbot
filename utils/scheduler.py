"""Scheduler for running automated tasks like cleanup"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.logger import get_logger

logger = get_logger(__name__)


class SchedulerManager:
    """Manages background scheduled tasks"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self._is_running = False

    def start_cleanup_scheduler(
        self, day: int = 1, hour: int = 0, minute: int = 0
    ) -> bool:
        """
        Start the monthly cleanup scheduler

        Args:
            day: Day of month to run cleanup (default: 1st)
            hour: Hour in UTC (default: 0 = midnight)
            minute: Minute (default: 0)

        Returns:
            True if scheduler started successfully
        """
        try:
            from services.cleanup_service import CleanupService

            if self._is_running:
                logger.warning("Scheduler already running")
                return False

            # Add cleanup job - runs on 1st of each month at specified time
            trigger = CronTrigger(day=day, hour=hour, minute=minute)
            self.scheduler.add_job(
                CleanupService.run_full_cleanup,
                trigger,
                id="monthly_cleanup",
                name="Monthly Data Cleanup",
                max_instances=1,  # Prevent overlapping executions
                coalesce=True,  # Skip missed runs if scheduler was down
                misfire_grace_time=3600,  # Allow 1 hour grace period for missed jobs
            )

            # Start the scheduler
            self.scheduler.start()
            self._is_running = True

            logger.info(
                f"Cleanup scheduler started. Schedule: Day {day} at {hour:02d}:{minute:02d} UTC"
            )
            return True

        except Exception as e:
            logger.error(f"Error starting cleanup scheduler: {e}", exc_info=True)
            return False

    def stop_scheduler(self) -> bool:
        """Stop the scheduler"""
        try:
            if self._is_running and self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                self._is_running = False
                logger.info("Scheduler stopped")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}", exc_info=True)
            return False

    def trigger_cleanup_now(self) -> dict:
        """Manually trigger cleanup immediately (for testing/admin command)"""
        try:
            from services.cleanup_service import CleanupService

            logger.info("Manual cleanup triggered")
            result = CleanupService.run_full_cleanup()
            logger.info(f"Manual cleanup completed: {result.get('status')}")
            return result

        except Exception as e:
            logger.error(f"Error triggering manual cleanup: {e}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e),
            }

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._is_running and self.scheduler.running

    def get_jobs(self) -> list:
        """Get list of scheduled jobs"""
        try:
            return [(job.id, job.name, str(job.trigger)) for job in self.scheduler.get_jobs()]
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []
