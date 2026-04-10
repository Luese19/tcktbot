#!/usr/bin/env python3
"""Telegram Help Desk Bot - Main Entry Point"""

import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config.settings import settings
from utils.logger import setup_logging, get_logger
from handlers.conversation import get_conversation_handler

class TelegramHelpDeskBot:
    """Main bot application class"""

    def __init__(self):
        if settings is None:
            raise RuntimeError("Configuration not loaded")

        self.logger = setup_logging(settings.app.LOG_LEVEL, settings.app.LOG_FILE_PATH)
        self.application = Application.builder().token(settings.bot.TOKEN).build()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup bot handlers"""
        self.application.add_handler(get_conversation_handler())

        # Admin and lookup handlers
        from handlers.admin import get_lookup_handler, get_admin_handler, get_admin_command_handlers
        self.application.add_handler(get_lookup_handler())
        self.application.add_handler(get_admin_handler())
        for handler in get_admin_command_handlers():
            self.application.add_handler(handler)

        # Command handlers
        self.application.add_handler(CommandHandler("help", self.help_cmd))
        self.application.add_handler(CommandHandler("status", self.status_cmd))
        self.application.add_error_handler(self.error_handler)
        self.logger.info("Bot handlers configured")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        self.logger.error(f"Exception while handling an update: {context.error}")

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        msg = f"""📋 Help Desk Bot Commands:

🎫 Ticket Creation:
/start - Create a new support ticket
/cancel - Cancel current ticket

🔍 Ticket Lookup:
/lookup - Check your tickets by email

🔐 Admin Commands:
/admin - Login to admin panel
/list - View all tickets
/view {{ticket_id}} - View ticket details
/delete {{ticket_id}} - Delete ticket
/reply {{ticket_id}} {{message}} - Add reply to ticket
/replies {{ticket_id}} - View ticket replies

Other:
/help - Show this message
/status - Check bot status

✨ Features:
✓ Field validation (name, description)
✓ File uploads (JPG, PNG, PDF, DOCX)
✓ HTML formatted emails
✓ Auto-priority routing
✓ Ticket replies & notes

Company: {settings.company.NAME}
Support Email: {settings.email.SPICEWORKS_EMAIL}"""
        await update.message.reply_text(msg)

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
        self.application.run_polling(drop_pending_updates=True)

def main():
    """Main entry point"""
    try:
        print("Initializing Telegram Help Desk Bot...")
        if settings is None:
            print("ERROR: Configuration not loaded. Check your .env file.")
            sys.exit(1)

        bot = TelegramHelpDeskBot()
        bot.run()

    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()