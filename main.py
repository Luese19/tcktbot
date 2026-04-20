#!/usr/bin/env python3
"""Telegram Help Desk Bot - Main Entry Point"""

import sys
import os
import asyncio
from pathlib import Path

# Ensure this directory is first in sys.path for imports
_root_dir = str(Path(__file__).parent.resolve())
if _root_dir in sys.path:
    sys.path.remove(_root_dir)
sys.path.insert(0, _root_dir)

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from config.settings import settings
from utils.logger import setup_logging, get_logger
from handlers.conversation import get_conversation_handler

# Environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
COMPANY_NAME = os.environ.get("COMPANY_NAME")
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL")

class TelegramHelpDeskBot:
    """Main bot application class"""

    def __init__(self):
        if settings is None:
            raise RuntimeError("Configuration not loaded")

        self.logger = setup_logging(settings.app.LOG_LEVEL, settings.app.LOG_FILE_PATH)

        # Build application with message_reaction updates enabled
        self.application = Application.builder().token(settings.bot.TOKEN).build()

        # Enable message reaction updates
        self.application.post_init = self._post_init

        self.scheduler_manager = None  # Initialize after application is ready
        self._setup_handlers()

    async def _post_init(self, application: Application) -> None:
        """Initialize allowed_updates after application is built"""
        self.logger.info("Configuring allowed updates to include message reactions...")
        # This ensures the bot listens for message_reaction updates
        await application.bot.set_my_commands([])  # Sync commands
        self.logger.info("Message reactions enabled in polling")

    def _setup_handlers(self):
        """Setup bot handlers"""
        # Message cache handler - cache all group messages for reaction lookups
        async def cache_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Cache group messages for later retrieval when reactions occur"""
            if update.message and update.effective_chat.type in ["group", "supergroup"]:
                from services.message_cache_service import MessageCacheService
                message_text = update.message.text or update.message.caption or ""
                sender_name = update.message.from_user.full_name if update.message.from_user else "Unknown"

                if message_text:  # Only cache if there's text
                    MessageCacheService.store_message(
                        update.effective_chat.id,
                        update.message.message_id,
                        message_text,
                        sender_name
                    )
            return True

        from telegram.ext import TypeHandler
        self.application.add_handler(TypeHandler(Update, cache_group_messages), group=-99)
        self.logger.info("Message cache handler enabled")

        # Reaction handler FIRST with group -1 (highest priority)
        if settings.app.REACTION_TICKET_ENABLED:
            from handlers.reaction_handler import ReactionTicketHandler
            self.application.add_handler(ReactionTicketHandler.get_reaction_handler(), group=-1)
            self.logger.info("Reaction-based ticket creation handler configured")

        # Group mention handler with group 0 (highest priority)
        from handlers.mention_handler import GroupMentionHandler
        self.application.add_handler(GroupMentionHandler.get_mention_handler(), group=0)
        self.application.add_handler(GroupMentionHandler.get_media_mention_handler(), group=0)
        self.application.add_handler(GroupMentionHandler.get_confirmation_handler(), group=0)
        self.application.add_handler(GroupMentionHandler.get_welcome_handler(), group=0)
        self.logger.info("Group mention, media, confirmation, and welcome handlers configured (DIRECT mode with media support)")

        # Email registration handlers with group 1
        from handlers.email_registration import EmailRegistrationHandler
        self.application.add_handler(EmailRegistrationHandler.get_registration_handler(), group=1)
        self.application.add_handler(EmailRegistrationHandler.get_check_handler(), group=1)
        self.logger.info("Email registration handlers configured")

        # Conversation handler with group 2 (lower priority)
        self.application.add_handler(get_conversation_handler(), group=2)

        # Admin and lookup handlers with group 3
        from handlers.admin import get_lookup_handler, get_admin_handler, get_admin_command_handlers
        self.application.add_handler(get_lookup_handler(), group=3)
        self.application.add_handler(get_admin_handler(), group=3)
        for handler in get_admin_command_handlers():
            self.application.add_handler(handler, group=3)
        
        # Schedule handler with group 3 (admin only)
        from handlers.schedule_handler import get_schedule_handler, ScheduleHandler
        self.application.add_handler(get_schedule_handler(), group=3)
        self.application.add_handler(CommandHandler('tasks', ScheduleHandler.list_tasks_command), group=3)
        self.application.add_handler(CommandHandler('delete', ScheduleHandler.delete_task_command), group=3)
        self.logger.info("Schedule handler configured")

        # Group command handlers with group 3.5 (between admin and basic commands)
        from handlers.group_commands import get_group_command_handlers, get_group_help_handler, get_group_reply_handler
        for handler in get_group_command_handlers():
            self.application.add_handler(handler, group=3)
        self.application.add_handler(get_group_reply_handler(), group=2)  # Higher priority for reply detection
        self.logger.info("Group command handlers configured")

        # Command handlers with group 4
        self.application.add_handler(get_group_help_handler(), group=4)  # Smart help handler
        self.application.add_handler(CommandHandler("status", self.status_cmd), group=4)
        self.application.add_error_handler(self.error_handler)
        self.logger.info("Bot handlers configured")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        self.logger.error(f"Exception while handling an update: {context.error}")

    async def status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        bot_info = await context.bot.get_me()
        msg = f"""Bot Status: Online
