"""Configuration management for Telegram Help Desk Bot"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class BotConfig:
    """Telegram Bot configuration"""
    def __init__(self):
        self.TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        if not self.TOKEN or self.TOKEN == 'your_bot_token_from_botfather':
            raise ValueError("TELEGRAM_BOT_TOKEN not configured in .env")

class CompanyConfig:
    """Company configuration"""
    def __init__(self):
        self.EMAIL_DOMAIN = os.getenv('COMPANY_EMAIL_DOMAIN', 'company.com')
        self.NAME = os.getenv('COMPANY_NAME', 'Your Company')

class EmailConfig:
    """Email/SMTP configuration"""
    def __init__(self):
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.company.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'helpdesk@company.com')
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
        self.SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.SPICEWORKS_EMAIL = os.getenv('SPICEWORKS_EMAIL', 'helpdesk@company.com')

class AppConfig:
    """Application configuration"""
    def __init__(self):
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/bot.log')
        self.MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '4000'))
        self.CONVERSATION_TIMEOUT_MINUTES = int(os.getenv('CONVERSATION_TIMEOUT_MINUTES', '30'))
        # File upload limits
        self.MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '10'))  # 10 MB
        self.MAX_ATTACHMENTS_PER_TICKET = int(os.getenv('MAX_ATTACHMENTS_PER_TICKET', '5'))
        # Admin settings
        self.ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
        self.ADMIN_USER_IDS = [int(uid) for uid in os.getenv('ADMIN_USER_IDS', '').split(',') if uid.strip()]

        # Field validation
        self.MIN_NAME_LENGTH = int(os.getenv('MIN_NAME_LENGTH', '2'))
        self.MAX_NAME_LENGTH = int(os.getenv('MAX_NAME_LENGTH', '100'))
        self.MIN_ISSUE_LENGTH = int(os.getenv('MIN_ISSUE_LENGTH', '5'))
        self.MAX_ISSUE_LENGTH = int(os.getenv('MAX_ISSUE_LENGTH', '200'))
        self.MIN_DESCRIPTION_LENGTH = int(os.getenv('MIN_DESCRIPTION_LENGTH', '10'))
        self.MAX_DESCRIPTION_LENGTH = int(os.getenv('MAX_DESCRIPTION_LENGTH', '2000'))

        # Group mention queue settings
        self.QUEUE_ENABLED = os.getenv('QUEUE_ENABLED', 'true').lower() == 'true'
        self.QUEUE_TIMEOUT_MINUTES = int(os.getenv('QUEUE_TIMEOUT_MINUTES', '30'))
        self.REQUEST_TIMEOUT_MINUTES = int(os.getenv('REQUEST_TIMEOUT_MINUTES', '60'))
        self.CONCURRENT_TICKET_CREATION = int(os.getenv('CONCURRENT_TICKET_CREATION', '1'))

        # Reaction-based ticket creation settings
        self.REACTION_TICKET_ENABLED = os.getenv('REACTION_TICKET_ENABLED', 'false').lower() == 'true'
        it_team_str = os.getenv('IT_TEAM_USER_IDS', '')
        self.IT_TEAM_USER_IDS = [int(uid) for uid in it_team_str.split(',') if uid.strip()]
        reaction_str = os.getenv('TICKET_REACTION_TRIGGERS', '🎫,👍,✅')
        self.TICKET_REACTION_TRIGGERS = [r.strip() for r in reaction_str.split(',') if r.strip()]

        Path(self.LOG_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)

class Settings:
    """Main settings class"""
    def __init__(self):
        try:
            self.bot = BotConfig()
            self.company = CompanyConfig()
            self.email = EmailConfig()
            self.app = AppConfig()
        except ValueError as e:
            raise ValueError(f"Configuration error: {e}")

    def is_company_email(self, email: str) -> bool:
        """Check if email belongs to company domain"""
        return email.lower().endswith(f"@{self.company.EMAIL_DOMAIN.lower()}")

try:
    settings = Settings()
except ValueError as e:
    # Configuration errors are critical and logged at startup
    import sys
    sys.stderr.write(f"FATAL: Configuration Error: {e}\n")
    sys.stderr.flush()
    settings = None