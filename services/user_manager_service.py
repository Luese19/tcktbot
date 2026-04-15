"""User management service for admins and IT team members"""
import json
from pathlib import Path
from typing import List, Optional, Set
from utils.logger import get_logger

logger = get_logger(__name__)


class UserManagerService:
    """Service for managing admin users and IT team members"""

    DATA_DIR = Path(__file__).parent.parent / "data" / "admins"
    ADMIN_USERS_FILE = DATA_DIR / "admin_users.json"
    IT_TEAM_USERS_FILE = DATA_DIR / "it_team_users.json"

    # Cache for performance - holds the current lists
    _admin_users_cache: Optional[Set[int]] = None
    _it_team_users_cache: Optional[Set[int]] = None

    @classmethod
    def _ensure_dir(cls):
        """Ensure admin data directory exists"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _load_json_list(cls, file_path: Path) -> Set[int]:
        """Load user list from JSON file"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(int(uid) for uid in data.get('users', []))
        except Exception as e:
            logger.error(f"Error loading user list from {file_path}: {e}")
        return set()

    @classmethod
    def _save_json_list(cls, file_path: Path, users: Set[int]):
        """Save user list to JSON file"""
        cls._ensure_dir()
        try:
            data = {'users': sorted(list(users))}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving user list to {file_path}: {e}")

    @classmethod
    def get_admin_users(cls, super_admin_ids: List[int]) -> Set[int]:
        """Get all admin user IDs (super admins + dynamic admins)"""
        if cls._admin_users_cache is None:
            cls._admin_users_cache = cls._load_json_list(cls.ADMIN_USERS_FILE)
        
        # Always include super admins from .env
        return cls._admin_users_cache | set(super_admin_ids)

    @classmethod
    def get_it_team_users(cls) -> Set[int]:
        """Get all IT team user IDs"""
        if cls._it_team_users_cache is None:
            cls._it_team_users_cache = cls._load_json_list(cls.IT_TEAM_USERS_FILE)
        return cls._it_team_users_cache

    @classmethod
    def add_admin_user(cls, user_id: int) -> bool:
        """Add a user to the admin list"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id for admin: {user_id}")
            return False

        # Reload cache if not initialized
        if cls._admin_users_cache is None:
            cls._admin_users_cache = cls._load_json_list(cls.ADMIN_USERS_FILE)

        if user_id in cls._admin_users_cache:
            logger.info(f"User {user_id} is already an admin")
            return False

        cls._admin_users_cache.add(user_id)
        cls._save_json_list(cls.ADMIN_USERS_FILE, cls._admin_users_cache)
        logger.info(f"Added user {user_id} to admin list")
        return True

    @classmethod
    def remove_admin_user(cls, user_id: int) -> bool:
        """Remove a user from the admin list"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id for removal: {user_id}")
            return False

        # Reload cache if not initialized
        if cls._admin_users_cache is None:
            cls._admin_users_cache = cls._load_json_list(cls.ADMIN_USERS_FILE)

        if user_id not in cls._admin_users_cache:
            logger.info(f"User {user_id} is not in admin list")
            return False

        cls._admin_users_cache.discard(user_id)
        cls._save_json_list(cls.ADMIN_USERS_FILE, cls._admin_users_cache)
        logger.info(f"Removed user {user_id} from admin list")
        return True

    @classmethod
    def add_it_user(cls, user_id: int) -> bool:
        """Add a user to the IT team list"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id for IT team: {user_id}")
            return False

        # Reload cache if not initialized
        if cls._it_team_users_cache is None:
            cls._it_team_users_cache = cls._load_json_list(cls.IT_TEAM_USERS_FILE)

        if user_id in cls._it_team_users_cache:
            logger.info(f"User {user_id} is already in IT team")
            return False

        cls._it_team_users_cache.add(user_id)
        cls._save_json_list(cls.IT_TEAM_USERS_FILE, cls._it_team_users_cache)
        logger.info(f"Added user {user_id} to IT team")
        return True

    @classmethod
    def remove_it_user(cls, user_id: int) -> bool:
        """Remove a user from the IT team list"""
        if not isinstance(user_id, int) or user_id <= 0:
            logger.warning(f"Invalid user_id for removal: {user_id}")
            return False

        # Reload cache if not initialized
        if cls._it_team_users_cache is None:
            cls._it_team_users_cache = cls._load_json_list(cls.IT_TEAM_USERS_FILE)

        if user_id not in cls._it_team_users_cache:
            logger.info(f"User {user_id} is not in IT team")
            return False

        cls._it_team_users_cache.discard(user_id)
        cls._save_json_list(cls.IT_TEAM_USERS_FILE, cls._it_team_users_cache)
        logger.info(f"Removed user {user_id} from IT team")
        return True

    @classmethod
    def reload_caches(cls):
        """Force reload of all caches (useful after external changes)"""
        cls._admin_users_cache = None
        cls._it_team_users_cache = None
        logger.info("User manager caches reloaded")

    @classmethod
    def initialize(cls):
        """Initialize service and load caches"""
        cls._ensure_dir()
        cls._admin_users_cache = cls._load_json_list(cls.ADMIN_USERS_FILE)
        cls._it_team_users_cache = cls._load_json_list(cls.IT_TEAM_USERS_FILE)
        logger.info(f"User manager initialized: {len(cls._admin_users_cache)} admins, {len(cls._it_team_users_cache)} IT members")
