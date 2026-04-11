"""Queue management command handlers"""
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from utils.logger import get_logger
from services.queue_service import QueueService
from config.settings import settings

logger = get_logger(__name__)

class QueueAdminHandler:
    """Handle queue management commands"""

    @staticmethod
    async def queue_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show queue status"""
        try:
            stats = QueueService.get_queue_stats()

            status_msg = f"""📊 Queue Status:

📋 Total Requests: {stats['total']}
⏳ Queued: {stats['queued']}
⚙️ Processing: {stats['processing']}
✅ Completed: {stats['completed']}
❌ Failed: {stats['failed']}

Queue is operating normally."""

            await update.message.reply_text(status_msg)
            logger.info(f"Queue status requested by {update.effective_user.id}")

        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            await update.message.reply_text("Error retrieving queue status")

    @staticmethod
    async def my_queue_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check user's position in queue"""
        user_id = update.effective_user.id
        position = QueueService.get_queue_position(user_id)

        if position is None:
            msg = "✅ You're not in the queue. You don't have any pending requests."
        else:
            queue_size = QueueService.get_queue_size()
            estimated_wait = QueueService.get_estimated_wait_time(user_id)
            wait_minutes = estimated_wait.total_seconds() / 60 if estimated_wait else 0

            msg = f"""📍 Your Queue Status:

Position: #{position} of {queue_size}
Estimated Wait: ~{wait_minutes:.0f} minutes

Your request will be processed shortly."""

        await update.message.reply_text(msg)

    @staticmethod
    def get_queue_command_handlers():
        """Get all queue-related command handlers"""
        handlers = []

        if settings.app.QUEUE_ENABLED:
            # Queue status (for admins)
            handlers.append(
                CommandHandler("queue_status", QueueAdminHandler.queue_status,
                              filters=filters.User(user_id=settings.app.ADMIN_USER_IDS) if settings.app.ADMIN_USER_IDS else None)
            )

            # My position (for everyone)
            handlers.append(
                CommandHandler("my_position", QueueAdminHandler.my_queue_position)
            )

        return handlers
