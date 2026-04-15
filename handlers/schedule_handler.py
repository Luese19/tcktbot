"""Schedule task handler for admins"""
from typing import Union
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.ext import filters as tg_filters
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class ScheduleState:
    """Conversation states for scheduling"""
    TASK_TYPE = 1
    SCHEDULE_TYPE = 2
    SCHEDULE_DATE_TIME = 3
    CONFIRM_SCHEDULE = 4
    
    # Task-specific parameters
    TICKET_NAME = 10
    TICKET_EMAIL = 11
    TICKET_DEPT = 12
    TICKET_SUMMARY = 13
    TICKET_ISSUE = 14
    TICKET_MEDIA = 15  # Changed from TICKET_DESC to handle photos/files
    TICKET_PRIORITY = 16
    
    MESSAGE_TARGET = 20
    MESSAGE_TEXT = 21


class ScheduleHandler:
    """Handler for scheduling tasks"""
    
    # Admin user IDs - set these in .env or hardcode
    ADMIN_IDS = [123456789]  # Replace with actual admin IDs from .env

    @staticmethod
    async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the scheduling flow"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        import os
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
        
        if user_id not in admin_ids:
            await update.message.reply_text("❌ You don't have permission to schedule tasks. Contact your administrator.")
            return ConversationHandler.END
        
        # Initialize context data
        context.user_data['schedule'] = {
            'task_type': None,
            'schedule_type': None,
            'schedule_config': {},
            'action_params': {}
        }
        
        # Ask for task type
        keyboard = [
            [InlineKeyboardButton("📝 Create Ticket", callback_data="task_create_ticket")],
            [InlineKeyboardButton("💬 Send Message", callback_data="task_send_message")],
            [InlineKeyboardButton("❌ Cancel", callback_data="task_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🗓️ <b>Schedule a Task</b>\n\nWhat would you like to schedule?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return ScheduleState.TASK_TYPE

    @staticmethod
    async def select_task_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle task type selection"""
        query = update.callback_query
        await query.answer()
        
        task_type = query.data.replace('task_', '')
        
        if task_type == 'cancel':
            await query.edit_message_text("❌ Scheduling cancelled.")
            return ConversationHandler.END
        
        context.user_data['schedule']['task_type'] = task_type
        
        # Ask for schedule type
        keyboard = [
            [InlineKeyboardButton("🔔 One-time (specific date/time)", callback_data="sched_once")],
            [InlineKeyboardButton("📅 Daily (same time every day)", callback_data="sched_daily")],
            [InlineKeyboardButton("📆 Weekly (specific day)", callback_data="sched_weekly")],
            [InlineKeyboardButton("📊 Monthly (specific day)", callback_data="sched_monthly")],
            [InlineKeyboardButton("⏰ Custom Cron", callback_data="sched_cron")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"When should the task run?\n\nSelected: {task_type.replace('_', ' ').title()}",
            reply_markup=reply_markup
        )
        return ScheduleState.SCHEDULE_TYPE

    @staticmethod
    async def select_schedule_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle schedule type selection"""
        query = update.callback_query
        await query.answer()
        
        schedule_type = query.data.replace('sched_', '')
        context.user_data['schedule']['schedule_type'] = schedule_type
        
        task_type = context.user_data['schedule']['task_type']
        
        # Request schedule details
        if schedule_type == 'once':
            msg = "📅 <b>One-time Task</b>\n\nEnter the date and time (must be in the future):\n<code>YYYY-MM-DD HH:MM AM/PM</code>\n\nToday: <code>" + datetime.now().strftime('%Y-%m-%d') + "</code>\nExample: <code>2026-04-14 6:35 PM</code>"
        elif schedule_type == 'daily':
            msg = "⏰ <b>Daily Task</b>\n\nEnter the time:\n<code>HH:MM AM/PM</code>\n\nExample: <code>9:00 AM</code>"
        elif schedule_type == 'weekly':
            msg = "📅 <b>Weekly Task</b>\n\nEnter day (0=Mon, 1=Tue, ..., 6=Sun) and time:\n<code>D HH:MM AM/PM</code>\n\nExample: <code>1 10:00 AM</code> (Tuesday at 10:00 AM)"
        elif schedule_type == 'monthly':
            msg = "📊 <b>Monthly Task</b>\n\nEnter day of month (1-31) and time:\n<code>D HH:MM AM/PM</code>\n\nExample: <code>15 2:00 PM</code> (15th at 2:00 PM)"
        elif schedule_type == 'cron':
            msg = "⏰ <b>Custom Cron Expression</b>\n\nEnter cron expression:\n<code>M H D M D</code>\n\nExample: <code>0 9 * * 1</code> (Every Monday at 9:00 AM)"
        
        await query.edit_message_text(msg, parse_mode='HTML')
        return ScheduleState.SCHEDULE_DATE_TIME

    @staticmethod
    async def collect_schedule_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect schedule date/time"""
        schedule_type = context.user_data['schedule']['schedule_type']
        user_input = update.message.text.strip()
        
        try:
            if schedule_type == 'once':
                # Parse: YYYY-MM-DD HH:MM AM/PM
                dt = datetime.strptime(user_input, '%Y-%m-%d %I:%M %p')
                
                # Check if the scheduled time is in the past
                if dt < datetime.now():
                    await update.message.reply_text(
                        f"❌ The scheduled time ({user_input}) is in the past!\n\n"
                        f"Please enter a future date and time in format: <code>YYYY-MM-DD HH:MM AM/PM</code>\n"
                        f"Example: <code>2026-04-14 6:35 PM</code>",
                        parse_mode='HTML'
                    )
                    return ScheduleState.SCHEDULE_DATE_TIME
                
                context.user_data['schedule']['schedule_config'] = {
                    'datetime': dt.isoformat()
                }
                time_str = dt.strftime('%B %d, %Y at %I:%M %p')
                confirm_msg = f"✅ Scheduled for: {time_str}"
                
            elif schedule_type == 'daily':
                # Parse: HH:MM AM/PM
                dt = datetime.strptime(user_input, '%I:%M %p')
                hour, minute = dt.hour, dt.minute
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    raise ValueError("Invalid time")
                context.user_data['schedule']['schedule_config'] = {
                    'time': f"{hour:02d}:{minute:02d}"
                }
                time_str = datetime.strptime(f"{hour:02d}:{minute:02d}", '%H:%M').strftime('%I:%M %p')
                confirm_msg = f"✅ Scheduled daily at: {time_str}"
                
            elif schedule_type == 'weekly':
                # Parse: D HH:MM AM/PM
                parts = user_input.split()
                day = int(parts[0])
                time_str = ' '.join(parts[1:])
                dt = datetime.strptime(time_str, '%I:%M %p')
                hour, minute = dt.hour, dt.minute
                
                if day < 0 or day > 6:
                    raise ValueError("Day must be 0-6")
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    raise ValueError("Invalid time")
                    
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                context.user_data['schedule']['schedule_config'] = {
                    'day_of_week': day,
                    'time': f"{hour:02d}:{minute:02d}"
                }
                dt = datetime.strptime(f"{hour:02d}:{minute:02d}", '%H:%M')
                time_str = dt.strftime('%I:%M %p')
                confirm_msg = f"✅ Scheduled every {days[day]} at {time_str}"
                
            elif schedule_type == 'monthly':
                # Parse: D HH:MM AM/PM
                parts = user_input.split()
                day = int(parts[0])
                time_str = ' '.join(parts[1:])
                dt = datetime.strptime(time_str, '%I:%M %p')
                hour, minute = dt.hour, dt.minute
                
                if day < 1 or day > 31:
                    raise ValueError("Day must be 1-31")
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    raise ValueError("Invalid time")
                    
                context.user_data['schedule']['schedule_config'] = {
                    'day': day,
                    'time': f"{hour:02d}:{minute:02d}"
                }
                dt = datetime.strptime(f"{hour:02d}:{minute:02d}", '%H:%M')
                time_str = dt.strftime('%I:%M %p')
                confirm_msg = f"✅ Scheduled on day {day} at {time_str}"
                
            elif schedule_type == 'cron':
                # Validate basic cron format
                parts = user_input.strip().split()
                if len(parts) != 5:
                    raise ValueError("Cron must have 5 parts: M H D M D")
                context.user_data['schedule']['schedule_config'] = {
                    'expression': user_input
                }
                confirm_msg = f"✅ Cron expression: {user_input}"
            
            await update.message.reply_text(confirm_msg)
            
            # Now collect task-specific parameters
            task_type = context.user_data['schedule']['task_type']
            if task_type == 'create_ticket':
                await update.message.reply_text(
                    "📝 <b>Ticket Details</b>\n\nEnter the creator's name:",
                    parse_mode='HTML'
                )
                return ScheduleState.TICKET_NAME
            elif task_type == 'send_message':
                await update.message.reply_text(
                    "💬 <b>Message Details</b>\n\nEnter target user ID:",
                    parse_mode='HTML'
                )
                return ScheduleState.MESSAGE_TARGET
                
        except Exception as e:
            await update.message.reply_text(f"❌ Invalid format: {str(e)}\n\nTry again.")
            return ScheduleState.SCHEDULE_DATE_TIME

    # CREATE TICKET WORKFLOW
    @staticmethod
    async def ticket_collect_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect ticket creator name"""
        context.user_data['schedule']['action_params']['name'] = update.message.text
        await update.message.reply_text("📧 Enter the creator's email:")
        return ScheduleState.TICKET_EMAIL

    @staticmethod
    async def ticket_collect_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect ticket creator email"""
        context.user_data['schedule']['action_params']['email'] = update.message.text
        
        from config.departments import DEPARTMENTS
        depts = list(DEPARTMENTS.keys())
        
        keyboard = []
        for i in range(0, len(depts), 2):
            row = [InlineKeyboardButton(DEPARTMENTS[depts[i]], callback_data=f"dept_{depts[i]}")]
            if i + 1 < len(depts):
                row.append(InlineKeyboardButton(DEPARTMENTS[depts[i+1]], callback_data=f"dept_{depts[i+1]}"))
            keyboard.append(row)
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🏢 Select department:",
            reply_markup=reply_markup
        )
        return ScheduleState.TICKET_DEPT

    @staticmethod
    async def ticket_select_dept(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Select ticket department"""
        query = update.callback_query
        await query.answer()
        
        dept = query.data.replace('dept_', '')
        context.user_data['schedule']['action_params']['department'] = dept
        
        await query.edit_message_text("📋 Enter a brief summary/title for Spiceworks:")
        return ScheduleState.TICKET_SUMMARY

    @staticmethod
    async def ticket_collect_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect ticket summary"""
        context.user_data['schedule']['action_params']['summary'] = update.message.text
        await update.message.reply_text("🎯 Enter the main issue/problem:")
        return ScheduleState.TICKET_ISSUE
    
    @staticmethod
    async def ticket_collect_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect ticket issue"""
        context.user_data['schedule']['action_params']['issue'] = update.message.text
        await update.message.reply_text(
            "📸 <b>Optional: Upload Photos or Files</b>\n\n"
            "Send photos/files to attach to the ticket, or press /skip to continue:",
            parse_mode='HTML'
        )
        return ScheduleState.TICKET_MEDIA
    
    @staticmethod
    async def ticket_collect_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect ticket media (photos/files)"""
        # Handle file uploads
        if update.message.document:
            media_info = f"📄 File: {update.message.document.file_name}"
        elif update.message.photo:
            media_info = "🖼️ Photo(s) attached"
        elif update.message.text and update.message.text.lower() == '/skip':
            media_info = ""
        else:
            await update.message.reply_text("❌ Please send a photo/file or press /skip")
            return ScheduleState.TICKET_MEDIA
        
        context.user_data['schedule']['action_params']['media_description'] = media_info
        
        keyboard = [
            [InlineKeyboardButton("🔴 High", callback_data="priority_high")],
            [InlineKeyboardButton("🟡 Medium", callback_data="priority_medium")],
            [InlineKeyboardButton("🟢 Low", callback_data="priority_low")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("⚠️ Select priority:", reply_markup=reply_markup)
        return ScheduleState.TICKET_PRIORITY

    @staticmethod
    async def ticket_select_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Select ticket priority"""
        query = update.callback_query
        await query.answer()
        
        priority = query.data.replace('priority_', '')
        context.user_data['schedule']['action_params']['priority'] = priority
        
        # Add user_id for DM notification
        context.user_data['schedule']['action_params']['user_id'] = query.from_user.id
        
        await ScheduleHandler._confirm_schedule(query, context)
        return ScheduleState.CONFIRM_SCHEDULE

    # MESSAGE WORKFLOW
    @staticmethod
    async def message_collect_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect message target user ID"""
        try:
            user_id = int(update.message.text)
            context.user_data['schedule']['action_params']['target_user_id'] = user_id
            await update.message.reply_text("✍️ Enter the message text:")
            return ScheduleState.MESSAGE_TEXT
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Enter a number:")
            return ScheduleState.MESSAGE_TARGET

    @staticmethod
    async def message_collect_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Collect message text"""
        context.user_data['schedule']['action_params']['message_text'] = update.message.text
        await ScheduleHandler._confirm_schedule(update, context)
        return ScheduleState.CONFIRM_SCHEDULE

    # CONFIRMATION
    @staticmethod
    async def _confirm_schedule(update_or_query: Union[Update, object], context: ContextTypes.DEFAULT_TYPE):
        """Show confirmation before scheduling"""
        schedule = context.user_data['schedule']
        
        # Determine if it's an Update or CallbackQuery
        if hasattr(update_or_query, 'message'):
            message_obj = update_or_query.message
        else:
            message_obj = update_or_query
        
        # Build confirmation message
        msg = "📋 <b>Confirm Schedule</b>\n\n"
        msg += f"<b>Task Type:</b> {schedule['task_type'].replace('_', ' ').title()}\n"
        msg += f"<b>Schedule Type:</b> {schedule['schedule_type'].upper()}\n"
        
        if schedule['schedule_type'] == 'once':
            dt = datetime.fromisoformat(schedule['schedule_config']['datetime'])
            time_str = dt.strftime('%B %d, %Y at %I:%M %p')
            msg += f"<b>Date/Time:</b> {time_str}\n"
        elif schedule['schedule_type'] == 'daily':
            dt = datetime.strptime(schedule['schedule_config']['time'], '%H:%M')
            time_str = dt.strftime('%I:%M %p')
            msg += f"<b>Time:</b> {time_str} every day\n"
        elif schedule['schedule_type'] == 'weekly':
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day = schedule['schedule_config']['day_of_week']
            dt = datetime.strptime(schedule['schedule_config']['time'], '%H:%M')
            time_str = dt.strftime('%I:%M %p')
            msg += f"<b>Day/Time:</b> {days[day]} at {time_str}\n"
        elif schedule['schedule_type'] == 'monthly':
            dt = datetime.strptime(schedule['schedule_config']['time'], '%H:%M')
            time_str = dt.strftime('%I:%M %p')
            msg += f"<b>Day/Time:</b> Day {schedule['schedule_config']['day']} at {time_str}\n"
        elif schedule['schedule_type'] == 'cron':
            msg += f"<b>Cron:</b> {schedule['schedule_config']['expression']}\n"
        
        msg += f"\n<b>Details:</b>\n"
        for key, value in schedule['action_params'].items():
            if key != 'user_id':  # Don't show internal user_id
                msg += f"  • {key.replace('_', ' ').title()}: {value}\n"
        
        msg += "\n✅ Create this scheduled task?"
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm_yes")],
            [InlineKeyboardButton("❌ Cancel", callback_data="confirm_no")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message_obj.reply_text(msg, reply_markup=reply_markup, parse_mode='HTML')

    @staticmethod
    async def confirm_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Final confirmation"""
        query = update.callback_query
        await query.answer()
        
        if query.data == 'confirm_no':
            await query.edit_message_text("❌ Scheduling cancelled.")
            return ConversationHandler.END
        
        try:
            from utils.scheduler import TaskManager
            from models.scheduled_task import ScheduledTask, TaskType, ScheduleType, TaskStatus
            import uuid
            import os
            
            schedule = context.user_data['schedule']
            
            # Get task manager from bot context
            if 'task_manager' not in context.bot_data:
                # Task manager might not be initialized, create a message first
                await query.edit_message_text(
                    "⚠️ Task manager not initialized. Please restart the bot.",
                    parse_mode='HTML'
                )
                return ConversationHandler.END
            
            task_manager = context.bot_data['task_manager']
            
            # Create task object
            task = ScheduledTask(
                task_id=f"TASK-{uuid.uuid4().hex[:12]}",
                task_type=TaskType(schedule['task_type']),
                schedule_type=ScheduleType(schedule['schedule_type']),
                schedule_config=schedule['schedule_config'],
                action_params=schedule['action_params'],
                status=TaskStatus.ACTIVE
            )
            
            # Add task via task manager
            task_manager.add_task(task)
            
            msg = f"✅ <b>Task Scheduled Successfully!</b>\n\n"
            msg += f"<b>Task ID:</b> <code>{task.task_id}</code>\n"
            msg += f"<b>Type:</b> {schedule['task_type'].replace('_', ' ').title()}\n"
            msg += f"<b>Next Run:</b> {task.next_run.strftime('%B %d, %Y at %H:%M') if task.next_run else 'N/A'}\n"
            
            await query.edit_message_text(msg, parse_mode='HTML')
            logger.info(f"Task {task.task_id} scheduled by admin {query.from_user.id}")
            
        except Exception as e:
            logger.error(f"Error scheduling task: {e}", exc_info=True)
            await query.edit_message_text(f"❌ Error: {str(e)}", parse_mode='HTML')
        
        return ConversationHandler.END

    @staticmethod
    async def list_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all scheduled tasks"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        import os
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
        
        if user_id not in admin_ids:
            await update.message.reply_text("❌ You don't have permission to view tasks.")
            return
        
        try:
            if 'task_manager' not in context.bot_data:
                await update.message.reply_text("⚠️ Task manager not initialized.")
                return
            
            task_manager = context.bot_data['task_manager']
            tasks = task_manager.get_all_tasks()
            
            if not tasks:
                await update.message.reply_text("📭 No scheduled tasks found.")
                return
            
            msg = f"📋 <b>Scheduled Tasks ({len(tasks)})</b>\n\n"
            
            for task in tasks:
                status_emoji = "✅" if str(task.status) == "TaskStatus.ACTIVE" else "⏸️"
                msg += f"{status_emoji} <b>{task.task_id}</b>\n"
                msg += f"   Type: {task.task_type.value}\n"
                msg += f"   Schedule: {task.schedule_type.value}\n"
                if task.next_run:
                    msg += f"   Next Run: {task.next_run.strftime('%Y-%m-%d %H:%M')}\n"
                msg += f"   Status: {task.status.value}\n\n"
            
            msg += "\n💡 Use /delete [task_id] to remove a task"
            await update.message.reply_text(msg, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    @staticmethod
    async def delete_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete a scheduled task"""
        user_id = update.effective_user.id
        
        # Check if user is admin
        import os
        admin_ids_str = os.getenv('ADMIN_IDS', '')
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
        
        if user_id not in admin_ids:
            await update.message.reply_text("❌ You don't have permission to delete tasks.")
            return
        
        try:
            # Get task_id from command
            if not context.args or len(context.args) == 0:
                msg = ("🗑️ <b>Delete Scheduled Task</b>\n\n"
                       "Usage: <code>/delete TASK-abc123</code>\n\n"
                       "Use /tasks to get the task ID")
                await update.message.reply_text(msg, parse_mode='HTML')
                return
            
            task_id = context.args[0]
            
            if 'task_manager' not in context.bot_data:
                await update.message.reply_text("⚠️ Task manager not initialized.")
                return
            
            task_manager = context.bot_data['task_manager']
            
            # Check if task exists
            task = task_manager.get_task(task_id)
            if not task:
                await update.message.reply_text(f"❌ Task {task_id} not found.")
                return
            
            # Delete the task
            job_id = f"task_{task_id}"
            if task_manager.scheduler.get_job(job_id):
                task_manager.scheduler.remove_job(job_id)
            
            # Remove from tasks dict
            if task_id in task_manager.tasks:
                del task_manager.tasks[task_id]
            
            msg = f"✅ Task <code>{task_id}</code> deleted successfully!"
            await update.message.reply_text(msg, parse_mode='HTML')
            logger.info(f"Task {task_id} deleted by admin {user_id}")
            
        except Exception as e:
            logger.error(f"Error deleting task: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")


def get_schedule_handler() -> ConversationHandler:
    """Get the schedule conversation handler"""
    
    entry_points = [CommandHandler('schedule', ScheduleHandler.schedule_command)]
    
    states = {
        ScheduleState.TASK_TYPE: [
            CallbackQueryHandler(ScheduleHandler.select_task_type, pattern='^task_')
        ],
        ScheduleState.SCHEDULE_TYPE: [
            CallbackQueryHandler(ScheduleHandler.select_schedule_type, pattern='^sched_')
        ],
        ScheduleState.SCHEDULE_DATE_TIME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleHandler.collect_schedule_datetime)
        ],
        ScheduleState.TICKET_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleHandler.ticket_collect_name)
        ],
        ScheduleState.TICKET_EMAIL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleHandler.ticket_collect_email)
        ],
        ScheduleState.TICKET_DEPT: [
            CallbackQueryHandler(ScheduleHandler.ticket_select_dept, pattern='^dept_')
        ],
        ScheduleState.TICKET_SUMMARY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleHandler.ticket_collect_summary)
        ],
        ScheduleState.TICKET_ISSUE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleHandler.ticket_collect_issue)
        ],
        ScheduleState.TICKET_MEDIA: [
            MessageHandler(filters.ALL, ScheduleHandler.ticket_collect_media)
        ],
        ScheduleState.TICKET_PRIORITY: [
            CallbackQueryHandler(ScheduleHandler.ticket_select_priority, pattern='^priority_')
        ],
        ScheduleState.MESSAGE_TARGET: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleHandler.message_collect_target)
        ],
        ScheduleState.MESSAGE_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScheduleHandler.message_collect_text)
        ],
        ScheduleState.CONFIRM_SCHEDULE: [
            CallbackQueryHandler(ScheduleHandler.confirm_schedule, pattern='^confirm_')
        ]
    }
    
    fallbacks = [
        CommandHandler('cancel', lambda u, c: ConversationHandler.END),
        CommandHandler('tasks', ScheduleHandler.list_tasks_command),
        CommandHandler('delete', ScheduleHandler.delete_task_command)
    ]
    
    return ConversationHandler(
        entry_points=entry_points,
        states=states,
        fallbacks=fallbacks,
        per_user=True
    )