Bot: {bot_info.first_name} (@{bot_info.username})
Company: {settings.company.NAME}
Support Email: {settings.email.SPICEWORKS_EMAIL}"""
        await update.message.reply_text(msg)

    def run(self):
        """Start the bot"""
        self.logger.info("Starting Telegram Help Desk Bot...")
        self.logger.info(f"Company: {settings.company.NAME}")
        self.logger.info(f"Support Email: {settings.email.SPICEWORKS_EMAIL}")

        # Initialize scheduler after application is fully built
        scheduler_manager = None
        task_manager = None
        
        try:
            from utils.scheduler import SchedulerManager, TaskManager

            scheduler_manager = SchedulerManager()

            # Start the cleanup scheduler (runs on 1st of each month at 00:00 UTC)
            if scheduler_manager.start_cleanup_scheduler(day=1, hour=0, minute=0):
                self.logger.info("Cleanup scheduler started successfully")
                scheduled_jobs = scheduler_manager.get_jobs()
                for job_id, job_name, job_trigger in scheduled_jobs:
                    self.logger.info(f"  Scheduled job: {job_name} ({job_id})")
            else:
                self.logger.warning("Failed to start cleanup scheduler")

            # Initialize TaskManager
            task_manager = TaskManager(scheduler_manager.scheduler)
            self.logger.info("Task Manager initialized")
            
            # Store task_manager in bot_data for schedule handler access
            self.application.bot_data['task_manager'] = task_manager

        except Exception as e:
            self.logger.warning(f"Could not initialize scheduler/task manager: {e}")
            scheduler_manager = None
            task_manager = None

        # Ensure event loop exists (Python 3.10+ compatibility)
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        # Start bot polling with message reactions enabled
        self.logger.info("Bot polling started - listening for messages, commands, and reactions")
        try:
            # explicitly allow message_reaction updates
            self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=[
                    'message',
                    'message_reaction',
                    'message_reaction_count',
                    'callback_query',
                    'my_chat_member',
                    'chat_member'
                ]
            )
        except KeyboardInterrupt:
            self.logger.info("Bot interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in bot polling: {e}", exc_info=True)
        finally:
            # Stop scheduler when bot stops
            if self.scheduler_manager:
                try:
                    self.scheduler_manager.stop_scheduler()
                    self.logger.info("Cleanup scheduler stopped")
                except Exception as e:
                    self.logger.warning(f"Error stopping scheduler: {e}")

def main():
    """Main entry point"""
    try:
        # Setup early logging for startup messages
        from utils.logger import setup_logging
        logger = setup_logging('INFO', './logs/bot.log')

        logger.info("Initializing Telegram Help Desk Bot...")
        if settings is None:
            logger.error("Configuration not loaded. Check your .env file.")
            sys.exit(1)

        bot = TelegramHelpDeskBot()
        bot.run()

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()