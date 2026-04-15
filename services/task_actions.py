"""Task action handlers for scheduled tasks"""
from datetime import datetime
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskActionExecutor:
    """Executes scheduled task actions"""

    @staticmethod
    async def execute(task) -> dict:
        """
        Execute a task based on its type

        Args:
            task: ScheduledTask object

        Returns:
            Result dictionary with status, message, and optional error
        """
        try:
            from models.scheduled_task import TaskType

            task_type = task.task_type

            if task_type == TaskType.SEND_MESSAGE:
                return await TaskActionExecutor.execute_send_message(task)
            elif task_type == TaskType.ESCALATE_TICKET:
                return await TaskActionExecutor.execute_escalate_ticket(task)
            elif task_type == TaskType.RUN_CLEANUP:
                return TaskActionExecutor.execute_run_cleanup(task)
            elif task_type == TaskType.SEND_REMINDER:
                return await TaskActionExecutor.execute_send_reminder(task)
            elif task_type == TaskType.GENERATE_REPORT:
                return TaskActionExecutor.execute_generate_report(task)
            elif task_type == TaskType.CREATE_TICKET:
                return await TaskActionExecutor.execute_create_ticket(task)
            else:
                return {"status": "failed", "error": f"Unknown task type: {task_type}"}

        except Exception as e:
            logger.error(f"Error executing task: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def execute_send_message(task) -> dict:
        """
        Send a message to a user

        Args:
            task: ScheduledTask with action_params:
                  - target_user_id: Telegram user ID
                  - message_text: Text to send

        Returns:
            Result dictionary
        """
        try:
            from telegram import Bot
            import os

            params = task.action_params
            target_user_id = params.get('target_user_id')
            message_text = params.get('message_text', '')

            if not target_user_id or not message_text:
                return {
                    "status": "failed",
                    "error": "Missing target_user_id or message_text"
                }

            # Get bot token from environment
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                return {
                    "status": "failed",
                    "error": "TELEGRAM_BOT_TOKEN not configured"
                }

            # Send message
            bot = Bot(token=bot_token)
            await bot.send_message(
                chat_id=target_user_id,
                text=message_text,
                parse_mode='HTML'
            )

            return {
                "status": "success",
                "message": f"Message sent to user {target_user_id}",
                "target_user_id": target_user_id
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def execute_escalate_ticket(task) -> dict:
        """
        Escalate a ticket (change priority/status)

        Args:
            task: ScheduledTask with action_params:
                  - ticket_id: Ticket ID to escalate
                  - new_priority: New priority level (optional)
                  - new_status: New status (optional)
                  - add_note: Note to add (optional)

        Returns:
            Result dictionary
        """
        try:
            from services.ticket_service import TicketService

            params = task.action_params
            ticket_id = params.get('ticket_id')

            if not ticket_id:
                return {
                    "status": "failed",
                    "error": "Missing ticket_id"
                }

            # Get ticket
            ticket = TicketService.get_ticket(ticket_id)
            if not ticket:
                return {
                    "status": "failed",
                    "error": f"Ticket {ticket_id} not found"
                }

            changes = []

            # Update priority if provided
            new_priority = params.get('new_priority')
            if new_priority and new_priority != ticket.get('priority'):
                ticket['priority'] = new_priority
                changes.append(f"priority: {ticket.get('priority')} → {new_priority}")

            # Update status if provided
            new_status = params.get('new_status')
            if new_status:
                TicketService.update_ticket_status(ticket_id, new_status, updated_by="scheduled_task")
                changes.append(f"status: {ticket.get('status')} → {new_status}")

            # Add note if provided
            note = params.get('add_note')
            if note:
                TicketService.add_reply(ticket_id, note, user_name="Scheduled Task")
                changes.append(f"note added: {note}")

            if not changes:
                return {
                    "status": "success",
                    "message": f"No changes needed for ticket {ticket_id}",
                    "ticket_id": ticket_id
                }

            return {
                "status": "success",
                "message": f"Ticket {ticket_id} escalated",
                "ticket_id": ticket_id,
                "changes": changes
            }

        except Exception as e:
            logger.error(f"Error escalating ticket: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    @staticmethod
    def execute_run_cleanup(task) -> dict:
        """
        Run data cleanup

        Args:
            task: ScheduledTask with action_params:
                  - days_threshold: Delete tickets older than N days (optional, default: 30)
                  - cleanup_type: 'tickets' or 'inactive_users' or 'full' (default: 'full')

        Returns:
            Result dictionary
        """
        try:
            from services.cleanup_service import CleanupService

            params = task.action_params
            days_threshold = params.get('days_threshold', 30)
            cleanup_type = params.get('cleanup_type', 'full')

            result = {}

            if cleanup_type in ('tickets', 'full'):
                cleanup_result = CleanupService.cleanup_old_tickets(days_threshold)
                result['tickets_cleanup'] = cleanup_result

            if cleanup_type in ('inactive_users', 'full'):
                inactive_months = params.get('inactive_months', 4)
                user_cleanup_result = CleanupService.cleanup_inactive_users(inactive_months)
                result['users_cleanup'] = user_cleanup_result

            return {
                "status": "success",
                "message": f"Cleanup completed ({cleanup_type})",
                "details": result
            }

        except Exception as e:
            logger.error(f"Error running cleanup: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def execute_send_reminder(task) -> dict:
        """
        Send a reminder message to admins or team

        Args:
            task: ScheduledTask with action_params:
                  - recipient_type: 'all_admins' or 'specific_user'
                  - target_user_id: User ID if specific_user
                  - message_title: Title of reminder
                  - message_body: Body of reminder

        Returns:
            Result dictionary
        """
        try:
            from telegram import Bot
            import os
            from handlers.admin import AdminHandlers

            params = task.action_params
            recipient_type = params.get('recipient_type', 'all_admins')
            message_title = params.get('message_title', 'Reminder')
            message_body = params.get('message_body', '')

            # Format message
            message_text = f"<b>📋 {message_title}</b>\n\n{message_body}"

            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                return {
                    "status": "failed",
                    "error": "TELEGRAM_BOT_TOKEN not configured"
                }

            bot = Bot(token=bot_token)
            sent_count = 0
            failed_users = []

            if recipient_type == 'all_admins':
                # Send to all authenticated admin sessions
                admin_user_ids = list(AdminHandlers.admin_sessions.keys())
                if not admin_user_ids:
                    logger.warning("No authenticated admin sessions found")
                    admin_user_ids = [int(os.getenv('DEFAULT_ADMIN_ID', '0'))]

            elif recipient_type == 'specific_user':
                target_user_id = params.get('target_user_id')
                if not target_user_id:
                    return {
                        "status": "failed",
                        "error": "target_user_id required for specific_user"
                    }
                admin_user_ids = [target_user_id]
            else:
                return {
                    "status": "failed",
                    "error": f"Unknown recipient_type: {recipient_type}"
                }

            # Send to each admin
            for user_id in admin_user_ids:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=message_text,
                        parse_mode='HTML'
                    )
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send reminder to {user_id}: {e}")
                    failed_users.append(user_id)

            return {
                "status": "success" if sent_count > 0 else "partial",
                "message": f"Reminder sent to {sent_count} recipient(s)",
                "sent_count": sent_count,
                "failed_users": failed_users
            }

        except Exception as e:
            logger.error(f"Error sending reminder: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    @staticmethod
    def execute_generate_report(task) -> dict:
        """
        Generate a report (ticket stats, etc.)

        Args:
            task: ScheduledTask with action_params:
                  - report_type: 'ticket_stats' or 'queue_status'
                  - include_details: bool (default: False)

        Returns:
            Result dictionary with report data
        """
        try:
            from services.ticket_service import TicketService
            from services.queue_service import QueueService
            from datetime import datetime, timedelta

            params = task.action_params
            report_type = params.get('report_type', 'ticket_stats')
            include_details = params.get('include_details', False)

            report_data = {
                "generated_at": datetime.now().isoformat(),
                "report_type": report_type
            }

            if report_type == 'ticket_stats':
                all_tickets = TicketService.list_tickets()

                # Calculate stats
                total_tickets = len(all_tickets)
                open_tickets = len([t for t in all_tickets if t.get('status') == 'open'])
                in_progress = len([t for t in all_tickets if t.get('status') == 'in_progress'])
                completed = len([t for t in all_tickets if t.get('status') == 'completed'])

                # Use high priority count
                high_priority = len([t for t in all_tickets if t.get('priority') == 'high'])

                # Department breakdown
                departments = {}
                for ticket in all_tickets:
                    dept = ticket.get('department', 'Unknown')
                    departments[dept] = departments.get(dept, 0) + 1

                report_data['summary'] = {
                    'total_tickets': total_tickets,
                    'open': open_tickets,
                    'in_progress': in_progress,
                    'completed': completed,
                    'high_priority': high_priority
                }

                if include_details:
                    report_data['details'] = {
                        'by_department': departments,
                        'by_priority': {
                            'high': high_priority,
                            'medium': len([t for t in all_tickets if t.get('priority') == 'medium']),
                            'low': len([t for t in all_tickets if t.get('priority') == 'low'])
                        }
                    }

            elif report_type == 'queue_status':
                try:
                    queue_data = QueueService.get_queue_stats()
                    report_data['queue'] = queue_data
                except Exception:
                    report_data['queue'] = {"status": "unavailable"}

            else:
                return {
                    "status": "failed",
                    "error": f"Unknown report_type: {report_type}"
                }

            return {
                "status": "success",
                "message": f"{report_type} report generated",
                "report": report_data
            }

        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    @staticmethod
    async def execute_create_ticket(task) -> dict:
        """
        Create a new ticket and send it to Spiceworks + send DM notification

        Args:
            task: ScheduledTask with action_params:
                  - name: Ticket creator name *
                  - email: Ticket creator email *
                  - department: Department *
                  - issue: Issue title *
                  - summary: Summary/title for Spiceworks (optional, uses issue if not provided)
                  - description: Issue description (optional)
                  - priority: Priority level (low/medium/high) (optional)
                  - user_id: Telegram user ID for DM notification (optional)

        Returns:
            Result dictionary with ticket_id if successful
        """
        try:
            from services.ticket_service import TicketService
            from services.spiceworks_service import SpiceworksService
            from telegram import Bot
            import os

            params = task.action_params

            # Validate required fields
            required_fields = ['name', 'email', 'department', 'issue']
            for field in required_fields:
                if not params.get(field):
                    return {
                        "status": "failed",
                        "error": f"Missing required field: {field}"
                    }

            # Create ticket data
            ticket_data = {
                'name': params.get('name'),
                'email': params.get('email'),
                'department': params.get('department'),
                'issue': params.get('summary', 'Support Request'),  # Use summary as issue title
                'description': params.get('issue'),  # Main problem becomes description
                'media_info': params.get('media_description', ''),
                'priority': params.get('priority', 'medium')
            }

            # Create ticket locally
            ticket_id = TicketService.create_ticket(ticket_data)
            logger.info(f"Created scheduled ticket {ticket_id}")

            # Build description with media info
            description = ticket_data['description']
            if ticket_data['media_info']:
                description += f"\n\n📎 {ticket_data['media_info']}"

            # Send to Spiceworks
            spice_result = SpiceworksService.send_ticket_to_spiceworks(
                ticket_data=ticket_data,
                ticket_id=ticket_id
            )

            # Send DM notification to user if user_id provided
            user_id = params.get('user_id')
            dm_result = None
            if user_id:
                try:
                    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                    if bot_token:
                        bot = Bot(token=bot_token)
                        message_text = (
                            f"🎟️ <b>Ticket Created: {ticket_id}</b>\n"
                            f"<b>Title:</b> {ticket_data['issue']}\n"
                            f"<b>Description:</b> {ticket_data['description']}\n"
                            f"<b>Department:</b> {ticket_data['department']}\n"
                            f"<b>Priority:</b> {ticket_data['priority']}\n"
                            f"<b>Status:</b> Created (pending review)"
                        )
                        await bot.send_message(
                            chat_id=user_id,
                            text=message_text,
                            parse_mode='HTML'
                        )
                        dm_result = "DM sent"
                        logger.info(f"Sent DM notification to user {user_id} for ticket {ticket_id}")
                    else:
                        logger.warning("TELEGRAM_BOT_TOKEN not configured for DM notification")
                except Exception as e:
                    logger.warning(f"Failed to send DM notification to user {user_id}: {e}")
                    dm_result = f"DM failed: {e}"

            if spice_result:
                result = {
                    "status": "success",
                    "message": f"Ticket {ticket_id} created and sent to Spiceworks",
                    "ticket_id": ticket_id
                }
                if dm_result:
                    result["dm_notification"] = dm_result
                return result
            else:
                result = {
                    "status": "partial",
                    "message": f"Ticket {ticket_id} created locally but Spiceworks submission failed",
                    "ticket_id": ticket_id
                }
                if dm_result:
                    result["dm_notification"] = dm_result
                return result

        except Exception as e:
            logger.error(f"Error creating scheduled ticket: {e}", exc_info=True)
            return {"status": "failed", "error": str(e)}
