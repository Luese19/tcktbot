#!/usr/bin/env python3
"""Telegram Help Desk Bot - Main Entry Point"""

import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

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
        # Group mention handler FIRST with group 0 (highest priority)
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