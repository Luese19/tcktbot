"""Email registration handlers for employees"""
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler

from utils.logger import get_logger
from services.employee_service import EmployeeService
from services.username_service import UsernameService
from config.settings import settings

logger = get_logger(__name__)

class RegistrationState:
    """States for registration conversation"""
    WAITING_FOR_EMAIL = 1

class EmailRegistrationHandler:
    """Handle employee email registration"""

    @staticmethod
    async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start email registration process"""
        user_id = update.effective_user.id
        user_name = update.effective_user.full_name or "User"

        # Check if already registered
        existing_email = EmployeeService.get_employee_email(user_id)
        if existing_email:
            await update.message.reply_text(
                f"Already registered!\n\n"
                f"Email: {existing_email}\n\n"
                f"To update your email, use /register_email again."
            )
            return ConversationHandler.END

        # Ask for email
        await update.message.reply_text(
            f"Email Registration\n\n"
            f"Hello {user_name}!\n\n"
            f"Please enter your company email to register.\n"
            f"This email will receive ticket confirmations.\n\n"
            f"Example: your.name@{settings.company.EMAIL_DOMAIN}"
        )

        return RegistrationState.WAITING_FOR_EMAIL

    @staticmethod
    async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and validate email"""
        user_id = update.effective_user.id
        user_name = update.effective_user.full_name or "User"
        email = update.message.text.strip()

        # Basic email validation
        if "@" not in email or "." not in email:
            await update.message.reply_text(
                "Invalid email format. Please enter a valid email address.\n\n"
                "Example: your.name@gmail.com"
            )
            return RegistrationState.WAITING_FOR_EMAIL

        # Check if company email (optional validation)
        if not settings.is_company_email(email):
            await update.message.reply_text(
                f"This doesn't appear to be a company email.\n\n"
                f"Expected domain: @{settings.company.EMAIL_DOMAIN}\n"
                f"Your email: {email}\n\n"
                f"Do you want to continue? Reply with:\n"
                f"- yes to confirm\n"
                f"- no to try again"
            )
            context.user_data['pending_email'] = email
            return RegistrationState.WAITING_FOR_EMAIL

        # Register the email
        success = EmployeeService.register_email(user_id, email, user_name)

        if success:
            # Also store username mapping for bulk mention support
            if update.effective_user.username:
                UsernameService.store_username(
                    update.effective_user.username,
                    user_id,
                    email
                )

            await update.message.reply_text(
                f"Email Registered Successfully!\n\n"
                f"Name: {user_name}\n"
                f"Email: {email}\n\n"
                f"Now when you mention the bot in groups with issues like:\n"
                f"admin office no internet @mevithelpdesk\n\n"
                f"A ticket will be created\n"
                f"Confirmation email will be sent to: {email}"
            )
            logger.info(f"User {user_id} registered email: {email}")
        else:
            await update.message.reply_text(
                "Error registering email. Please try again."
            )

        return ConversationHandler.END

    @staticmethod
    async def check_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check current registration status"""
        user_id = update.effective_user.id

        employee = EmployeeService.get_employee_info(user_id)

        if employee:
            registered_date = employee.get('registered_at', 'Unknown')
            registered_date = registered_date.split('T')[0] if registered_date != 'Unknown' else registered_date

            await update.message.reply_text(
                f"Your Registration\n\n"
                f"Name: {employee.get('name', 'Unknown')}\n"
                f"Email: {employee.get('email')}\n"
                f"Registered: {registered_date}\n\n"
                f"You will receive ticket confirmations at this email."
            )
        else:
            await update.message.reply_text(
                f"You are not registered yet.\n\n"
                f"Use /register_email to register your company email."
            )

    @staticmethod
    async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel registration process"""
        await update.message.reply_text("❌ Registration cancelled.")
        return ConversationHandler.END

    @staticmethod
    def get_registration_handler():
        """Create and return registration conversation handler"""
        return ConversationHandler(
            entry_points=[CommandHandler("register_email", EmailRegistrationHandler.start_registration)],
            states={
                RegistrationState.WAITING_FOR_EMAIL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, EmailRegistrationHandler.receive_email),
                ]
            },
            fallbacks=[CommandHandler("cancel", EmailRegistrationHandler.cancel_registration)],
            per_message=False
        )

    @staticmethod
    def get_check_handler():
        """Create and return status check handler"""
        return CommandHandler("my_email", EmailRegistrationHandler.check_registration)
