"""Private welcome handler for registered employees in DMs"""
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from utils.logger import get_logger
from services.employee_service import EmployeeService

logger = get_logger(__name__)


class PrivateWelcomeHandler:
    """Handle welcome messages for registered employees in private chats"""

    @staticmethod
    async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle private text messages to send welcome message to registered employees
        """
        try:
            if not update.message or not update.effective_chat:
                return

            message = update.message
            chat = update.effective_chat
            user = update.effective_user

            # Only process private chats
            if chat.type != "private":
                return

            user_id = user.id

            # Check if user is registered and hasn't been welcomed
            if not EmployeeService.is_registered(user_id):
                logger.info(f"Ignoring private message from non-registered user {user_id}")
                return

            if EmployeeService.is_welcomed(user_id):
                logger.info(f"Ignoring private message from already welcomed user {user_id}")
                return

            # Send welcome message
            welcome_msg = """Welcome to the Help Desk Bot!

You can use these commands:
- Create a new ticket: /start
- View your tickets: /my_tickets
- Check ticket status: /ticket_status
- Get help: /help
- Register/update email: /register_email"""

            await context.bot.send_message(
                chat_id=chat.id,
                text=welcome_msg
            )

            # Mark as welcomed immediately to prevent duplicates
            EmployeeService.mark_as_welcomed(user_id)
            logger.info(f"Welcome message sent to registered employee {user_id}")

        except Exception as e:
            logger.error(f"Error in private welcome handler: {e}", exc_info=True)

    @staticmethod
    def get_handler():
        """Get the private welcome handler"""
        return MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT,
            PrivateWelcomeHandler.handle_private_message
        )