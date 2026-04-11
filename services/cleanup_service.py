"""Cleanup service for managing data retention and storage optimization"""
from datetime import datetime, timedelta
from pathlib import Path
import shutil
from utils.logger import get_logger

logger = get_logger(__name__)


class CleanupService:
    """Service for cleaning up old data to optimize storage"""

    @staticmethod
    def cleanup_old_tickets(days_before: int = 30) -> dict:
        """
        Delete all tickets created more than N days ago

        Args:
            days_before: Delete tickets older than this many days (default: 30 days)

        Returns:
            Dict with cleanup statistics:
            {
                "deleted_count": int,
                "total_size_freed": int (bytes),
                "errors": [str],
                "status": "success" | "partial" | "failed"
            }
        """
        from services.ticket_service import TicketService

        try:
            logger.info(f"Starting cleanup of tickets older than {days_before} days...")

            deleted_count = 0
            total_size_freed = 0
            errors = []

            # Get all tickets
            all_tickets = TicketService.list_tickets()
            cutoff_date = datetime.now() - timedelta(days=days_before)

            logger.info(f"Found {len(all_tickets)} total tickets. Cutoff date: {cutoff_date}")

            for ticket in all_tickets:
                try:
                    ticket_id = ticket.get('ticket_id')
                    created_at_str = ticket.get('created_at')

                    if not created_at_str or not ticket_id:
                        continue

                    # Parse ISO format datetime
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse created_at for {ticket_id}: {created_at_str}")
                        continue

                    # Check if ticket is old enough to delete
                    if created_at < cutoff_date:
                        # Calculate size before deletion
                        ticket_dir = Path(__file__).parent.parent / "data" / "tickets" / ticket_id
                        size_to_free = 0

                        if ticket_dir.exists():
                            for file_path in ticket_dir.rglob('*'):
                                if file_path.is_file():
                                    size_to_free += file_path.stat().st_size

                        # Delete ticket
                        if TicketService.delete_ticket(ticket_id):
                            deleted_count += 1
                            total_size_freed += size_to_free
                            logger.info(
                                f"Deleted ticket {ticket_id} (created: {created_at}, freed: {size_to_free} bytes)"
                            )
                        else:
                            errors.append(f"Failed to delete ticket {ticket_id}")

                except Exception as e:
                    error_msg = f"Error processing ticket {ticket.get('ticket_id')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            status = "success" if not errors else ("partial" if deleted_count > 0 else "failed")

            result = {
                "deleted_count": deleted_count,
                "total_size_freed": total_size_freed,
                "total_size_freed_mb": round(total_size_freed / (1024 * 1024), 2),
                "errors": errors,
                "status": status,
            }

            logger.info(
                f"Ticket cleanup complete: {deleted_count} deleted, "
                f"{total_size_freed_mb}MB freed, {len(errors)} errors"
            )

            return result

        except Exception as e:
            logger.error(f"Error in cleanup_old_tickets: {e}", exc_info=True)
            return {
                "deleted_count": 0,
                "total_size_freed": 0,
                "total_size_freed_mb": 0,
                "errors": [str(e)],
                "status": "failed",
            }

    @staticmethod
    def cleanup_inactive_users(months_inactive: int = 4) -> dict:
        """
        Delete user registrations for users with no activity in N+ months

        Args:
            months_inactive: Delete users inactive for this many months (default: 4)

        Returns:
            Dict with cleanup statistics:
            {
                "deleted_users": [user_id],
                "tickets_deleted": int,
                "registrations_deleted": int,
                "errors": [str],
                "status": "success" | "partial" | "failed"
            }
        """
        from services.employee_service import EmployeeService
        from services.ticket_service import TicketService

        try:
            logger.info(f"Starting cleanup of users inactive for {months_inactive}+ months...")

            deleted_users = []
            tickets_deleted = 0
            errors = []

            # Get all registered users
            all_users = EmployeeService.get_all_employees()
            if not all_users:
                logger.info("No registered users found")
                return {
                    "deleted_users": [],
                    "tickets_deleted": 0,
                    "registrations_deleted": 0,
                    "errors": [],
                    "status": "success",
                }

            cutoff_date = datetime.now() - timedelta(days=30 * months_inactive)
            logger.info(f"Found {len(all_users)} registered users. Activity cutoff: {cutoff_date}")

            for user_info in all_users:
                try:
                    user_id = user_info.get('user_id')
                    user_email = user_info.get('email')

                    if not user_id or not user_email:
                        continue

                    # Get all tickets for this user
                    user_tickets = TicketService.get_tickets_by_user_email(user_email)

                    # Check if user has any recent activity (tickets within timeframe)
                    has_recent_activity = False

                    if user_tickets:
                        for ticket in user_tickets:
                            try:
                                created_at_str = ticket.get('created_at')
                                if created_at_str:
                                    created_at = datetime.fromisoformat(created_at_str)
                                    if created_at >= cutoff_date:
                                        has_recent_activity = True
                                        break
                            except (ValueError, TypeError):
                                continue

                    # If no recent activity found, delete user registration
                    if not has_recent_activity:
                        # Delete user registration
                        if EmployeeService.delete_user_registration(user_id):
                            deleted_users.append(user_id)
                            logger.info(f"Deleted registration for inactive user {user_id} ({user_email})")

                            # Also delete all their old tickets
                            if user_tickets:
                                for ticket in user_tickets:
                                    try:
                                        ticket_id = ticket.get('ticket_id')
                                        if TicketService.delete_ticket(ticket_id):
                                            tickets_deleted += 1
                                            logger.info(f"Deleted ticket {ticket_id} for deleted user {user_id}")
                                    except Exception as e:
                                        logger.warning(f"Could not delete ticket {ticket_id}: {e}")
                        else:
                            errors.append(f"Failed to delete registration for user {user_id}")

                except Exception as e:
                    error_msg = f"Error processing user {user_info.get('user_id')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            status = "success" if not errors else ("partial" if deleted_users else "failed")

            result = {
                "deleted_users": deleted_users,
                "tickets_deleted": tickets_deleted,
                "registrations_deleted": len(deleted_users),
                "errors": errors,
                "status": status,
            }

            logger.info(
                f"User cleanup complete: {len(deleted_users)} users deleted, "
                f"{tickets_deleted} tickets deleted, {len(errors)} errors"
            )

            return result

        except Exception as e:
            logger.error(f"Error in cleanup_inactive_users: {e}", exc_info=True)
            return {
                "deleted_users": [],
                "tickets_deleted": 0,
                "registrations_deleted": 0,
                "errors": [str(e)],
                "status": "failed",
            }

    @staticmethod
    def run_full_cleanup(
        delete_tickets_days: int = 30, delete_inactive_months: int = 4
    ) -> dict:
        """
        Run complete cleanup: old tickets + inactive users

        Args:
            delete_tickets_days: Days before which to delete tickets
            delete_inactive_months: Months of inactivity before deleting users

        Returns:
            Combined cleanup statistics
        """
        logger.info("=" * 60)
        logger.info("STARTING FULL CLEANUP CYCLE")
        logger.info("=" * 60)

        try:
            # Run ticket cleanup
            ticket_result = CleanupService.cleanup_old_tickets(delete_tickets_days)

            # Run user cleanup
            user_result = CleanupService.cleanup_inactive_users(delete_inactive_months)

            # Combined result
            combined = {
                "ticket_cleanup": ticket_result,
                "user_cleanup": user_result,
                "total_tickets_deleted": ticket_result.get("deleted_count", 0),
                "total_users_deleted": user_result.get("registrations_deleted", 0),
                "total_users_tickets_deleted": user_result.get("tickets_deleted", 0),
                "total_size_freed_mb": ticket_result.get("total_size_freed_mb", 0),
                "status": (
                    "success"
                    if ticket_result.get("status") == "success" and user_result.get("status") == "success"
                    else "partial"
                    if ticket_result.get("status") in ["success", "partial"]
                    and user_result.get("status") in ["success", "partial"]
                    else "failed"
                ),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info("=" * 60)
            logger.info(f"CLEANUP CYCLE COMPLETE - Status: {combined.get('status')}")
            logger.info(f"  Tickets deleted: {combined['total_tickets_deleted']}")
            logger.info(f"  Storage freed: {combined['total_size_freed_mb']}MB")
            logger.info(f"  Users deleted: {combined['total_users_deleted']}")
            logger.info(f"  User tickets deleted: {combined['total_users_tickets_deleted']}")
            logger.info("=" * 60)

            return combined

        except Exception as e:
            logger.error(f"Error in run_full_cleanup: {e}", exc_info=True)
            return {
                "ticket_cleanup": {"status": "failed", "errors": [str(e)]},
                "user_cleanup": {"status": "failed", "errors": [str(e)]},
                "status": "failed",
                "timestamp": datetime.now().isoformat(),
            }
