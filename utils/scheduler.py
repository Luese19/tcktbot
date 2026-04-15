"""Scheduler for running automated tasks like cleanup"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.logger import get_logger

logger = get_logger(__name__)


class SchedulerManager:
    """Manages background scheduled tasks"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)  # Run as daemon thread
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
                func=self._safe_cleanup_wrapper,
                trigger=trigger,
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

    @staticmethod
    def _safe_cleanup_wrapper():
        """Wrapper to safely execute cleanup"""
        try:
            from services.cleanup_service import CleanupService
            CleanupService.run_full_cleanup()
        except Exception as e:
            logger.error(f"Error in scheduled cleanup: {e}", exc_info=True)

    def stop_scheduler(self) -> bool:
        """Stop the scheduler"""
        try:
            if self._is_running:
                self.scheduler.shutdown(wait=False)  # Non-blocking shutdown
                self._is_running = False
                logger.info("Scheduler stopped")
                return True
            return False
        except Exception as e:
            logger.warning(f"Error stopping scheduler: {e}")
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


class TaskManager:
    """Manages custom admin-scheduled tasks"""

    def __init__(self, scheduler: BackgroundScheduler):
        """
        Initialize task manager with an APScheduler instance

        Args:
            scheduler: BackgroundScheduler instance to use for scheduling
        """
        self.scheduler = scheduler
        self.tasks = {}  # Dict of task_id -> ScheduledTask
        self.task_counter = 0

    def add_task(self, task) -> str:
        """
        Add a new scheduled task

        Args:
            task: ScheduledTask object

        Returns:
            task_id of the created task
        """
        try:
            from bot.models.scheduled_task import ScheduleType, TaskStatus
            from apscheduler.triggers.cron import CronTrigger
            from datetime import datetime, timedelta

            if task.status != TaskStatus.ACTIVE:
                logger.warning(f"Task {task.task_id} is not active, not scheduling")
                self.tasks[task.task_id] = task
                return task.task_id

            # Calculate next run time based on schedule type
            if task.schedule_type == ScheduleType.ONCE:
                # scheduled_time is ISO format datetime string
                next_run = datetime.fromisoformat(task.schedule_config.get('datetime'))
                
                # Check if the scheduled time is in the past
                if next_run < datetime.now():
                    logger.warning(f"Task {task.task_id} scheduled for the past ({next_run}). Skipping...")
                    task.next_run = next_run  # Set it anyway for reference
                    self.tasks[task.task_id] = task
                    return task.task_id
                
                task.next_run = next_run  # Set next_run on the task object
                
                trigger = None  # Will be handled separately
                self.scheduler.add_job(
                    func=self._execute_task_wrapper,
                    args=[task.task_id],
                    trigger='date',
                    run_date=next_run,
                    id=f"task_{task.task_id}",
                    name=f"{task.task_type.value}: {task.task_id}",
                    max_instances=1,
                    misfire_grace_time=3600,
                    coalesce=True,
                )

            elif task.schedule_type == ScheduleType.CRON:
                # Cron expression
                cron_expr = task.schedule_config.get('expression')
                self.scheduler.add_job(
                    func=self._execute_task_wrapper,
                    args=[task.task_id],
                    trigger=CronTrigger.from_crontab(cron_expr),
                    id=f"task_{task.task_id}",
                    name=f"{task.task_type.value}: {task.task_id}",
                    max_instances=1,
                    misfire_grace_time=3600,
                    coalesce=False,  # Run all missed instances
                )

            elif task.schedule_type == ScheduleType.DAILY:
                # Daily at specific time HH:MM
                time_str = task.schedule_config.get('time', '09:00')
                hour, minute = map(int, time_str.split(':'))
                trigger = CronTrigger(hour=hour, minute=minute)
                self.scheduler.add_job(
                    func=self._execute_task_wrapper,
                    args=[task.task_id],
                    trigger=trigger,
                    id=f"task_{task.task_id}",
                    name=f"{task.task_type.value}: {task.task_id}",
                    max_instances=1,
                    misfire_grace_time=3600,
                    coalesce=False,
                )

            elif task.schedule_type == ScheduleType.WEEKLY:
                # Weekly on specific day and time
                day_of_week = task.schedule_config.get('day_of_week', 0)  # 0=Monday
                time_str = task.schedule_config.get('time', '09:00')
                hour, minute = map(int, time_str.split(':'))
                trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
                self.scheduler.add_job(
                    func=self._execute_task_wrapper,
                    args=[task.task_id],
                    trigger=trigger,
                    id=f"task_{task.task_id}",
                    name=f"{task.task_type.value}: {task.task_id}",
                    max_instances=1,
                    misfire_grace_time=3600,
                    coalesce=False,
                )

            elif task.schedule_type == ScheduleType.MONTHLY:
                # Monthly on specific day and time
                day = task.schedule_config.get('day', 1)
                time_str = task.schedule_config.get('time', '09:00')
                hour, minute = map(int, time_str.split(':'))
                trigger = CronTrigger(day=day, hour=hour, minute=minute)
                self.scheduler.add_job(
                    func=self._execute_task_wrapper,
                    args=[task.task_id],
                    trigger=trigger,
                    id=f"task_{task.task_id}",
                    name=f"{task.task_type.value}: {task.task_id}",
                    max_instances=1,
                    misfire_grace_time=3600,
                    coalesce=False,
                )

            elif task.schedule_type == ScheduleType.YEARLY:
                # Yearly on specific month, day, and time
                month = task.schedule_config.get('month', 1)
                day = task.schedule_config.get('day', 1)
                time_str = task.schedule_config.get('time', '09:00')
                hour, minute = map(int, time_str.split(':'))
                trigger = CronTrigger(month=month, day=day, hour=hour, minute=minute)
                self.scheduler.add_job(
                    func=self._execute_task_wrapper,
                    args=[task.task_id],
                    trigger=trigger,
                    id=f"task_{task.task_id}",
                    name=f"{task.task_type.value}: {task.task_id}",
                    max_instances=1,
                    misfire_grace_time=3600,
                    coalesce=False,
                )

            # Calculate next run time
            try:
                job = self.scheduler.get_job(f"task_{task.task_id}")
                if job:
                    task.next_run = job.next_run_time
            except Exception as e:
                logger.warning(f"Could not get next run time for task {task.task_id}: {e}")

            self.tasks[task.task_id] = task
            logger.info(f"Task {task.task_id} ({task.task_type.value}) scheduled successfully")
            return task.task_id

        except Exception as e:
            logger.error(f"Error adding task {task.task_id}: {e}", exc_info=True)
            raise

    def get_all_tasks(self) -> list:
        """Get all scheduled tasks"""
        return list(self.tasks.values())

    def get_task(self, task_id: str):
        """Get a specific task by ID"""
        return self.tasks.get(task_id)

    def update_task(self, task_id: str, updates: dict) -> bool:
        """
        Update a task (reschedule if needed)

        Args:
            task_id: Task ID to update
            updates: Dictionary with fields to update

        Returns:
            True if successful
        """
        try:
            from bot.models.scheduled_task import ScheduledTask
            from datetime import datetime

            if task_id not in self.tasks:
                logger.error(f"Task {task_id} not found")
                return False

            task = self.tasks[task_id]

            # Update fields
            for key, value in updates.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            task.updated_at = datetime.now()

            # Reschedule if schedule config changed
            try:
                self.scheduler.remove_job(f"task_{task_id}")
            except Exception:
                pass

            # Re-add with new schedule
            self.add_task(task)
            logger.info(f"Task {task_id} updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}", exc_info=True)
            return False

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task

        Args:
            task_id: Task ID to delete

        Returns:
            True if successful
        """
        try:
            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return False

            # Remove from scheduler
            try:
                self.scheduler.remove_job(f"task_{task_id}")
            except Exception as e:
                logger.warning(f"Could not remove job {task_id} from scheduler: {e}")

            # Remove from tasks dict
            del self.tasks[task_id]
            logger.info(f"Task {task_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}", exc_info=True)
            return False

    def pause_task(self, task_id: str) -> bool:
        """
        Pause a task (remove from scheduler but keep in memory)

        Args:
            task_id: Task ID to pause

        Returns:
            True if successful
        """
        try:
            from bot.models.scheduled_task import TaskStatus

            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return False

            task = self.tasks[task_id]
            task.status = TaskStatus.PAUSED

            # Remove from scheduler
            try:
                self.scheduler.remove_job(f"task_{task_id}")
            except Exception as e:
                logger.warning(f"Could not remove job {task_id} from scheduler: {e}")

            logger.info(f"Task {task_id} paused")
            return True

        except Exception as e:
            logger.error(f"Error pausing task {task_id}: {e}", exc_info=True)
            return False

    def resume_task(self, task_id: str) -> bool:
        """
        Resume a paused task

        Args:
            task_id: Task ID to resume

        Returns:
            True if successful
        """
        try:
            from bot.models.scheduled_task import TaskStatus

            if task_id not in self.tasks:
                logger.warning(f"Task {task_id} not found")
                return False

            task = self.tasks[task_id]
            task.status = TaskStatus.ACTIVE

            # Re-add to scheduler
            self.add_task(task)
            logger.info(f"Task {task_id} resumed")
            return True

        except Exception as e:
            logger.error(f"Error resuming task {task_id}: {e}", exc_info=True)
            return False

    def run_task_now(self, task_id: str) -> dict:
        """
        Manually trigger a task immediately

        Args:
            task_id: Task ID to run

        Returns:
            Result dictionary
        """
        try:
            if task_id not in self.tasks:
                logger.error(f"Task {task_id} not found")
                return {"status": "failed", "error": "Task not found"}

            task = self.tasks[task_id]
            return self._execute_task(task)

        except Exception as e:
            logger.error(f"Error running task {task_id}: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    def _execute_task_wrapper(self, task_id: str):
        """Wrapper for task execution (called by APScheduler)"""
        try:
            task = self.tasks.get(task_id)
            if task:
                self._execute_task(task)
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}", exc_info=True)

    def _execute_task(self, task) -> dict:
        """
        Execute a task and handle result

        Args:
            task: ScheduledTask object

        Returns:
            Result dictionary
        """
        try:
            from bot.services.task_actions import TaskActionExecutor
            from datetime import datetime
            import asyncio

            logger.info(f"Executing task {task.task_id} ({task.task_type.value})")

            # Execute the task action (handle async function in sync context)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running, create a task instead
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        result = loop.run_in_executor(pool, lambda: asyncio.run(TaskActionExecutor.execute(task)))
                        result = result.result()
                else:
                    result = asyncio.run(TaskActionExecutor.execute(task))
            except RuntimeError:
                # No event loop in current thread, create one
                result = asyncio.run(TaskActionExecutor.execute(task))

            # Log the execution
            task.add_execution_log(
                status=result.get('status', 'unknown'),
                error=result.get('error'),
                result=result
            )

            # Send notification to admins
            try:
                self._send_task_notification(task, result)
            except Exception as e:
                logger.warning(f"Could not send task notification: {e}")

            logger.info(f"Task {task.task_id} executed with status: {result.get('status')}")
            return result

        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}", exc_info=True)
            error_result = {"status": "failed", "error": str(e)}
            task.add_execution_log(status="failed", error=str(e))
            try:
                self._send_task_notification(task, error_result)
            except Exception as notify_error:
                logger.warning(f"Could not send error notification: {notify_error}")
            return error_result

    @staticmethod
    def _send_task_notification(task, result: dict):
        """
        Send a Telegram notification to all admins about task execution

        Args:
            task: ScheduledTask that executed
            result: Execution result dictionary
        """
        try:
            # This will be implemented in the main bot
            # For now, just log it
            status = result.get('status', 'unknown')
            logger.info(f"Task execution result: {task.task_id} - {status}")

        except Exception as e:
            logger.warning(f"Error sending task notification: {e}")

