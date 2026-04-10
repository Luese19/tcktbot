"""Service for managing Telegram username to user ID mappings"""
import json
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class UsernameService:
    """Service for storing and retrieving username to user_id mappings"""

    # Store mappings relative to bot directory
    USERNAMES_FILE = Path(__file__).parent.parent / "data" / "usernames" / "mapping.json"

    @classmethod
    def _ensure_file_exists(cls):
        """Ensure usernames directory and file exist"""
        cls.USERNAMES_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not cls.USERNAMES_FILE.exists():
            with open(cls.USERNAMES_FILE, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=2)

    @classmethod
    def store_username(cls, username: str, user_id: int, email: str = None) -> bool:
        """
        Store or update a username mapping

        Args:
            username: Telegram username (without @)
            user_id: Telegram user ID
            email: Optional email address

        Returns:
            True if successful
        """
        try:
            cls._ensure_file_exists()

            with open(cls.USERNAMES_FILE, 'r', encoding='utf-8') as f:
                mapping = json.load(f)

            mapping[username.lower()] = {
                'user_id': user_id,
                'email': email
            }

            with open(cls.USERNAMES_FILE, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)

            logger.info(f"Stored username mapping: @{username} -> {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing username mapping: {e}")
            return False

    @classmethod
    def get_user_id_by_username(cls, username: str) -> int:
        """
        Get user ID for a username

        Args:
            username: Telegram username (without @)

        Returns:
            User ID if found, None otherwise
        """
        try:
            cls._ensure_file_exists()

            with open(cls.USERNAMES_FILE, 'r', encoding='utf-8') as f:
                mapping = json.load(f)

            username_lower = username.lower()
            if username_lower in mapping:
                return mapping[username_lower].get('user_id')

            return None

        except Exception as e:
            logger.error(f"Error retrieving username mapping for {username}: {e}")
            return None

    @classmethod
    def get_email_by_username(cls, username: str) -> str:
        """
        Get email for a username

        Args:
            username: Telegram username (without @)

        Returns:
            Email if found, None otherwise
        """
        try:
            cls._ensure_file_exists()

            with open(cls.USERNAMES_FILE, 'r', encoding='utf-8') as f:
                mapping = json.load(f)

            username_lower = username.lower()
            if username_lower in mapping:
                return mapping[username_lower].get('email')

            return None

        except Exception as e:
            logger.error(f"Error retrieving email for {username}: {e}")
            return None

    @classmethod
    def get_all_mappings(cls) -> dict:
        """Get all username mappings"""
        try:
            cls._ensure_file_exists()

            with open(cls.USERNAMES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error retrieving all mappings: {e}")
            return {}
